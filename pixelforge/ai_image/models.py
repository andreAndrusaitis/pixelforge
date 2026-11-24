"""Catálogo de pesos da IA de imagem, pasta de modelos e download.

Tudo vem do Hugging Face e precisa ser aberto (sem aceite de licença nem login).
Um repositório restrito ("gated") nunca é baixado: o comando para e diz qual é
e onde aceitar — a decisão é do autor.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from . import AIImageError, INSTALL_HINT


@dataclass(frozen=True)
class Weights:
    key: str
    repo: str
    kind: str  # base | lora | vae | ip-adapter
    patterns: tuple[str, ...]
    file: str = ""  # arquivo principal (LoRA / IP-Adapter)
    note: str = ""
    defaults: dict = field(default_factory=dict)

    @property
    def folder(self) -> str:
        return self.repo.replace("/", "--")


CATALOG: dict[str, Weights] = {w.key: w for w in (
    Weights("dreamshaper-xl-lightning", "Lykon/dreamshaper-xl-lightning", "base",
            ("model_index.json", "scheduler/*", "tokenizer*/*", "*/config.json", "*/*.fp16.safetensors"),
            note="SDXL ajustado + Lightning: 4–8 passos, guia ~2 (padrão)",
            defaults={"passos": 6, "guia": 2.0}),
    Weights("sdxl-base", "stabilityai/stable-diffusion-xl-base-1.0", "base",
            ("model_index.json", "scheduler/*", "tokenizer*/*", "*/config.json", "*/*.fp16.safetensors"),
            note="SDXL 1.0 original: 25–30 passos, guia ~6 (mais lento)",
            defaults={"passos": 28, "guia": 6.0}),
    Weights("pixel-art-xl", "nerijs/pixel-art-xl", "lora", ("*.safetensors",), "pixel-art-xl.safetensors",
            note="LoRA de pixel art (blocos de ~8 px em 1024)"),
    Weights("pixelart-redmond", "artificialguybr/PixelArtRedmond", "lora", ("*.safetensors",),
            "PixelArtRedmond-Lite64.safetensors", note="LoRA alternativo (gatilho: PixArFK)"),
    Weights("vae-fp16", "madebyollin/sdxl-vae-fp16-fix", "vae",
            ("config.json", "diffusion_pytorch_model.safetensors"), note="VAE do SDXL sem NaN em fp16"),
    Weights("ip-adapter", "h94/IP-Adapter", "ip-adapter",
            ("models/image_encoder/config.json", "models/image_encoder/model.safetensors",
             "sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors",
             "sdxl_models/ip-adapter-plus-face_sdxl_vit-h.safetensors"),
            note="referência de personagem (plus = corpo/roupa; plus-face = rosto)"),
)}

DEFAULT_SET = ("dreamshaper-xl-lightning", "pixel-art-xl", "vae-fp16", "ip-adapter")


def models_dir(setting: str = "", root: Path | None = None) -> Path:
    """$PIXELFORGE_MODELS > `[ia] modelos` (relativo à raiz do projeto) > ./models."""
    raw = os.environ.get("PIXELFORGE_MODELS") or setting or "models"
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (root or Path.cwd()) / path
    return path


def local_path(weights: Weights, base: Path) -> Path:
    return base / weights.folder


def is_downloaded(weights: Weights, base: Path) -> bool:
    folder = local_path(weights, base)
    if not folder.is_dir():
        return False
    if weights.file:
        return any(folder.rglob(weights.file))
    return any(folder.rglob("*.safetensors"))


def size_on_disk(weights: Weights, base: Path) -> int:
    folder = local_path(weights, base)
    if not folder.is_dir():
        return 0
    return sum(f.stat().st_size for f in folder.rglob("*") if f.is_file() and ".cache" not in f.parts)


def get(key: str) -> Weights:
    if key not in CATALOG:
        raise AIImageError(f"modelo '{key}' desconhecido. Catálogo: {', '.join(CATALOG)}")
    return CATALOG[key]


def require_local(key: str, base: Path) -> Path:
    weights = get(key)
    if not is_downloaded(weights, base):
        raise AIImageError(f"modelo '{key}' não está em {local_path(weights, base)}. "
                           f"Baixe com: python -m pixelforge ia modelos --baixar {key}")
    return local_path(weights, base)


def download(key: str, base: Path) -> Path:
    """Baixa os arquivos do catálogo; recusa repositórios restritos (gated)."""
    weights = get(key)
    try:
        from huggingface_hub import HfApi, snapshot_download
    except ImportError:
        raise AIImageError(f"download precisa do huggingface_hub. Instale: {INSTALL_HINT}") from None
    info = HfApi().model_info(weights.repo)
    if info.gated:
        raise AIImageError(
            f"'{weights.repo}' é restrito: exige aceitar a licença e fazer login no Hugging Face "
            f"(https://huggingface.co/{weights.repo}). Não baixei — aceite lá, se quiser, e rode de novo.")
    path = snapshot_download(weights.repo, allow_patterns=list(weights.patterns),
                             local_dir=local_path(weights, base))
    return Path(path)
