"""Seu Geraldo — base da via de IA (geraldo_ia_final_corpo) repintada por código.

O que a pintura acrescenta à base (receita 5.2 de docs/estilo/estilo-pixelforge.md):
- aba fazendo sombra nos olhos: terço de cima do rosto um tom abaixo, olhos como traço
  escuro dentro da sombra, um ponto de pele tocado pela luz (ref 14);
- aba com borda clara em cima e faixa escura embaixo;
- mãos enormes (~10×14 px) com dedos em blocos e nó claro (ref 1);
- cicatriz lisa e brilhante no antebraço esquerdo (lado de quem olha: direita);
- luz de borda pontual de duas temperaturas (ref 22).
Estados do chapéu: "cabeca", "erguido" (meio do tirar_chapeu), "mao" (segurando ao lado).

Render: python -m pixelforge render art/coletanea/veu/final/geraldo_repinta.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from pixelforge.palettes import parse_color
from pixelforge.paint import Paint
from pixelforge.sprite import Sprite, load_spec

NAME = "geraldo_repinta"
FPS = 4
BASE = Path(__file__).resolve().parents[1] / "geraldo_ia_final_corpo.json"
HAT_ROWS = (8, 19)          # linhas do chapéu na base (copa + aba)
FACE = (39, 20, 60, 31)     # caixa do rosto (x0, y0, x1, y1)


SKIN_BOXES = ((38, 18, 61, 34), (26, 58, 40, 94), (58, 58, 74, 92))   # rosto+pescoço, braço/mão esq., dir.


def base_sprite() -> Sprite:
    """Base da IA com a pele parda da ficha (#c48a64) só nas regiões de pele."""
    from pixelforge.paint import PARDO, retone
    px = load_spec(BASE).frames[0].pixels
    mask = np.zeros(px.shape[:2], dtype=bool)
    for x0, y0, x1, y1 in SKIN_BOXES:
        mask[y0:y1 + 1, x0:x1 + 1] = True
    return Sprite(retone(px, mask, PARDO, hue=(20, 62), min_chroma=0.035))


def hat_mask(px: np.ndarray) -> np.ndarray:
    ys = np.arange(px.shape[0])[:, None]
    return (px[..., 3] > 0) & (ys >= HAT_ROWS[0]) & (ys <= HAT_ROWS[1])


def draw(hat: str = "cabeca", eyes: bool = True, mouth: bool = False) -> Paint:
    base = base_sprite()
    hat_px = np.where(hat_mask(base.pixels)[..., None], base.pixels, 0).astype(np.uint8)
    p = Paint.from_sprite(base)
    ys, xs = p.ys, p.xs
    P = p.poly
    from pixelforge.paint import PARDO
    p.custom_ramp("pardo", PARDO, 4, rim="#f4b07a", outline="#3a1c1c", rim2="#9a8ab0")
    SKIN_FAMS = sorted({p._r(name) for color, name in p._family.items()                # famílias da pele parda
                        if color in {tuple(parse_color(c)[:3]) for c in PARDO}})
    p.hue_ramp("cabelo", "#bdb8b2", 3, 1, hue=10, rim="#fff0dc", outline="#4a4650", rim2="#b8c0dc")
    p.custom_ramp("linha", ["#2a1414", "#3e2220"], 0, rim="#3e2220", outline="#1a0a0a")
    p.custom_ramp("cicatriz", ["#e4b49c", "#f6d6c4"], 0, rim="#fff4ea", outline="#3a1c1c")
    p.custom_ramp("brilho", ["#fff6ea"], 0, rim="#ffffff", outline="#3a1c1c")

    face = p.rect(*FACE) & (p.rid >= 0)
    if hat == "cabeca":
        # aba: borda de cima clara, faixa escura embaixo (já vem da base); sombra nos olhos
        brim_top = hat_mask(base.pixels) & ~p.moved(hat_mask(base.pixels), 0, 1) & (ys >= 15)
        p.shift(brim_top, 2)
        p.shift(face & (ys <= 25), -2)                                   # terço de cima do rosto na sombra
        p.shift(face & (ys >= 26) & (xs >= 52), -1)
        if eyes:
            p.pixels([(45, 23), (46, 23), (52, 23), (53, 23), (54, 23)], "linha", 0)   # traço dentro da sombra
        p.pixels([(49, 26), (50, 26), (49, 27)], "pardo", 2)              # ponto de pele na luz (ref 14)
    else:
        p.erase(hat_mask(base.pixels))
        # só o lugar do chapéu é repintado: testa (linhas 14–19) e cabelo branco rente (≤ 14);
        # o rosto da base fica intacto da linha 20 para baixo
        skull = p.ellipse(49.5, 21, 9.2, 10) & (ys <= 19)
        p.set(skull, "pardo", 0)
        p.set(skull & (xs >= 54), "pardo", -2)
        p.set(skull & (xs <= 43), "pardo", 1)
        hair = (p.ellipse(49.5, 20.5, 9.9, 10.4) & (ys <= 14)) |             (p.ellipse(49.5, 21, 10, 10.4) & (np.abs(xs - 49.5) >= 8.6) & (ys <= 21))   # calota + têmporas
        p.set(hair, "cabelo", 0)
        p.set(hair & (xs >= 54), "cabelo", -1)
        p.set(hair & (xs <= 45) & (ys <= 13), "cabelo", 1)
        p.texture(hair, -1, 0.35, seed=2, stroke=(1, 1))
        brim_shadow = face & (ys <= 21) & (p.tone <= 1) & np.isin(p.rid, SKIN_FAMS)    # sombra da aba some
        p.shift(brim_shadow, 2)
        if eyes:
            p.pixels([(45, 23), (46, 23), (52, 23), (53, 23)], "linha", 1)
    if mouth:
        p.pixels([(48, 28), (49, 28), (50, 28)], "linha", 0)

    # mãos grandes da base (~7×14 px, receita 5.2): dedos marcados por 1 px de sombra e nó claro (ref 1)
    hands = np.zeros((p.h, p.w), dtype=bool)
    for x0, y0, x1, y1 in ((29, 78, 37, 91), (61, 76, 70, 89)):
        box = p.rect(x0, y0, x1, y1) & np.isin(p.rid, SKIN_FAMS)
        hands |= box
        for k in (0, 1, 2):
            fx = x0 + 2 + 2 * k
            p.set(p.rect(fx, y1 - 5, fx, y1 - 1) & box, "pardo", -3)     # sombra entre os dedos
            p.set(p.rect(fx - 1, y1 - 6, fx - 1, y1 - 6) & box, "pardo", 2)  # nó do dedo
    p._hands = hands

    # cicatriz lisa e brilhante no antebraço esquerdo dele (direita de quem olha)
    p.set(P([(63, 64), (65, 63.5), (68.5, 71), (66.5, 72)]), "cicatriz", 0)
    p.set(P([(64, 64.5), (65, 64.5), (67.5, 70.5), (66.5, 71)]), "cicatriz", 1)
    p.px(65, 66, "brilho", 0, lock=True)
    p.px(66, 67, "brilho", 0, lock=True)

    # luz de borda pontual: quente do lado da luz (esquerda), fria do outro
    p.rim_spots([(66, 30, 80, 48), (64, 56, 80, 74), (58, 90, 70, 120)], second=True, dirs=((1, 0),))
    p.rim_spots([(36, 4, 52, 14), (26, 30, 42, 44), (22, 44, 34, 62), (26, 92, 34, 112), (24, 120, 40, 146)],
                width=2)                                                  # laranja do fim de tarde, por trás
    p._hat_px = hat_px
    return p


def render(hat: str = "cabeca", **kw) -> Sprite:
    p = draw(hat, **kw)
    out = p.render(outline=False).pixels.copy()
    if hat == "erguido":                                                  # chapéu erguido 6 px acima da cabeça
        src = np.roll(p._hat_px, -6, axis=0)
        m = src[..., 3] > 0
        out[m] = src[m]
    elif hat == "mao":                                                    # chapéu na mão, ao lado do corpo
        hp = p._hat_px[HAT_ROWS[0]:HAT_ROWS[1] + 1]
        cols = np.nonzero(hp[..., 3].any(axis=0))[0]
        hp = np.rot90(hp[:, cols.min():cols.max() + 1], k=1)              # aba vertical, copa para fora
        h, w = hp.shape[:2]
        y0, x0 = 80, 31 - w + 4                                           # aba presa atrás dos dedos
        dst = out[y0:y0 + h, max(x0, 0):x0 + w]
        src = hp[:, max(-x0, 0):]
        m = src[..., 3] > 0
        dst[m] = src[m]
        hand = p.render(outline=False).pixels
        out[p._hands] = hand[p._hands]                                    # dedos por cima do chapéu
    return Sprite(out)


def build():
    return [render("cabeca"), render("erguido"), render("mao")]
