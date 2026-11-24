"""Presets de estilo da IA de imagem (`[ia]` e `[ia.presets.<nome>]` no pixelforge.toml).

Um preset junta as duas metades da via de IA:
  geração     prompt, negativo, resolucao, passos, guia, lora_peso, forca, ref_peso
  pixelização tamanho, cores, paleta, metodo, fundo, fundo_tolerancia, contorno, limpeza, fundir,
              contraste, saturacao, grade
Sem dependências pesadas: `ia pixelizar --preset` funciona sem o extra.
"""

from __future__ import annotations

import copy

from ..config import Config, merge
from ..convert import parse_size

DEFAULTS: dict = {
    "modelos": "models",
    "modelo": "dreamshaper-xl-lightning",
    "lora": "pixel-art-xl",
    "lora_peso": 1.1,
    "passos": 0,  # 0 = padrão do modelo
    "guia": 0.0,  # 0 = padrão do modelo
    "precisao": "fp8",  # fp8 (UNet em 2,6 GB) | fp16
    "offload": "modelo",  # modelo | sequencial | nenhum
    "preset": "retrato",
    "forca": 0.55,  # imagem → imagem: 0 = igual à entrada, 1 = ignora a entrada
    "ref_peso": 0.55,  # força do IP-Adapter (referência de personagem)
    "ref_tipo": "plus",  # plus (corpo e roupa) | face (rosto)
    "estilo_peso": 0.6,  # imagens de estilo (refs do preset) só nas camadas de estilo da UNet
    "estilo_lora": "models/pixelforge-estilo/pxfrg-estilo.safetensors",  # de `ia treinar`; "" desliga
    "estilo_lora_peso": 0.8,
    "gatilho": "pxfrg style",  # palavra do LoRA de estilo (vai na frente do prompt)
    "presets": {},
}

PRESET_KEYS = {
    "prompt", "negativo", "resolucao", "passos", "guia", "lora_peso", "forca", "ref_peso", "ref_tipo",
    "tamanho", "cores", "paleta", "metodo", "fundo", "fundo_tolerancia", "contorno", "limpeza", "fundir", "contraste",
    "saturacao", "grade", "descricao", "tipo", "refs", "estilo_peso",
}

# pixelização: chave do preset → campo de PixelizeOptions
PIXEL_FIELDS = {
    "tamanho": "size", "cores": "colors", "paleta": "palette", "metodo": "method", "fundo": "remove_bg",
    "fundo_tolerancia": "bg_tolerance",
    "contorno": "outline", "limpeza": "cleanup", "fundir": "merge", "contraste": "contrast",
    "saturacao": "saturation", "grade": "grid",
}
METHODS = {"moda": "mode", "mediana": "median", "mode": "mode", "median": "median"}
OUTLINES = {"seletivo": "selective", "nenhum": "", "não": ""}


def settings(config: Config) -> dict:
    return merge(copy.deepcopy(DEFAULTS), config.data.get("ia", {}))


def preset(config: Config, name: str | None) -> dict:
    data = settings(config)
    name = name or data["preset"]
    presets = data["presets"]
    if name not in presets:
        disponiveis = ", ".join(sorted(presets)) or "nenhum (veja [ia.presets] no pixelforge.toml)"
        raise KeyError(f"preset de IA '{name}' não existe. Disponíveis: {disponiveis}")
    values = dict(presets[name])
    unknown = set(values) - PRESET_KEYS
    if unknown:
        raise ValueError(f"preset de IA '{name}': chaves desconhecidas: {', '.join(sorted(unknown))}")
    return values


def pixel_options(values: dict) -> dict:
    """Chaves de pixelização do preset → dicionário para PixelizeOptions.from_dict."""
    out = {}
    for key, field in PIXEL_FIELDS.items():
        if key not in values or values[key] is None:
            continue
        value = values[key]
        if key == "metodo":
            value = METHODS.get(value, value)
        elif key == "contorno":
            value = OUTLINES.get(value, value)
        elif key == "grade":
            value = str(value)
        out[field] = value
    return out


def resolution(values: dict, fallback: int = 1024) -> tuple[int, int]:
    """Resolução de geração, múltipla de 8 (exigência do SDXL)."""
    w, h = parse_size(values.get("resolucao", fallback))
    return max(64, w // 8 * 8), max(64, h // 8 * 8)


LEAD = "pixel art"


def style_lora_dir(config: Config):
    from pathlib import Path

    return (config.root / settings(config)["estilo_lora"]).parent if settings(config)["estilo_lora"] else (
        config.root / "models" / "pixelforge-estilo")


def style_lora_path(config: Config):
    """Arquivo do LoRA de estilo, se existir (o treino é opcional)."""
    from pathlib import Path

    raw = settings(config)["estilo_lora"]
    if not raw:
        return None
    path = Path(raw)
    path = path if path.is_absolute() else config.root / path
    return path if path.is_file() else None


def join_prompt(description: str, base: str, trigger: str = "") -> str:
    """"pixel art" na frente, depois a descrição, depois o resto do estilo do preset.

    O CLIP lê só ~77 tokens e pesa mais o começo: sem o gatilho na frente, uma
    descrição longa vira foto; sem a descrição logo depois, ela se perde no estilo.
    """
    base = (base or "").strip(" ,")
    lead = ""
    if base.lower().startswith(LEAD):
        lead, base = LEAD, base[len(LEAD):].strip(" ,")
    parts = [p.strip(" ,") for p in (trigger, lead, description, base) if p and p.strip(" ,")]
    return ", ".join(parts)
