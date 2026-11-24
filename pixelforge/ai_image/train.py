"""`ia treinar`: LoRA de estilo local treinado nas referências do autor (uso pessoal).

Dataset (montado sem GPU):
  refs/estilo-referencias/ → resolução nativa (`pixelforge.style` desfaz a grade) →
  reampliada por vizinho em múltiplo inteiro (até ×8, o pseudo-pixel de 8 px da
  geração) → recorte central em múltiplos de 64. Legenda = gatilho + tipo + tags
  do índice (em inglês) + números da decomposição (paleta, contorno, rim, blocos).
  As refs com ruído de IA (§7 do estilo: 17, 24, 25, 31) ficam de fora, ou entram
  com metade das repetições (`--com-ruidosas`).

Treino (cabe em 8 GB):
  UNet do modelo-base com o LoRA de pixel fundido (o mesmo da geração), pesos
  congelados em fp8 calculados em bf16 (`store_frozen_fp8`), gradient checkpointing, AdamW 8-bit (bitsandbytes),
  latentes e textos cacheados antes (VAE e codificadores de texto saem da GPU),
  LoRA rank 16 nas projeções de atenção, perda MSE com min-SNR (γ = 5).
Os pesos e o dataset ficam em models/ (fora do git) e nunca são publicados.
"""

from __future__ import annotations

import json
import math
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image

from ..config import Config
from . import AIImageError
from . import models as catalog
from . import presets, style

TIPO_EN = {"personagem": "character", "retrato": "bust portrait", "cenario": "landscape", "cena": "scene",
           "criatura": "creature"}

# tags do índice (pt) → termos que o CLIP conhece; as que não estão aqui ficam de fora
TAG_EN = {
    "armadura": "armor", "asas": "wings", "baixa-resolucao": "low resolution", "blocos-grandes": "large pixel blocks",
    "brilho": "glow", "brilhos": "sparkles", "busto": "bust", "busto-e-corpo": "bust and full body",
    "cabelo-cacheado": "curly hair", "cabelo-em-mechas": "hair in tufts", "cabelo-longo": "long hair",
    "cajado": "staff", "calca-larga": "baggy pants", "capa": "cape", "capa-em-blocos": "blocky cape",
    "capa-rasgada": "torn cape", "capuz": "hood", "casaco": "coat", "cavaleiro": "knight",
    "cavaleiro-a-cavalo": "rider on horse", "cavalo": "horse", "ceu-com-nuvens": "cloudy sky",
    "ceu-vermelho": "red sky", "chapeu": "hat", "chibi": "chibi", "chibi-atarracado": "chibi", "chifres": "horns",
    "cinto": "belt", "contorno-claro": "light outline", "contorno-colorido": "colored outline",
    "contorno-de-luz": "light outline", "contorno-seletivo": "selective outline", "contraluz": "backlight",
    "contraste": "high contrast", "cores-de-destaque": "accent colors", "corpo-inteiro": "full body",
    "destaque-laranja": "orange accent", "detalhe": "detailed", "escala": "sense of scale", "escudo": "shield",
    "espaco": "outer space", "espada": "sword", "esqueleto": "skeleton", "estampa": "patterned cloth",
    "estandarte": "banner", "flores": "flowers", "fogo": "fire", "frente": "front view",
    "fundo-pintado": "painted background", "jovem": "young", "kimono": "kimono", "lago": "lake",
    "lanterna": "lantern", "lua": "moon", "luz-atras": "light behind", "luz-dramatica": "dramatic light",
    "magia": "magic", "mago": "wizard", "manto": "cloak", "mar": "sea", "massa": "heavy mass",
    "menino-de-costas": "boy from behind", "minimalista": "minimalist", "moldura": "framed",
    "moldura-de-folhas": "leaf framing", "moletom-capuz": "hoodie", "monocromatico": "monochrome",
    "monstro": "monster", "montanha": "mountain", "neve": "snow", "nevoa": "mist", "nuvens-em-blocos": "blocky clouds",
    "oculos": "glasses", "olhos-brilhantes": "glowing eyes", "olhos-sob-a-franja": "eyes under bangs",
    "ouro": "gold", "paisagem": "landscape", "paladino": "paladin", "paleta-cinza": "gray palette",
    "paleta-contida": "limited palette", "paleta-de-3-cores": "three color palette",
    "paleta-dominante": "dominant palette", "paleta-fria": "cool palette", "paleta-terrosa": "earthy palette",
    "paleta-viva": "vivid palette", "pano": "cloth folds", "pano-azul": "blue cloth", "particulas": "particles",
    "pelo": "fur", "penhasco": "cliff", "perspectiva-atmosferica": "atmospheric perspective",
    "pinheiros": "pine trees", "por-do-sol": "sunset", "porta-redonda": "round door", "pose": "pose",
    "pose-de-combate": "combat pose", "pose-dinamica": "dynamic pose", "reflexo": "reflection",
    "reflexo-quebrado": "broken reflection", "rim-light": "rim light", "rim-light-colorido": "colored rim light",
    "rosa-e-laranja": "pink and orange", "rosto-discreto": "subtle face", "silhueta": "silhouette",
    "silhueta-de-arvores": "tree silhouettes", "tempestade": "storm", "textura": "texture",
    "textura-densa": "dense texture", "textura-pintada": "painterly texture", "tochas": "torches",
    "torre": "tower", "trapos": "rags", "trono": "throne", "vagalumes": "fireflies", "vermelho": "red",
    "vila": "village",
}


@dataclass
class TrainOptions:
    steps: int = 1500
    rank: int = 16
    lr: float = 1e-4
    resolution: int = 768  # lado de referência: área máxima ≈ (1,25 × resolução)²
    include_noisy: bool = False
    repeats: int = 2  # repetições por época das refs limpas (as ruidosas: 1)
    seed: int = 0
    save_every: int = 500
    min_snr: float = 5.0


@dataclass
class Item:
    n: int
    image: str
    caption: str
    width: int
    height: int
    repeats: int


def metric_words(m: dict) -> list[str]:
    """Números da decomposição → termos de estilo para a legenda."""
    words = []

    def get(path: str, default: float) -> float:
        value = _get(m, path)
        return default if value is None else value

    if get("paleta.cores_efetivas", 99) <= 32:
        words.append("limited palette")
    if get("paleta.croma_media", 1) <= 0.04:
        words.append("desaturated colors")
    if get("paleta.variacao_media_graus", 0) >= 40:
        words.append("hue shifted shading")
    if get("contorno.ausente", 0) >= 0.7:
        words.append("selective outline")
    elif get("contorno.escuro", 0) >= 0.4:
        words.append("dark outline")
    if get("luz_de_borda.fracao", 0) >= 0.15:
        words.append("rim light")
    if get("valor.contraste", 0) >= 0.7:
        words.append("high value contrast")
    if get("clusters.tamanho_medio", 0) >= 4:
        words.append("large painted pixel clusters")
    if get("clusters.dithering", 1) <= 0.005:
        words.append("no dithering")
    return words


def _get(d: dict, path: str):
    for part in path.split("."):
        if not isinstance(d, dict) or part not in d:
            return None
        d = d[part]
    return d


def caption_for(trigger: str, tipo: str, tags: list[str], metrics: dict) -> str:
    parts = [trigger, "pixel art", TIPO_EN.get(tipo, tipo)]
    parts += [TAG_EN[t] for t in tags if t in TAG_EN]
    parts += metric_words(metrics)
    return ", ".join(dict.fromkeys(p for p in parts if p))


def prepare_image(path: Path, resolution: int) -> Image.Image:
    """Ref → nativa → ampliada por vizinho (×k inteiro, k ≤ 8) → recorte central múltiplo de 64."""
    native = style.native_image(path, longest=1, background=(128, 128, 128))  # longest=1 → escala 1
    w, h = native.size
    max_area = (1.25 * resolution) ** 2
    k = 8
    while k > 1 and (max(w, h) * k > 1024 or w * h * k * k > max_area):
        k -= 1
    big = native.resize((w * k, h * k), Image.Resampling.NEAREST)
    tw, th = max(64, big.width // 64 * 64), max(64, big.height // 64 * 64)
    if big.width < tw or big.height < th:  # muito pequena: completa com a cor da borda
        canvas = Image.new("RGB", (max(tw, big.width), max(th, big.height)), big.getpixel((0, 0)))
        canvas.paste(big, ((canvas.width - big.width) // 2, (canvas.height - big.height) // 2))
        big = canvas
    left, top = (big.width - tw) // 2, (big.height - th) // 2
    return big.crop((left, top, left + tw, top + th))


def build_dataset(config: Config, folder: Path, options: TrainOptions) -> list[Item]:
    trigger = presets.settings(config)["gatilho"]
    folder.mkdir(parents=True, exist_ok=True)
    analyses = style.style_docs(config) / "analises"
    items = []
    for ref in style.load_index(config):
        noisy = ref.n in style.NO_COPY
        if noisy and not options.include_noisy:
            continue
        if not ref.path.is_file():
            print(f"  aviso: ref {ref.n} não está em {ref.path.parent}", flush=True)
            continue
        metrics_path = analyses / f"{ref.n}.json"
        metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.is_file() else {}
        image = prepare_image(ref.path, options.resolution)
        out = folder / f"{ref.n:02d}.png"
        image.save(out)
        caption = caption_for(trigger, ref.tipo, ref.tags, metrics)
        out.with_suffix(".txt").write_text(caption, encoding="utf-8")
        items.append(Item(ref.n, str(out), caption, image.width, image.height,
                          max(1, options.repeats // 2) if noisy else options.repeats))
    if len(items) < 5:
        raise AIImageError(f"só {len(items)} referências utilizáveis em {style.refs_dir(config)}")
    (folder / "dataset.json").write_text(json.dumps([asdict(i) for i in items], ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    return items


# --------------------------------------------------------------------------
# Treino
# --------------------------------------------------------------------------


def train(config: Config, base: Path, items: list[Item], out_dir: Path, options: TrainOptions,
          log_every: int = 25) -> tuple[Path, dict]:
    from .generate import _quiet, _require

    _quiet()
    torch = _require("torch")
    diffusers = _require("diffusers")
    peft = _require("peft")
    bnb = _require("bitsandbytes")
    if not torch.cuda.is_available():
        raise AIImageError("treino precisa de GPU CUDA")
    from diffusers.training_utils import compute_snr
    from diffusers.utils import convert_state_dict_to_diffusers
    from peft.utils import get_peft_model_state_dict

    data = presets.settings(config)
    random.seed(options.seed)
    torch.manual_seed(options.seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    dev = "cuda"
    compute = torch.bfloat16

    # 1. pipeline em CPU, LoRA de pixel fundido (a geração usa o mesmo)
    from .generate import fuse_loras, load_base

    pipe = load_base(diffusers, diffusers.StableDiffusionXLPipeline, base, data["modelo"], torch.float16)
    fuse_loras(pipe, base, data["lora"], data["lora_peso"])

    # 2. cache dos textos (cada legenda uma vez) e dos latentes
    torch.cuda.reset_peak_memory_stats()
    text_cache: dict[str, tuple] = {}
    pipe.text_encoder.to(dev), pipe.text_encoder_2.to(dev)
    with torch.no_grad():
        for item in items:
            if item.caption not in text_cache:
                emb, _, pooled, _ = pipe.encode_prompt(item.caption, device=dev, do_classifier_free_guidance=False)
                text_cache[item.caption] = (emb.to("cpu", compute), pooled.to("cpu", compute))
        empty = pipe.encode_prompt("", device=dev, do_classifier_free_guidance=False)
        empty = (empty[0].to("cpu", compute), empty[2].to("cpu", compute))
    pipe.text_encoder.to("cpu"), pipe.text_encoder_2.to("cpu")
    vae = pipe.vae.to(dev)
    latents = {}
    with torch.no_grad():
        for item in items:
            with Image.open(item.image) as opened:
                img = torch.from_numpy(__import__("numpy").array(opened.convert("RGB"))).permute(2, 0, 1)
            x = (img.float() / 127.5 - 1).unsqueeze(0).to(dev, torch.float16)
            latents[item.n] = (vae.encode(x).latent_dist.mean * vae.config.scaling_factor).to("cpu", compute)
    vae.to("cpu")
    torch.cuda.empty_cache()

    # 3. UNet: fp8 guardado, bf16 calculado, checkpointing, LoRA nas atenções
    unet = pipe.unet
    del pipe
    unet.to(compute)
    unet.requires_grad_(False)
    unet.add_adapter(peft.LoraConfig(r=options.rank, lora_alpha=options.rank, init_lora_weights="gaussian",
                                     target_modules=["to_k", "to_q", "to_v", "to_out.0"]))
    params = [p for p in unet.parameters() if p.requires_grad]
    for p in params:
        p.data = p.data.float()
    store_frozen_fp8(unet, torch, compute)
    unet.enable_gradient_checkpointing()
    unet.to(dev)
    unet.train()
    optimizer = bnb.optim.AdamW8bit(params, lr=options.lr, weight_decay=1e-2)
    noise_sched = diffusers.DDPMScheduler.from_pretrained(catalog.require_local(data["modelo"], base),
                                                          subfolder="scheduler")
    alphas = noise_sched.alphas_cumprod.to(dev)

    pool = [it for it in items for _ in range(it.repeats)]
    order: list[Item] = []
    losses, curve = [], []
    warmup = min(100, options.steps // 10)
    for step in range(1, options.steps + 1):
        if not order:
            order = pool[:]
            random.shuffle(order)
        item = order.pop()
        lat = latents[item.n].to(dev)
        # 10 % das vezes sem legenda: o LoRA também aprende o estilo "de fundo"
        emb, pooled = empty if random.random() < 0.1 else text_cache[item.caption]
        emb, pooled = emb.to(dev), pooled.to(dev)
        noise = torch.randn_like(lat)
        t = torch.randint(0, noise_sched.config.num_train_timesteps, (1,), device=dev).long()
        noisy = noise_sched.add_noise(lat, noise, t)
        time_ids = torch.tensor([[item.height, item.width, 0, 0, item.height, item.width]], device=dev, dtype=compute)
        lr = options.lr * min(1.0, step / max(warmup, 1)) * (0.5 * (1 + math.cos(math.pi * step / options.steps)))
        for group in optimizer.param_groups:
            group["lr"] = max(lr, options.lr * 0.05)
        with torch.autocast("cuda", dtype=compute):
            pred = unet(noisy, t, encoder_hidden_states=emb,
                        added_cond_kwargs={"text_embeds": pooled, "time_ids": time_ids}).sample
        loss = torch.nn.functional.mse_loss(pred.float(), noise.float(), reduction="none").mean()
        snr = compute_snr(noise_sched, t)
        loss = loss * (torch.minimum(snr, torch.full_like(snr, options.min_snr)) / snr).mean()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        losses.append(float(loss))
        if step % log_every == 0 or step == options.steps:
            mean = sum(losses[-log_every:]) / len(losses[-log_every:])
            curve.append([step, round(mean, 5)])
            elapsed = time.perf_counter() - started
            print(f"  passo {step}/{options.steps}  perda {mean:.4f}  {elapsed / 60:.1f} min  "
                  f"VRAM {torch.cuda.max_memory_allocated() / 1e9:.2f} GB", flush=True)
        if step % options.save_every == 0 or step == options.steps:
            name = "pxfrg-estilo.safetensors" if step == options.steps else f"pxfrg-estilo-{step}.safetensors"
            _save(unet, out_dir, name, get_peft_model_state_dict, convert_state_dict_to_diffusers, diffusers)

    report = {
        "passos": options.steps, "opcoes": asdict(options), "imagens": len(items),
        "refs": [i.n for i in items], "tempo_min": round((time.perf_counter() - started) / 60, 1),
        "vram_pico_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2),
        "perda_final": curve[-1][1] if curve else None, "curva": curve,
        "gatilho": data["gatilho"], "modelo_base": data["modelo"], "lora_pixel": data["lora"],
        "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__,
        "aviso": "uso pessoal e local: não publique os pesos nem o dataset (as refs são de outros artistas)",
    }
    (out_dir / "treino.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir / "pxfrg-estilo.safetensors", report


def store_frozen_fp8(model, torch, compute) -> int:
    """Pesos congelados de Linear/Conv2d guardados em fp8 (metade da VRAM do bf16).

    O forward converte o peso para bf16 numa cópia nova; é ela que o autograd guarda,
    então o backward funciona (o `enable_layerwise_casting` do diffusers troca o peso
    no próprio parâmetro e quebra o backward). Com gradient checkpointing, as cópias
    só existem para o bloco que está sendo recalculado.
    """
    import types

    nn, F = torch.nn, torch.nn.functional
    fp8 = torch.float8_e4m3fn
    count = 0

    def linear(self, x):
        return F.linear(x, self.weight.to(compute), None if self.bias is None else self.bias.to(compute))

    def conv(self, x):
        return self._conv_forward(x, self.weight.to(compute), None if self.bias is None else self.bias.to(compute))

    for module in model.modules():
        if isinstance(module, (nn.Linear, nn.Conv2d)) and not module.weight.requires_grad                 and module.weight.dtype != fp8 and module.weight.numel() >= 4096:
            module.weight = nn.Parameter(module.weight.data.to(fp8), requires_grad=False)
            module.forward = types.MethodType(linear if isinstance(module, nn.Linear) else conv, module)
            count += 1
    return count


def _save(unet, out_dir: Path, name: str, get_state, convert, diffusers) -> None:
    state = convert(get_state(unet))
    diffusers.StableDiffusionXLPipeline.save_lora_weights(out_dir, unet_lora_layers=state, weight_name=name,
                                                         safe_serialization=True)
