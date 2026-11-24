"""Céu de Goiânia depois do temporal, fim de tarde de janeiro (cap 01): lavado,
indo do azul para o laranja, com nuvens desfiando cor-de-rosa. Parallax 0.1.
"""

import random

from pixelforge import Canvas

NAME = "ceu"
W, H = 720, 360
PALETTE = {
    "anil": "#2b3a67", "azul": "#3f5b98", "azul_claro": "#6f8cc4", "lavanda": "#a58fc0",
    "rosa": "#e59aa6", "salmao": "#f4a37a", "laranja": "#fbbf6a", "ouro": "#ffe19a",
    "nuvem": "#c77f9e", "nuvem_luz": "#ffc9a6", "nuvem_sombra": "#8a6aa0",
}


def cloud(c: Canvas, x: int, y: int, w: int, rnd: random.Random) -> None:
    for i in range(w // 6):
        cx = x + i * 6 + rnd.randint(-2, 2)
        r = rnd.randint(3, 6)
        c.ellipse(cx, y, r + 3, r * 0.6, "nuvem")
    for i in range(w // 6):
        cx = x + i * 6 + rnd.randint(-1, 1)
        c.line(cx - 3, y - 3, cx + 3, y - 3, "nuvem_luz")
    c.line(x, y + 3, x + w, y + 3, "nuvem_sombra")


def build() -> Canvas:
    rnd = random.Random(1)
    c = Canvas(W, H, palette=PALETTE)
    # o laranja precisa aparecer por cima das lajes (topo das casas em y = 150-170)
    c.gradient(0, 0, W, 50, ["anil", "azul"])
    c.gradient(0, 50, W, 50, ["azul", "azul_claro", "lavanda"])
    c.gradient(0, 100, W, 45, ["lavanda", "rosa", "salmao"])
    c.gradient(0, 145, W, 215, ["salmao", "laranja", "ouro"])
    for x, y, w in [(30, 70, 90), (180, 52, 140), (390, 88, 110), (560, 64, 120), (250, 118, 70), (640, 110, 60)]:
        cloud(c, x, y, w, rnd)
    for _ in range(18):                                   # fiapos longos
        x, y = rnd.randint(0, W), rnd.randint(100, 160)
        c.line(x, y, x + rnd.randint(20, 60), y, rnd.choice(["rosa", "nuvem_luz", "lavanda"]))
    return c
