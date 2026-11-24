"""Martim — retrato de busto da via de IA (martim_ia_final_retrato, 96×128) repintado por código.

- pele parda da ficha (#b47a52) no lugar da pele clara da base, tom a tom pela luminosidade;
- crespo curto na máquina no lugar do cabelo liso volumoso com franja: calota rente ao
  crânio, linha reta na testa descendo nas têmporas, textura de cachinho em 1–2 px, brilho
  em grupinhos, carocinhos na silhueta; a testa aparece onde era franja;
- luz de borda quente do lado da luz.
Render: python -m pixelforge render art/coletanea/veu/final/martim_retrato_repinta.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from pixelforge.palettes import parse_color
from pixelforge.paint import Paint
from pixelforge.sprite import Sprite, load_spec

NAME = "martim_retrato_repinta"
FPS = 4
BASE = Path(__file__).resolve().parents[1] / "martim_ia_final_retrato.json"
BG = "#978d88"
SKIN_MAP = {"#d5c9c9": "#e0b490", "#cfafa5": "#d4a07a", "#cfaaa0": "#d4a07a", "#c3958d": "#c08a62",
            "#b07d78": "#a8724e", "#a0706c": "#a8724e", "#a36562": "#95603f", "#8b5453": "#7d4c37",
            "#6a3739": "#5e3426"}
CX, CY = 48, 47            # centro do crânio


def base_sprite() -> Sprite:
    px = load_spec(BASE).frames[0].pixels.copy()
    out = px.copy()
    for old, new in SKIN_MAP.items():
        m = np.all(px[..., :3] == np.array(parse_color(old)[:3]), axis=-1)
        out[m, :3] = parse_color(new)[:3]
    return Sprite(out)


def draw(eyes: bool = True, mouth: bool = False) -> Paint:
    base = base_sprite()
    p = Paint.from_sprite(base)
    ys, xs = p.ys, p.xs
    p.hue_ramp("cabelo", "#2e2226", 3, 2, hue=20, rim="#b8704a", outline="#0a060a", rim2="#5a5a7a")
    p.custom_ramp("pele", ["#5e3426", "#7d4c37", "#95603f", "#a8724e", "#c08a62", "#d4a07a"], 3,
                  rim="#f0b080", outline="#3a1c18", rim2="#9a86a8")
    p.custom_ramp("fundo", [BG], 0, rim=BG, outline=BG)
    bg_color = np.array(parse_color(BG)[:3])
    colors = p.colors()[..., :3]
    is_bg = np.all(colors == bg_color, axis=-1)

    # cabelo antigo = tons escuros acima do queixo, fora do rosto
    dark = (colors.astype(int).sum(axis=-1) < 260) & (ys <= 60) & ~is_bg
    hairline = 41 + ((xs - CX) / 20.0) ** 2 * 10                            # reta na testa, desce nas têmporas
    skull = p.ellipse(CX, CY + 2, 24, 23)
    cap = skull & (ys <= hairline) & (ys <= 58)
    face = p.ellipse(CX, 66, 22, 24) & ~cap
    old_hair_zone = (ys <= 56) & ~cap & ~face & ~is_bg & ~p.ellipse(CX, 64, 30, 16)   # orelhas ficam
    p.set(old_hair_zone, "fundo", 0)                                      # volume liso some (todos os tons)
    forehead = dark & face & (ys <= 56)
    stray = face & (ys <= 70) & ~is_bg & ~np.isin(p.rid, [p._r(p.family_of(c)) for c in SKIN_MAP.values()
                                                          if tuple(parse_color(c)[:3]) in p._family]) & ~dark
    p.set(stray, "pele", 1)                                               # restos cinza do cabelo no rosto
    p.set(forehead, "pele", 1)                                            # franja vira testa
    p.set(forehead & (xs >= CX + 8), "pele", 0)
    p.set(cap, "cabelo", 0)
    p.set(cap & (xs >= CX + 9), "cabelo", -1)                             # lado da sombra
    p.set(cap & (ys >= hairline - 3) & (np.abs(xs - CX) > 14), "cabelo", -1)   # têmporas
    rng = np.random.default_rng(4)
    for y in range(20, 58):
        for x in range(20, 76):
            if cap[y, x] and (x + 2 * y) % 3 == 0:                         # cachinho: 1–2 px um tom acima/abaixo
                t = 1 if rng.random() < 0.5 else -2
                p.px(x, y, "cabelo", t)
                if rng.random() < 0.4 and x + 1 < 96 and cap[y, x + 1]:
                    p.px(x + 1, y, "cabelo", t)
    for cx, cy in ((36, 30), (40, 28), (44, 27), (33, 34), (38, 32)):         # brilho em grupos de 1–3 px
        p.pixels([(cx, cy), (cx + 1, cy), (cx, cy + 1)], "cabelo", 2)
    rimtop = cap & ~p.moved(cap, 0, 1)
    for x, y in zip(*np.nonzero(rimtop.T)):
        if x % 3 == 0:
            p.px(int(x), int(y) - 1, "cabelo", 0 if x < CX else -1)        # carocinho na silhueta
    p.set(p.moved(cap, 0, 1) & ~cap & face, "pele", -1)                    # sombra da linha do cabelo
    p.set(p.moved(cap, 0, 2) & ~cap & face & ~p.moved(cap, 0, 1), "pele", 0)
    if not eyes:                                                          # piscar: o traço do olho vira pálpebra
        lids = (ys >= 60) & (ys <= 64) & face & (colors.astype(int).sum(axis=-1) < 200)
        p.set(lids & ((np.abs(xs - 36.5) <= 4) | (np.abs(xs - 60.5) <= 4)), "pele", -2)
    if mouth:
        p.set(p.ellipse(48, 81, 3, 1.5), "pele", -3)

    # luz de borda desenhada na silhueta (o retrato tem fundo opaco): quente à esquerda/topo, fria à direita
    p.tone[cap & ~p.moved(cap, 1, 0) & (xs < CX)] = -1
    p.tone[cap & ~p.moved(cap, 0, 1) & (xs < CX - 4)] = -1
    p.tone[cap & ~p.moved(cap, -1, 0) & (xs > CX + 6)] = -2
    return p


def render(**kw) -> Sprite:
    return draw(**kw).render(outline=False)


def build():
    return render()
