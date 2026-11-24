"""Referências de estilo do autor dentro da via de IA (sem dependências pesadas).

- escolhe as referências de cada preset (ou as mais próximas da arte) no índice
  `docs/estilo/referencias.json`, sem as que a seção 7 do estilo manda não copiar;
- prepara a imagem de estilo: a referência reduzida à resolução nativa e
  reampliada em múltiplo inteiro (pixel limpo) para o IP-Adapter e o treino;
- dá a nota técnica de uma arte (`pixelforge.style.compare`) e monta a folha
  resultado + 3 referências do mesmo tipo para revisão.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from ..config import Config

# docs/estilo/estilo-pixelforge.md §7: marcas de imagem gerada/reamostrada — copiar a ideia, não a textura
NO_COPY = frozenset({17, 24, 25, 31})

# preset de IA → tipo do `estilo comparar`
DEFAULT_TIPO = {"retrato": "retrato", "personagem-corpo": "personagem", "cenario": "cenario",
                "cena-noturna": "cena"}


@dataclass
class StyleRef:
    n: int
    arquivo: str
    tipo: str
    tags: list[str]
    path: Path


def refs_dir(config: Config) -> Path:
    from ..style.cli import refs_dir as _refs_dir

    return _refs_dir(config)


def style_docs(config: Config) -> Path:
    return config.root / "docs" / "estilo"


def load_index(config: Config) -> list[StyleRef]:
    path = style_docs(config) / "referencias.json"
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    folder = refs_dir(config)
    return [StyleRef(i["n"], i["arquivo"], i["tipo"], list(i.get("tags", [])), folder / i["arquivo"])
            for i in data["itens"]]


def tipo_for(preset_name: str, values: dict) -> str:
    return values.get("tipo") or DEFAULT_TIPO.get(preset_name, "personagem")


def pick(config: Config, numbers: list[int]) -> list[StyleRef]:
    """Referências pelo número, na ordem pedida; avisa das que faltam na pasta."""
    index = {r.n: r for r in load_index(config)}
    missing = [n for n in numbers if n not in index]
    if missing:
        raise ValueError(f"referência(s) {missing} não estão em docs/estilo/referencias.json")
    found = [index[n] for n in numbers]
    absent = [r.n for r in found if not r.path.is_file()]
    if absent:
        raise FileNotFoundError(f"imagens das referências {absent} não estão em {refs_dir(config)}")
    return found


def parse_numbers(text: str) -> list[int]:
    return [int(v) for v in str(text).replace(" ", "").split(",") if v]


def native_image(path: Path, longest: int = 768, background=(128, 128, 128)) -> Image.Image:
    """Referência → resolução nativa (desfaz a grade) → reampliada em múltiplo inteiro (vizinho)."""
    from ..style.analyze import analyze_file

    _, extras = analyze_file(path)
    native = Image.fromarray(extras["native"]).convert("RGBA")
    scale = max(1, longest // max(native.size))
    big = native.resize((native.width * scale, native.height * scale), Image.Resampling.NEAREST)
    flat = Image.new("RGB", big.size, background)
    flat.paste(big, mask=big.getchannel("A"))
    return flat


def references(config: Config):
    from ..style.compare import load_references

    refs = load_references(style_docs(config) / "referencias.json", style_docs(config) / "analises")
    if len(refs) < 5:
        raise ValueError("faltam as decomposições das referências (docs/estilo/analises/): "
                         "rode `python -m pixelforge estilo analisar --refs`")
    return refs


def score_pixels(rgba: np.ndarray, tipo: str, config: Config, refs=None):
    """Nota técnica (0–100) de uma arte em resolução nativa contra as refs do tipo."""
    from ..style.analyze import analyze_array
    from ..style.compare import score

    metrics, extras = analyze_array(rgba, native=True)
    return score(metrics, refs if refs is not None else references(config), tipo), extras


def review_sheet(rgba: np.ndarray, tipo: str, config: Config, title: str, chosen: list[int] | None = None,
                 refs=None) -> tuple[Image.Image, object]:
    """Folha: arte + 3 referências do mesmo tipo (as do preset, ou as mais próximas) + métricas fora da faixa."""
    from ..style.compare import comparison_sheet

    refs = refs if refs is not None else references(config)
    result, extras = score_pixels(rgba, tipo, config, refs)
    if chosen:
        by_n = {r.n: r for r in refs}
        result.nearest = [by_n[n] for n in chosen if n in by_n][:3] or result.nearest
    return comparison_sheet(extras["native"], result, refs_dir(config), title), result
