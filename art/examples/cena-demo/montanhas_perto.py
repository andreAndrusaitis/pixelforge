"""Cordilheira da frente, escura, com pinheiros na crista. Emendável
(repetir "x").

Render: python -m pixelforge render art/examples/cena-demo/montanhas_perto.py
"""

import math

from pixelforge import Canvas

NAME = "montanhas_perto"
W, H = 480, 180
PALETTE = {"corpo": "#262b44", "luz": "#3a4466", "pinho": "#181425"}
WAVES = [(3, 12, 2.2), (7, 5, 0.7), (13, 2, 1.3)]
STEPS = [7, 11, 5, 9, 13, 6, 8]


def ridge(x: int) -> int:
    return round(128 - sum(a * math.sin(2 * math.pi * k * x / W + p) for k, a, p in WAVES))


def build():
    c = Canvas(W, H, palette=PALETTE)
    tops = [ridge(x) for x in range(W)]
    for x, top in enumerate(tops):
        c.line(x, top, x, H - 1, "corpo")
        if tops[x - 1] > top:
            c.px(x, top, "luz")
    x, i = 3, 0
    while x < W - 3:                               # pinheiros com espaçamento fixo irregular
        h = 6 + (x * 7) % 5
        top = tops[x]
        c.polygon([(x, top - h), (x - 2, top + 1), (x + 2, top + 1)], "pinho")
        x += STEPS[i % len(STEPS)]
        i += 1
    return c
