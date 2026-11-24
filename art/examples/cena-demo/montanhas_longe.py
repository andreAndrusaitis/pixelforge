"""Cordilheira do fundo, azulada pela distância, com neve rosada nos picos.
Emendável (ondas com nº inteiro de ciclos): o cenário a usa com repetir "x".

Render: python -m pixelforge render art/examples/cena-demo/montanhas_longe.py
"""

import math

from pixelforge import Canvas

NAME = "montanhas_longe"
W, H = 480, 180
PALETTE = {"corpo": "#5a6988", "luz": "#8b9bb4", "neve": "#e8b796"}
WAVES = [(2, 16, 0.4), (3, 7, 2.5), (5, 7, 1.9), (11, 2.5, 0.2)]


def ridge(x: int) -> int:
    return round(92 - sum(a * math.sin(2 * math.pi * k * x / W + p) for k, a, p in WAVES))


def build():
    c = Canvas(W, H, palette=PALETTE)
    tops = [ridge(x) for x in range(W)]
    for x, top in enumerate(tops):
        c.line(x, top, x, H - 1, "corpo")
        if tops[(x + 3) % W] - tops[x - 3] < -1:   # encosta subindo: pega a luz do poente
            c.line(x, top, x, top + 3, "luz")
        if top < 80:
            c.line(x, top, x, top + (80 - top) // 3, "neve")
    return c
