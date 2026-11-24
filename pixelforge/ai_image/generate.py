"""Geração do rascunho: SDXL (fp16, offload) + LoRA de pixel art, via diffusers.

Modos (combináveis):
  texto → imagem      só o prompt
  imagem → imagem     `init` (esboço por código, quadro de cena ou foto) + `strength`
  referência          `ref` (IP-Adapter): mesmo rosto/roupa entre gerações

Cabe em 8 GB de VRAM: pesos fp16 e `enable_model_cpu_offload` (só o módulo em
uso fica na GPU). Semente, prompt, negativo e parâmetros voltam em `Result`
para gravar ao lado da saída e reproduzir depois.
"""

from __future__ import annotations

import importlib
import math
import os
import random
import time
import warnings
from dataclasses import asdict, dataclass, field
from pathlib import Path

from PIL import Image, ImageOps

from . import AIImageError, INSTALL_HINT
from . import models as catalog


@dataclass
class Request:
    prompt: str
    negative: str = ""
    width: int = 1024
    height: int = 1024
    seed: int = -1  # -1 = sorteia (e grava a sorteada)
    steps: int = 0  # 0 = padrão do modelo
    guidance: float = 0.0  # 0 = padrão do modelo
    model: str = "dreamshaper-xl-lightning"
    lora: str = "pixel-art-xl"  # "" desliga
    lora_weight: float = 1.0
    init: str = ""  # imagem → imagem
    strength: float = 0.55
    ref: str = ""  # referência de personagem (IP-Adapter)
    ref_weight: float = 0.55
    ref_kind: str = "plus"  # plus | face
    style_refs: list[str] = field(default_factory=list)  # imagens de estilo (IP-Adapter só nas camadas de estilo)
    style_weight: float = 0.6
    style_lora: str = ""  # LoRA de estilo treinado (`ia treinar`): arquivo .safetensors; "" desliga
    style_lora_weight: float = 0.8
    offload: str = "modelo"  # modelo | sequencial | nenhum
    precision: str = "fp8"  # fp8 (UNet em 2,6 GB) | fp16

    def adapters(self) -> tuple[str, ...]:
        """IP-Adapters que o pedido usa, na ordem: personagem, estilo."""
        return tuple(k for k, on in ((self.ref_kind, bool(self.ref)), ("plus", bool(self.style_refs))) if on)

    def engine_key(self) -> tuple:
        return (self.model, self.lora, self.lora_weight, self.style_lora, self.style_lora_weight,
                bool(self.init), self.adapters(), self.precision, self.offload)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Request":
        known = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Result:
    image: Image.Image
    request: Request
    seconds: float  # só a geração (sem carregar o modelo)
    load_seconds: float
    info: dict = field(default_factory=dict)


def _require(module: str):
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        raise AIImageError(f"IA de imagem precisa do pacote '{module}' ({exc.name} não encontrado). "
                           f"Instale: {INSTALL_HINT}") from None


def _quiet() -> None:
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")  # tudo vem de models/; nada de rede na geração
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("DIFFUSERS_VERBOSITY", "error")
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    for category in (UserWarning, FutureWarning, DeprecationWarning):
        warnings.filterwarnings("ignore", category=category)


def fit_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Recorta/escala para preencher `size` (imagem → imagem precisa do tamanho exato)."""
    image = ImageOps.exif_transpose(image)
    if image.mode == "RGBA":  # transparente vira cinza neutro (fundo liso para a IA)
        flat = Image.new("RGB", image.size, (128, 128, 128))
        flat.paste(image, mask=image.getchannel("A"))
        image = flat
    return ImageOps.fit(image.convert("RGB"), size, Image.Resampling.LANCZOS)


def make_scheduler(diffusers, config):
    """DPM++ SDE Karras (o recomendado para modelos Lightning); sem torchsde, Euler."""
    try:
        import torchsde  # noqa: F401
        return diffusers.DPMSolverSDEScheduler.from_config(config, use_karras_sigmas=True)
    except ImportError:
        return diffusers.EulerDiscreteScheduler.from_config(config, timestep_spacing="trailing")


def split_prompt(tokenizer, text: str) -> list[str]:
    """Divide o prompt em pedaços de até 75 tokens, sem cortar termos (separa nas vírgulas)."""
    limit = tokenizer.model_max_length - 2
    out, current = [], []
    for term in [t.strip() for t in (text or "").split(",") if t.strip()]:
        trial = ", ".join([*current, term])
        if current and len(tokenizer(trial).input_ids) - 2 > limit:
            out.append(", ".join(current))
            current = [term]
        else:
            current.append(term)
    if current:
        out.append(", ".join(current))
    return out or [""]


# InstantStyle: no SDXL o estilo mora em up_blocks.0.attentions.1; injetar a imagem só ali
# passa cor, luz e textura sem copiar o conteúdo da referência
def style_only(weight: float) -> dict:
    return {"up": {"block_0": [0.0, weight, 0.0]}}


ADAPTER_FILES = {"plus": "ip-adapter-plus_sdxl_vit-h.safetensors",
                 "face": "ip-adapter-plus-face_sdxl_vit-h.safetensors"}


class Engine:
    """Carrega o pipeline uma vez e gera várias imagens com a mesma configuração."""

    def __init__(self, base: Path, model: str, lora: str = "", lora_weight: float = 1.0,
                 style_lora: str = "", style_lora_weight: float = 0.8, img2img: bool = False,
                 adapters: tuple[str, ...] = (), precision: str = "fp8", offload: str = "modelo"):
        _quiet()
        self.torch = _require("torch")
        diffusers = _require("diffusers")
        if not self.torch.cuda.is_available():
            raise AIImageError("nenhuma GPU CUDA disponível (o PyTorch instalado é só CPU?). "
                               "Instale o PyTorch com CUDA: veja o docs/manual.md, seção IA de imagem.")
        if precision not in ("fp8", "fp16"):
            raise AIImageError(f"precisao deve ser fp8 ou fp16, recebido {precision!r}")
        started = time.perf_counter()
        torch = self.torch
        dtype = torch.float16
        cls = diffusers.StableDiffusionXLImg2ImgPipeline if img2img else diffusers.StableDiffusionXLPipeline
        pipe = load_base(diffusers, cls, base, model, dtype)
        fuse_loras(pipe, base, lora, lora_weight, style_lora, style_lora_weight)
        if adapters:
            pipe.load_ip_adapter(str(catalog.require_local("ip-adapter", base)),
                                 subfolder=["sdxl_models"] * len(adapters),
                                 weight_name=[ADAPTER_FILES[k] for k in adapters],
                                 image_encoder_folder="models/image_encoder")
        if precision == "fp8":
            # pesos da UNet guardados em fp8 e calculados em fp16: 5,1 → 2,6 GB na GPU
            pipe.unet.enable_layerwise_casting(storage_dtype=torch.float8_e4m3fn, compute_dtype=dtype)
        if offload == "sequencial":
            pipe.enable_sequential_cpu_offload()
        elif offload == "nenhum":
            pipe.to("cuda")
        else:
            pipe.enable_model_cpu_offload()
        pipe.vae.enable_tiling()
        pipe.set_progress_bar_config(disable=True)
        self.pipe = pipe
        self.key = (model, lora, lora_weight, style_lora, style_lora_weight, img2img, tuple(adapters),
                    precision, offload)
        self.load_seconds = time.perf_counter() - started

    @classmethod
    def for_request(cls, request: Request, base: Path) -> "Engine":
        return cls(base, request.model, request.lora, request.lora_weight, request.style_lora,
                   request.style_lora_weight, bool(request.init), request.adapters(), request.precision,
                   request.offload)

    def accepts(self, request: Request) -> bool:
        """O pipeline carregado serve para este pedido (mesmo modelo, LoRAs, modo, adapters)?"""
        return request.engine_key() == self.key

    def chunks(self, text: str) -> list[str]:
        return split_prompt(self.pipe.tokenizer, text)

    def long_prompt(self, prompt: str, negative: str) -> dict | None:
        """Embeddings de prompts acima de 77 tokens: cada pedaço codificado à parte e concatenado
        (o CLIP sozinho ignora o que passa de 77). None quando cabe tudo num pedaço só."""
        pos, neg = self.chunks(prompt), self.chunks(negative)
        if len(pos) == 1 and len(neg) == 1:
            return None
        n = max(len(pos), len(neg))
        pos, neg = pos + [""] * (n - len(pos)), neg + [""] * (n - len(neg))
        embeds, negs, pooled, neg_pooled = [], [], None, None
        device = self.pipe._execution_device
        for i, (a, b) in enumerate(zip(pos, neg)):
            e, ne, pe, npe = self.pipe.encode_prompt(a, device=device, do_classifier_free_guidance=True,
                                                     negative_prompt=b)
            embeds.append(e)
            negs.append(ne)
            if i == 0:
                pooled, neg_pooled = pe, npe
        torch = self.torch
        return {"prompt_embeds": torch.cat(embeds, dim=1), "negative_prompt_embeds": torch.cat(negs, dim=1),
                "pooled_prompt_embeds": pooled, "negative_pooled_prompt_embeds": neg_pooled}

    def run(self, request: Request) -> Result:
        torch = self.torch
        defaults = catalog.get(request.model).defaults
        steps = request.steps or defaults.get("passos", 25)
        guidance = request.guidance or defaults.get("guia", 5.0)
        seed = request.seed if request.seed >= 0 else random.randrange(2 ** 31)
        kwargs = dict(prompt=request.prompt, negative_prompt=request.negative or None,
                      guidance_scale=guidance, generator=torch.Generator("cpu").manual_seed(seed))
        if request.init:
            with Image.open(request.init) as opened:
                kwargs["image"] = fit_cover(opened, (request.width, request.height))
            kwargs["strength"] = request.strength
            # o img2img roda só a fração `strength` dos passos: compensa para manter a qualidade
            kwargs["num_inference_steps"] = min(50, math.ceil(steps / max(request.strength, 0.05)))
        else:
            kwargs.update(width=request.width, height=request.height, num_inference_steps=steps)
        images, scales = [], []
        if request.ref:
            with Image.open(request.ref) as opened:
                images.append(ImageOps.exif_transpose(opened).convert("RGB"))
            scales.append(request.ref_weight)
        if request.style_refs:
            styles = []
            for path in request.style_refs:
                with Image.open(path) as opened:
                    styles.append(opened.convert("RGB"))
            images.append(styles)
            scales.append(style_only(request.style_weight))
        if images:
            kwargs["ip_adapter_image"] = images
            self.pipe.set_ip_adapter_scale(scales)

        embeds = self.long_prompt(request.prompt, request.negative)
        if embeds:  # prompt longo: vai em pedaços (nada é cortado)
            kwargs.pop("prompt")
            kwargs.pop("negative_prompt")
            kwargs.update(embeds)

        torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        try:
            image = self.pipe(**kwargs).images[0]
        except (torch.OutOfMemoryError, torch.AcceleratorError) as exc:
            if "out of memory" not in str(exc):
                raise
            torch.cuda.empty_cache()
            raise AIImageError(
                "a GPU ficou sem memória. Feche programas que usam a GPU (jogos, navegador com "
                "aceleração, papel de parede animado) ou use `offload = \"sequencial\"` em [ia] "
                "(mais lento) ou uma resolução menor (--resolucao).") from None
        seconds = time.perf_counter() - started
        torch.cuda.empty_cache()  # devolve a memória entre gerações (a VRAM é dividida com outros apps)
        resolved = Request(**{**request.to_dict(), "seed": seed, "steps": steps, "guidance": guidance})
        info = {
            "gpu": torch.cuda.get_device_name(0),
            "vram_pico_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2),
            "torch": torch.__version__,
            "diffusers": importlib.import_module("diffusers").__version__,
            "repositorios": {k: catalog.get(k).repo for k in (request.model, "vae-fp16", request.lora,
                                                              "ip-adapter" if request.adapters() else "")
                             if k},
        }
        return Result(image, resolved, seconds, self.load_seconds, info)


def load_base(diffusers, cls, base: Path, model: str, dtype):
    """Pipeline SDXL do catálogo, com o VAE fp16-fix e o amostrador dos modelos Lightning."""
    vae = diffusers.AutoencoderKL.from_pretrained(catalog.require_local("vae-fp16", base), torch_dtype=dtype)
    pipe = cls.from_pretrained(catalog.require_local(model, base), vae=vae, torch_dtype=dtype, variant="fp16",
                               use_safetensors=True)
    pipe.scheduler = make_scheduler(diffusers, pipe.scheduler.config)
    return pipe


def fuse_loras(pipe, base: Path, lora: str, lora_weight: float, style_lora: str = "",
               style_lora_weight: float = 0.8) -> None:
    """Funde os LoRAs nos pesos: sem camadas extras do PEFT na memória nem no tempo."""
    names, weights = [], []
    if lora:
        pipe.load_lora_weights(str(catalog.require_local(lora, base)), weight_name=catalog.get(lora).file,
                               adapter_name="pixel")
        names.append("pixel")
        weights.append(lora_weight)
    if style_lora:
        path = Path(style_lora)
        if not path.is_file():
            raise AIImageError(f"LoRA de estilo não encontrado: {path} (treine com `ia treinar`)")
        pipe.load_lora_weights(str(path.parent), weight_name=path.name, adapter_name="estilo")
        names.append("estilo")
        weights.append(style_lora_weight)
    if names:
        pipe.set_adapters(names, adapter_weights=weights)
        pipe.fuse_lora(adapter_names=names, lora_scale=1.0)
        pipe.unload_lora_weights()


def generate(request: Request, base: Path) -> Result:
    return Engine.for_request(request, base).run(request)
