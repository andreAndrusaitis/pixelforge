"""Seu Geraldo — retrato de busto da via de IA (geraldo_ia_final_retrato, 96×128) repintado por código.

- pele parda da ficha (#c48a64) no lugar da pele clara (só a faixa de matiz da pele: a
  camisa bege fica);
- olho sem esclera branca: traço escuro de 2–3 px, pálpebra pesada de quem tem 64 anos;
- luz de borda quente no lado da luz (cabelo branco, testa, ombro) e fria do outro lado.
Render: python -m pixelforge render art/coletanea/veu/final/geraldo_retrato_repinta.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from pixelforge.palettes import parse_color
from pixelforge.paint import PARDO, Paint, retone
from pixelforge.sprite import Sprite, load_spec

NAME = "geraldo_retrato_repinta"
FPS = 4
BASE = Path(__file__).resolve().parents[1] / "geraldo_ia_final_retrato.json"
BG = (0x5c, 0x5a, 0x60)
EYES = ((33, 37, 38), (48, 37, 54))         # (x0, y, x1) de cada olho na base
MOUTH = (41, 52, 49)


def base_sprite() -> Sprite:
    px = load_spec(BASE).frames[0].pixels
    not_bg = ~np.all(px[..., :3] == np.array(BG), axis=-1)
    return Sprite(retone(px, not_bg, PARDO, hue=(20, 60), min_chroma=0.028))


def draw(eyes: bool = True, mouth: bool = False) -> Paint:
    base = base_sprite()
    p = Paint.from_sprite(base)
    ys, xs = p.ys, p.xs
    p.custom_ramp("pardo", PARDO, 4, rim="#f4b07a", outline="#3a1c1c", rim2="#9a8ab0")
    p.custom_ramp("olho", ["#1e1012", "#3a2220"], 0, rim="#3a2220", outline="#120808")
    colors = p.colors()[..., :3]
    face = p.rect(30, 30, 60, 58)
    white = face & (colors.astype(int).min(axis=-1) >= 200)
    p.set(white, "pardo", -1)                                             # sem esclera branca
    for x0, y, x1 in EYES:
        p.set(p.rect(x0, y - 1, x1, y - 1), "pardo", -2)                   # pálpebra pesada
        if eyes:
            p.set(p.rect(x0 + 1, y, x1 - 1, y), "olho", 0)                 # traço do olho
        else:
            p.set(p.rect(x0, y, x1, y), "pardo", -2)
    if mouth:
        p.set(p.rect(MOUTH[0] + 2, MOUTH[1], MOUTH[2] - 2, MOUTH[1] + 1), "olho", 1)

    # luz de borda desenhada na silhueta (fundo opaco): quente à esquerda/topo, fria à direita
    bg = np.all(colors == np.array(BG), axis=-1)
    fig = ~bg
    left_edge = fig & np.roll(bg, 1, axis=1) & (xs < 60) & (ys < 90)
    top_edge = fig & np.roll(bg, 1, axis=0) & (xs < 62)
    right_edge = fig & np.roll(bg, -1, axis=1) & (xs > 64)
    p.tone[left_edge | top_edge] = -1
    p.tone[right_edge] = -2
    return p


def render(**kw) -> Sprite:
    return draw(**kw).render(outline=False)


def build():
    return render()
