"""Primeiro plano (frente, parallax 1): o portão verde da avó, de tinta
descascando, com corrente e cadeado, desenhado por cima de quem está atrás dele.
"""

import random

from pixelforge import Canvas

NAME = "portao"
W, H = 1280, 360
BASE = 282
PALETTE = {
    "verde": "#2f8a57", "verde_luz": "#5fbf7d", "verde_escuro": "#1f5a43", "lasca": "#b9b3a6",
    "ferrugem": "#9a5a3a", "corrente": "#9aa0ad", "corrente_s": "#5d6270",
    "cadeado": "#d8b04a", "cadeado_s": "#9a7a2e",
    "cinza": "#6e7380", "cinza_luz": "#9aa0ad",
}


def build() -> Canvas:
    rnd = random.Random(3)
    c = Canvas(W, H, palette=PALETTE)
    x0, x1, top = 1022, 1086, BASE - 66
    c.rect(x0, top, x1 - x0, 4, "verde")                          # travessas
    c.rect(x0, top + 30, x1 - x0, 3, "verde")
    c.rect(x0, BASE - 5, x1 - x0, 4, "verde")
    c.line(x0, top, x1 - 1, top, "verde_luz")
    for gx in range(x0 + 2, x1, 6):                               # barras
        c.rect(gx, top, 2, BASE - top - 1, "verde")
        c.px(gx, top - 1, "verde_luz")
        c.line(gx + 1, top + 4, gx + 1, BASE - 6, "verde_escuro")
        for _ in range(4):                                        # tinta descascando
            c.px(gx + rnd.randint(0, 1), rnd.randint(top + 2, BASE - 4), rnd.choice(["lasca", "ferrugem"]))
    c.line(x0 + 32, top, x0 + 32, BASE - 1, "verde_escuro")       # as duas folhas
    for i in range(10):                                           # corrente no meio
        cx, cy = x0 + 24 + i * 2, top + 26 + (i % 2) + abs(i - 5) // 2
        c.rect(cx, cy, 2, 2, "corrente" if i % 2 else "corrente_s")
    c.rect(x0 + 29, top + 31, 7, 6, "cadeado")
    c.rect(x0 + 34, top + 31, 2, 6, "cadeado_s")
    c.line(x0 + 30, top + 29, x0 + 34, top + 29, "corrente")
    c.px(x0 + 32, top + 34, "cadeado_s")
    # grade cinza da casa da frente, por cima do Bolacha (mesma posição da rua.py)
    for gx in range(779, 823, 5):
        c.line(gx, BASE - 56, gx, BASE - 1, "cinza")
        c.px(gx, BASE - 57, "cinza_luz")
    c.rect(778, BASE - 59, 44, 3, "cinza_luz")
    c.rect(778, BASE - 30, 44, 2, "cinza")
    return c
