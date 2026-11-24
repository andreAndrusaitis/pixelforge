"""Nota técnica de uma arte contra as referências do mesmo tipo.

Cada métrica da decomposição vira uma faixa (p10–p90 das referências do tipo).
Dentro da faixa = 1; fora, cai com a distância. A nota é a média ponderada × 100.
A nota técnica é metade da conta: o agente `critico-de-arte` soma a rubrica visual.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

# (caminho na decomposição, peso, escala log?, rótulo)
METRICS = [
    ("paleta.cores_efetivas", 10, True, "cores efetivas"),
    ("paleta.croma_media", 5, False, "croma média"),
    ("paleta.variacao_media_graus", 8, False, "variação de matiz nas rampas (°)"),
    ("paleta.tons_por_rampa", 10, False, "tons por rampa"),
    ("valor.niveis", 8, False, "níveis de valor"),
    ("clusters.densidade_detalhe", 10, False, "densidade de detalhe"),
    ("valor.contraste", 10, False, "contraste de valor"),
    ("valor.desvio", 4, False, "desvio de valor"),
    ("clusters.tamanho_medio", 15, True, "tamanho médio dos blocos (px)"),
    ("clusters.orfaos", 10, False, "pixels órfãos"),
    ("clusters.dithering", 4, False, "dithering"),
    ("contorno.escuro", 4, False, "contorno escuro"),
    ("contorno.ausente", 4, False, "contorno ausente (seletivo)"),
    ("luz_de_borda.fracao", 6, False, "luz de borda (rim light)"),
    ("luz.forca", 6, False, "força da direção de luz"),
    ("composicao.espaco_negativo", 4, False, "espaço negativo"),
    ("composicao.dist_tercos", 4, False, "foco × terços"),
    ("figura.proporcao_cabecas", 6, False, "proporção (cabeças)"),
    ("figura.altura_px", 15, True, "altura da figura (px)"),
]

TYPE_GROUPS = {
    "retrato": ["retrato"],
    "personagem": ["personagem", "criatura"],
    "cenario": ["cenario"],
    "cena": ["cena", "cenario"],
}


def get(d: dict, path: str):
    for part in path.split("."):
        if not isinstance(d, dict) or part not in d:
            return None
        d = d[part]
    return d if isinstance(d, (int, float)) and not isinstance(d, bool) else None


@dataclass
class Reference:
    n: int
    arquivo: str
    tipo: str
    metrics: dict


def load_references(index_path: Path, analyses_dir: Path) -> list[Reference]:
    index = json.loads(Path(index_path).read_text(encoding="utf-8"))
    refs = []
    for item in index["itens"]:
        p = Path(analyses_dir) / f"{item['n']}.json"
        if p.is_file():
            refs.append(Reference(item["n"], item["arquivo"], item["tipo"],
                                  json.loads(p.read_text(encoding="utf-8"))))
    return refs


@dataclass
class MetricScore:
    path: str
    label: str
    value: float
    low: float
    high: float
    score: float
    weight: float


@dataclass
class Result:
    nota: float
    tipo: str
    scores: list[MetricScore] = field(default_factory=list)
    nearest: list[Reference] = field(default_factory=list)

    def fora_da_faixa(self) -> list[MetricScore]:
        return sorted((s for s in self.scores if s.score < 0.999), key=lambda s: (s.score - 1) * s.weight)

    def as_dict(self) -> dict:
        return {
            "nota_tecnica": self.nota,
            "tipo": self.tipo,
            "referencias_proximas": [r.n for r in self.nearest],
            "metricas": [{"metrica": s.label, "chave": s.path, "valor": s.value, "faixa": [s.low, s.high],
                          "nota": round(s.score, 3), "peso": s.weight} for s in self.scores],
        }


def _pool(refs: list[Reference], tipo: str) -> list[Reference]:
    group = [r for r in refs if r.tipo in TYPE_GROUPS.get(tipo, [tipo])]
    return group if len(group) >= 4 else refs


def score(metrics: dict, refs: list[Reference], tipo: str, exclude: str | None = None) -> Result:
    """`exclude`: arquivo de referência a deixar de fora (avaliar uma referência sem ela mesma)."""
    pool = _pool([r for r in refs if r.arquivo != exclude], tipo)
    scores = []
    for path, weight, log, label in METRICS:
        value = get(metrics, path)
        vals = [v for v in (get(r.metrics, path) for r in pool) if v is not None]
        if value is None or len(vals) < 3:
            continue
        f = (lambda x: math.log(max(x, 1e-6))) if log else (lambda x: x)
        tv = np.array([f(v) for v in vals])
        lo, hi = np.percentile(tv, [10, 90])
        width = max(hi - lo, 0.15 if log else 0.02 + 0.1 * abs(hi))
        x = f(value)
        dist = 0.0 if lo <= x <= hi else min(abs(x - lo), abs(x - hi)) / width
        s = math.exp(-1.5 * dist)
        back = (lambda y: math.exp(y)) if log else (lambda y: y)
        scores.append(MetricScore(path, label, round(float(value), 4), round(back(lo), 4), round(back(hi), 4),
                                  s, weight))
    total_w = sum(s.weight for s in scores) or 1
    nota = round(100 * sum(s.score * s.weight for s in scores) / total_w, 1)
    return Result(nota, tipo, scores, nearest(metrics, pool))


def nearest(metrics: dict, pool: list[Reference], k: int = 3) -> list[Reference]:
    paths = [m[0] for m in METRICS]
    mat = np.array([[get(r.metrics, p) if get(r.metrics, p) is not None else np.nan for p in paths] for r in pool],
                   dtype=float)
    keep = ~np.isnan(mat).all(axis=0)
    mat = mat[:, keep]
    paths = [p for p, k in zip(paths, keep) if k]
    mu, sd = np.nanmean(mat, axis=0), np.nanstd(mat, axis=0) + 1e-6
    me = np.array([get(metrics, p) if get(metrics, p) is not None else np.nan for p in paths], dtype=float)
    dist = []
    for i, r in enumerate(pool):
        diff = ((mat[i] - me) / sd) ** 2
        ok = ~np.isnan(diff)
        dist.append(float(np.sqrt(diff[ok].mean())) if ok.any() else 1e9)
    return [pool[i] for i in np.argsort(dist)[:k]]


def comparison_sheet(art_native: np.ndarray, result: Result, refs_dir: Path, title: str) -> Image.Image:
    from .analyze import analyze_file

    cell = 260
    panels = []

    def fit(arr: np.ndarray) -> Image.Image:
        img = Image.fromarray(arr).convert("RGBA")
        s = max(1, min(cell // img.width, cell // img.height))
        img = img.resize((img.width * s, img.height * s), Image.Resampling.NEAREST)
        img.thumbnail((cell, cell), Image.Resampling.NEAREST)
        return img

    panels.append((fit(art_native), f"{title}  ·  nota técnica {result.nota}"))
    for r in result.nearest:
        path = Path(refs_dir) / r.arquivo
        if path.is_file():
            _, ex = analyze_file(path)
            panels.append((fit(ex["native"]), f"ref {r.n} ({r.tipo})"))
    W = (cell + 20) * len(panels)
    off = result.fora_da_faixa()
    H = cell + 60 + 16 * (len(off) + 2)
    sheet = Image.new("RGB", (max(W, 700), H), (24, 20, 37))
    d = ImageDraw.Draw(sheet)
    for i, (img, label) in enumerate(panels):
        x = i * (cell + 20) + 10
        sheet.paste(img, (x + (cell - img.width) // 2, 30 + (cell - img.height) // 2), img)
        d.text((x, 10), label, fill=(234, 228, 214))
    y = cell + 45
    d.text((10, y), "fora da faixa das referencias (pior primeiro):", fill=(255, 205, 117))
    for s in off:
        y += 16
        d.text((16, y), f"{s.label}: {s.value}  (faixa {s.low}-{s.high})  nota {round(s.score, 2)}  peso {s.weight}",
               fill=(200, 190, 200))
    return sheet
