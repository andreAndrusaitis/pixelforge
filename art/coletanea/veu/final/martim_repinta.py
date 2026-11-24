"""Martim — base da via de IA (martim_ia_final_corpo) repintada por código.

A base vem com bermuda, cabelo liso e 124 px. A pintura (receita 5.1 de
docs/estilo/estilo-pixelforge.md, guia ref 21):
- reduz a figura para ~101 px (vizinho mais próximo, 0,82×): menino pequeno e magro;
- calça comprida azul-marinho no lugar da bermuda, com 3–4 dobras grandes amontoadas
  no tornozelo, mais largas que a perna (ref 21);
- crespo curto na máquina no lugar do cabelo liso: calota redonda com carocinhos de
  1 px na silhueta e brilho em grupinhos (nada de franja: a ficha não tem);
- olhos como traço de 2×1 px marrom-escuro; luz de borda quente pontual e fria do outro lado.
Moletom com forro laranja do capuz, cordões e mão no bolso vêm da base.

Render: python -m pixelforge render art/coletanea/veu/final/martim_repinta.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from pixelforge.paint import Paint
from pixelforge.sprite import Sprite, load_spec

NAME = "martim_repinta"
FPS = 4
W, H = 64, 104
BASE = Path(__file__).resolve().parents[1] / "martim_ia_final_corpo.json"
TARGET = 101          # altura da figura reduzida
OX, OY = 11, 1         # posição da base reduzida no quadro 64×104 (pé na linha 101)


def base_sprite() -> Sprite:
    a = load_spec(BASE).frames[0].pixels
    ys, xs = np.nonzero(a[..., 3] > 0)
    crop = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    k = TARGET / crop.shape[0]
    small = np.array(Image.fromarray(crop).resize((round(crop.shape[1] * k), TARGET), Image.NEAREST))
    out = np.zeros((H, W, 4), dtype=np.uint8)
    out[OY:OY + small.shape[0], OX:OX + small.shape[1]] = small
    return Sprite(pardo(out))


SKIN = ["#f6c9b9", "#e9a898", "#d1887f", "#bc726e"]          # pele clara que a IA fez (claro → escuro)
PARDO = ["#c9926a", "#b47a52", "#9a6345", "#7d4c37"]         # ficha: pardo/moreno (claro → escuro)


def pardo(px: np.ndarray) -> np.ndarray:
    """Troca só as cores de pele (rosto, mãos) pela rampa parda da ficha."""
    from pixelforge.palettes import parse_color
    out = px.copy()
    for old, new in zip(SKIN, PARDO):
        m = np.all(px[..., :3] == np.array(parse_color(old)[:3]), axis=-1) & (px[..., 3] > 0)
        out[m, :3] = parse_color(new)[:3]
    return out


def draw(eyes: bool = True, mouth: bool = False) -> Paint:
    p = Paint.from_sprite(base_sprite())
    ys, xs = p.ys, p.xs
    P = lambda pts: p.poly([(x + OX, y + OY) for x, y in pts])  # noqa: E731  (coordenadas da base reduzida)
    R = lambda x0, y0, x1, y1: p.rect(x0 + OX, y0 + OY, x1 + OX, y1 + OY)  # noqa: E731
    p.hue_ramp("calca", "#2f3550", 3, 2, hue=18, rim="#b8785a", outline="#0c0d16", rim2="#6070a8")
    p.hue_ramp("cabelo", "#2a2024", 3, 2, hue=20, rim="#b8704a", outline="#0a060a", rim2="#4a4a6a")
    p.custom_ramp("olho", ["#2e1a18", "#4a2a24"], 0, rim="#4a2a24", outline="#1a0c0c")
    p.custom_ramp("pardo", PARDO[::-1], 2, rim="#f0a868", outline="#3a1c18", rim2="#9a86a8")

    # --- calça comprida no lugar da bermuda e das canelas ------------------------------------
    legs_area = (ys >= 52 + OY) & (ys <= 90 + OY)
    p.erase(legs_area & ~R(-2, 86, 40, 101) & ((p.xs < 6 + OX) | (p.xs > 35 + OX)))
    far = P([(8, 52), (18.5, 52), (16.5, 64), (12.5, 76), (10, 86), (2.5, 86), (5, 76), (8, 64)])
    near = P([(20.5, 52), (32.5, 52), (33.5, 64), (34, 76), (34.5, 86), (25.5, 86), (25, 76), (23, 64)])
    for leg in (far, near):
        p.erase(leg)
    p.set(far, "calca", -1)                                               # perna de trás um tom abaixo
    p.set(far & P([(8, 52), (12, 52), (8, 70), (5, 78), (4, 86), (2.5, 86), (5, 76), (8, 64)]), "calca", 0)
    p.set(near, "calca", 0)
    p.set(near & P([(29, 52), (32.5, 52), (33.5, 64), (34, 76), (34.5, 86), (31, 86), (30.5, 70)]), "calca", -1)
    for pts, t in (([(9, 58), (16, 56), (14.5, 61), (9.5, 63)], 1),           # dobra grande na coxa (luz)
                   ([(9.5, 63), (15.5, 61), (13, 66), (8.5, 68)], -2),
                   ([(23.5, 60), (29, 58), (28, 63), (24, 65)], 1),
                   ([(25, 66), (33, 64), (33.5, 69), (25.5, 71)], -2),           # atrás do joelho
                   ([(25, 72), (31, 71.5), (30, 75), (25.5, 75.5)], 1)):         # joelho
        p.set(P(pts) & (far | near), "calca", t)
    p.set(P([(18.5, 53), (21, 53), (20.5, 63)]), "calca", -3)               # entreperna
    # tecido amontoado no tornozelo: 3 dobras desencontradas, mais largas que a perna (ref 21)
    for k, (cx, y) in enumerate(((6, 80), (6.5, 83.5), (6, 87), (30, 80), (29.5, 83.5), (30, 87))):
        half = 4.6 + (k % 3) * 0.6
        band = P([(cx - half, y), (cx + half, y - 1), (cx + half + 0.5, y + 2.2), (cx - half - 0.5, y + 2.8)])
        band &= p.moved(far | near, 1, 0) | p.moved(far | near, -1, 0)   # só 1 px além da perna
        p.set(band, "calca", 0 if k < 3 else 1)
        p.set(band & ~p.moved(band, 0, 1), "calca", 1 if k < 3 else 2)      # aresta da dobra na luz
        p.set(band & ~p.moved(band, 0, -1), "calca", -3)                    # vão escuro embaixo
    for fam in {p.family_of(c) for c in PARDO}:                           # canela nua da bermuda: vira calça
        p.set((ys >= 84 + OY) & (ys <= 92 + OY) & (p.rid == p._r(fam)), "calca", -1)
    pants = p.rid == p._r("calca")
    p.texture(pants, -1, 0.05, seed=6, stroke=(1, 2))
    p.painterly(pants, edge=0.5, speck=0.0, seed=7)
    p.shift(R(6, 50, 34, 51) & (p.rid >= 0) & ~pants, -1)                   # bainha do moletom faz sombra

    # --- crespo na máquina: a silhueta da base arredondada, textura de cachinho, linha reta --------
    hair_fam = p.family_of("#2a1c22")
    hair_old = (p.rid == p._r(hair_fam)) & (ys <= 11 + OY)
    hairline = 4.5 + OY + ((xs - 18 - OX) / 8.0) ** 2 * 5.0                # reta na testa, desce nas têmporas
    cap = p.ellipse(18 + OX, 8.5 + OY, 8.6, 8.4) & (ys <= hairline)
    p.erase(hair_old & ~cap)                                              # mechas soltas do liso somem
    p.set(cap, "cabelo", 0)
    p.set(cap & (xs >= 21 + OX), "cabelo", -1)
    p.set(cap & (xs <= 12 + OX), "cabelo", -1)                            # nuca
    rng = np.random.default_rng(3)
    for y in range(0, 12):
        for x in range(8, 28):
            if cap[y + OY, x + OX] and (x + 2 * y) % 3 == 0:              # cachinhos: 1 px um tom acima/abaixo
                p.px(x + OX, y + OY, "cabelo", 1 if rng.random() < 0.55 else -2)
    rimtop = cap & ~p.moved(cap, 0, 1)
    for x, y in zip(*np.nonzero(rimtop.T)):
        if x % 3 == 1:
            p.px(int(x), int(y) - 1, "cabelo", 0 if x < 17 + OX else -1)   # carocinho de 1 px
    for cx, cy in ((13, 2), (15, 1), (18, 1), (12, 4)):                    # brilho em grupos de 1–3 px
        p.pixels([(cx + OX, cy + OY), (cx + 1 + OX, cy + OY)], "cabelo", 2)
    skin_fam = "pardo"
    forehead = p.ellipse(18 + OX, 9 + OY, 8, 8.5) & ~cap & (ys <= 9 + OY) & (p.rid < 0)
    p.set(forehead, skin_fam, 0)                                          # testa onde era franja
    p.shift(p.moved(cap, 0, 1) & ~cap & (p.rid == p._r(skin_fam)), -1)     # sombra da linha do cabelo

    # rosto: olhos como traço marrom-escuro de 2×1 px, boca curta
    E = lambda pts: [(x + OX, y + OY) for x, y in pts]  # noqa: E731
    head = p.ellipse(19.5 + OX, 10 + OY, 8.5, 8.5)
    white = np.all(p.colors()[..., :3] >= 235, axis=-1) & head & (ys <= 13 + OY)
    p.set(white, "pardo", -1)                                             # nada de esclera branca
    p.pixels(E([(17, 8), (18, 8), (19, 8), (22, 8), (23, 8), (24, 8)]), "olho", 0)   # sobrancelha grossa (2 linhas)
    p.pixels(E([(17, 9), (18, 9), (19, 9), (23, 9), (24, 9)]), "olho", 0)
    p.set(head & (ys == 10 + OY) & (xs >= 16 + OX) & (xs <= 25 + OX), "pardo", -1)    # sombra da testa nos olhos
    if eyes:                                                              # traço de 2–3×1 px marrom-escuro
        p.pixels(E([(17, 11), (18, 11), (19, 11), (22, 11), (23, 11)]), "olho", 1)
    else:
        p.pixels(E([(17, 11), (18, 11), (19, 11), (22, 11), (23, 11)]), "pardo", -1)
    if mouth:
        p.pixels(E([(20, 14), (21, 14), (20, 15)]), "olho", 0)

    # --- luz de borda: laranja do fim de tarde (esquerda), fria do outro lado ------------------
    p.rim_spots([(36 + OX - 34, 0, 26 + OX, 8), (0 + OX - 2, 20, 10 + OX, 34), (OX - 2, 36, 8 + OX, 50),
                 (OX - 4, 80, 6 + OX, 101)], width=1)
    p.rim_spots([(28 + OX, 20, 44 + OX, 40), (30 + OX, 60, 44 + OX, 90)], second=True, dirs=((1, 0),))
    return p


def render(**kw) -> Sprite:
    return draw(**kw).render(outline=False)


def build():
    return render()
