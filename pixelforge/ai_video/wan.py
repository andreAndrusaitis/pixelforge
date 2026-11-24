"""Imagem → vídeo com Wan 2.2 TI2V-5B (Apache-2.0), local, em 8 GB de VRAM e 16 GB de RAM.

Escolha (out/2026): o TI2V-5B é o maior modelo de imagem→vídeo aberto, sem login nem
licença a aceitar, que cabe numa RTX 4060 de 8 GB. O LTX-2 (19B) exige GGUF agressivo e
resolução mínima; o Wan 14B não cabe. Para caber também em 16 GB de RAM:

- transformer em GGUF Q8_0 (QuantStack, 5,4 GB; quase sem perda) em vez de 20 GB fp32;
- codificador de texto UMT5-XXL em 4 bits NF4 com cálculo em bf16 (bitsandbytes; o 8 bits
  passa por fp16, que estoura no T5, e usa 7,9 GB), uma vez por descrição e descarregado —
  os embeddings ficam em cache em disco (~50 s na 1ª vez, 0,04 s depois);
- VAE do Wan 2.2 em float32 (recomendado), com `enable_model_cpu_offload`.

Pesos em `<modelos>/video/` (padrão `~/.cache/pixelforge/models/video`, fora do
repositório e do OneDrive; `PIXELFORGE_MODELS` muda a raiz). Baixar: `video-ia baixar`.
"""

from __future__ import annotations

import gc
import hashlib
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from ..audio.ai.common import BackendError, available, models_dir, require, use_hf_cache

REPO = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
GGUF_REPO = "QuantStack/Wan2.2-TI2V-5B-GGUF"
GGUF_FILE = "Wan2.2-TI2V-5B-Q8_0.gguf"
BASE_FILES = ["model_index.json", "scheduler/*", "tokenizer/*", "text_encoder/*", "vae/*", "transformer/config.json"]
FPS = 24                    # o TI2V-5B gera a 24 fps
STEPS = 24
GUIDANCE = 5.0
NEGATIVE = ("blurry, low quality, jpeg artifacts, distorted, deformed, extra limbs, morphing, flicker, "
            "text, watermark, camera shake, zoom, scene change, cut")
MIN_FREE_GB = 5.0           # VRAM livre exigida antes de gerar (outro job na GPU = swap e lentidão)
INSTALL_HINT = "pip install -e .[video-ia]  (e PyTorch com CUDA; veja o docs/manual.md, seção Vídeo por IA)"


def video_dir(models: Path | str | None = None) -> Path:
    return models_dir(models) / "models" / "video"


def base_dir(models: Path | str | None = None) -> Path:
    return video_dir(models) / REPO.replace("/", "--")


def gguf_path(models: Path | str | None = None) -> Path:
    return video_dir(models) / GGUF_REPO.replace("/", "--") / GGUF_FILE


def installed(models: Path | str | None = None) -> bool:
    root = base_dir(models)
    return (gguf_path(models).is_file() and (root / "model_index.json").is_file()
            and any((root / "text_encoder").glob("*.safetensors")) and any((root / "vae").glob("*.safetensors")))


def dependencies_ok() -> bool:
    return all(available(m) for m in ("torch", "diffusers", "transformers", "gguf", "accelerate"))


def download(models: Path | str | None = None) -> list[Path]:
    """Baixa só o necessário (~19,6 GB): UMT5 bf16, VAE, configs e o transformer GGUF Q8."""
    use_hf_cache(models_dir(models))
    # o cliente Xet travou em arquivos de 5 GB nesta máquina; HTTP comum retoma sem travar
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    hub = require("huggingface_hub", "download do Wan 2.2")
    for repo in (REPO, GGUF_REPO):
        info = hub.model_info(repo)
        if getattr(info, "gated", False):
            raise BackendError(f"{repo} exige aceitar licença/login no Hugging Face; não aceito por você — "
                               "faça manualmente se quiser")
    paths = [Path(hub.snapshot_download(REPO, allow_patterns=BASE_FILES, local_dir=base_dir(models)))]
    paths.append(Path(hub.hf_hub_download(GGUF_REPO, GGUF_FILE, local_dir=gguf_path(models).parent)))
    return paths


@dataclass
class Timing:
    """Tempos (s) de uma geração, para mostrar ao autor."""

    text: float = 0.0
    load: float = 0.0
    sample: float = 0.0
    decode: float = 0.0
    extra: dict = field(default_factory=dict)

    @property
    def total(self) -> float:
        return self.text + self.load + self.sample + self.decode

    def describe(self) -> str:
        return (f"texto {self.text:.0f} s, carga {self.load:.0f} s, amostragem {self.sample:.0f} s, "
                f"VAE {self.decode:.0f} s — total {self.total:.0f} s")


def frame_count(seconds: float) -> int:
    """Quadros a 24 fps no formato 4k+1 que o Wan exige."""
    n = max(5, int(round(seconds * FPS)))
    return (n - 1) // 4 * 4 + 1


def video_size(aspect: float, long_side: int = 832) -> tuple[int, int]:
    """(largura, altura) múltiplos de 32 na proporção pedida, com a área de `long_side`×(long_side·9/16)
    (≈ 832x480): imagens largas (rua 1280x360) ganham largura em vez de perder altura."""
    area = long_side * long_side * 9 / 16
    w, h = (area * aspect) ** 0.5, (area / aspect) ** 0.5
    return max(256, int(round(w / 32)) * 32), max(256, int(round(h / 32)) * 32)


def check_gpu(torch, need_gb: float = MIN_FREE_GB) -> None:
    """Recusa gerar com a GPU ocupada por outro processo (ex.: treino de LoRA): os dois
    trocariam memória com a RAM e se arrastariam. `PIXELFORGE_GPU_LIVRE=0` desliga a checagem."""
    if os.environ.get("PIXELFORGE_GPU_LIVRE") == "0" or not torch.cuda.is_available():
        return
    free, total = torch.cuda.mem_get_info()
    if free / 1e9 < need_gb:
        raise BackendError(f"GPU ocupada: {free / 1e9:.1f} de {total / 1e9:.1f} GB livres (o Wan precisa de "
                           f"~{need_gb:g} GB). Espere o outro job terminar ou use --sem-ia.")


class WanI2V:
    """Gera clipes; mantém o transformer carregado entre chamadas da mesma execução."""

    def __init__(self, models: Path | str | None = None, steps: int = STEPS, guidance: float = GUIDANCE,
                 cache_dir: Path | None = None):
        if not dependencies_ok():
            raise BackendError(f"vídeo por IA precisa de torch, diffusers, transformers, gguf e accelerate. "
                               f"Instale: {INSTALL_HINT}")
        if not installed(models):
            raise BackendError("pesos do Wan 2.2 TI2V-5B não encontrados em "
                               f"{video_dir(models)}; baixe com: python -m pixelforge video-ia baixar")
        self.models = models
        self.steps = steps
        self.guidance = guidance
        self.cache_dir = cache_dir
        self._pipe = None

    # ------------------------------------------------------------------ texto

    def _embeds(self, prompt: str, timing: Timing):
        """Embeddings do UMT5 (positivo e negativo), em cache por hash da descrição."""
        torch = require("torch", "vídeo por IA")
        key = hashlib.sha1(f"{REPO}|nf4|{prompt}|{NEGATIVE}".encode("utf-8")).hexdigest()[:16]
        cache = (self.cache_dir or video_dir(self.models) / "embeds") / f"umt5_{key}.pt"
        if cache.is_file():
            data = torch.load(cache, map_location="cpu")
            return data["pos"], data["neg"]
        t0 = time.time()
        transformers = require("transformers", "vídeo por IA")
        root = base_dir(self.models)
        tokenizer = transformers.AutoTokenizer.from_pretrained(root / "tokenizer")
        quant = (transformers.BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                 bnb_4bit_compute_dtype=torch.bfloat16)
                 if available("bitsandbytes") else None)
        encoder = transformers.UMT5EncoderModel.from_pretrained(
            root / "text_encoder", torch_dtype=torch.bfloat16, quantization_config=quant,
            device_map="cuda" if quant else None, low_cpu_mem_usage=True)
        if quant is None:
            encoder = encoder.to("cuda")
        out = []
        for text in (prompt, NEGATIVE):
            ids = tokenizer([text], padding="max_length", max_length=512, truncation=True,
                            add_special_tokens=True, return_attention_mask=True, return_tensors="pt")
            mask = ids.attention_mask.to("cuda")
            with torch.no_grad():
                hidden = encoder(ids.input_ids.to("cuda"), mask).last_hidden_state
            length = int(mask.sum())
            emb = torch.zeros_like(hidden)
            emb[:, :length] = hidden[:, :length]       # como o pipeline do Wan: zera depois do texto
            out.append(emb.to("cpu", torch.bfloat16))
        del encoder
        gc.collect()
        torch.cuda.empty_cache()
        cache.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"pos": out[0], "neg": out[1]}, cache)
        timing.text = time.time() - t0
        return out[0], out[1]

    # ------------------------------------------------------------------ vídeo

    def _pipeline(self, timing: Timing):
        if self._pipe is not None:
            return self._pipe
        t0 = time.time()
        torch = require("torch", "vídeo por IA")
        diffusers = require("diffusers", "vídeo por IA")
        root = base_dir(self.models)
        transformer = diffusers.WanTransformer3DModel.from_single_file(
            str(gguf_path(self.models)), config=str(root), subfolder="transformer",
            quantization_config=diffusers.GGUFQuantizationConfig(compute_dtype=torch.bfloat16),
            torch_dtype=torch.bfloat16)
        vae = diffusers.AutoencoderKLWan.from_pretrained(root, subfolder="vae", torch_dtype=torch.float32)
        pipe = diffusers.WanImageToVideoPipeline.from_pretrained(
            root, transformer=transformer, vae=vae, text_encoder=None, tokenizer=None,
            image_encoder=None, image_processor=None, torch_dtype=torch.bfloat16)
        pipe.enable_model_cpu_offload()
        pipe.set_progress_bar_config(disable=True)
        self._pipe = pipe
        timing.load = time.time() - t0
        return pipe

    def generate(self, image: Image.Image, prompt: str, seconds: float = 2.0, seed: int = 0,
                 long_side: int = 832) -> tuple[list[np.ndarray], Timing]:
        """Imagem (RGB) + descrição do movimento → quadros RGB a 24 fps."""
        torch = require("torch", "vídeo por IA")
        check_gpu(torch)
        timing = Timing()
        pos, neg = self._embeds(prompt, timing)
        pipe = self._pipeline(timing)
        width, height = video_size(image.width / image.height, long_side)
        frames = frame_count(seconds)
        start = image.convert("RGB").resize((width, height), Image.LANCZOS)
        t0 = time.time()
        marks = {}

        def on_step(pipe_, i, t, kwargs):
            if i == self.steps - 1:
                marks["sampled"] = time.time()
            return kwargs

        out = pipe(image=start, prompt_embeds=pos.to("cuda"), negative_prompt_embeds=neg.to("cuda"),
                   height=height, width=width, num_frames=frames, num_inference_steps=self.steps,
                   guidance_scale=self.guidance, generator=torch.Generator("cpu").manual_seed(seed),
                   output_type="np", callback_on_step_end=on_step).frames[0]
        done = time.time()
        timing.sample = marks.get("sampled", done) - t0
        timing.decode = done - marks.get("sampled", done)
        timing.extra = {"tamanho": f"{width}x{height}", "quadros": frames, "passos": self.steps, "semente": seed}
        video = [(np.clip(f, 0, 1) * 255).round().astype(np.uint8) for f in out]
        return video, timing

    def close(self) -> None:
        self._pipe = None
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except ImportError:
            pass
