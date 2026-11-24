"""Céu de crepúsculo (camada do fundo, parallax 0.1): rampa com dithering,
lua, nuvens e estrelas que piscam (2 frames).

Render: python -m pixelforge render art/examples/cena-demo/ceu.py
"""

import random

from pixelforge import Canvas

NAME = "ceu"
FPS = 2
W, H = 360, 240

PALETTE = {
    "noite": "#181425",
    "anil": "#262b44",
    "azul": "#3a4466",
    "roxo": "#68386c",
    "magenta": "#b55088",
    "rosa": "#f6757a",
    "laranja": "#feae34",
    "estrela": "#ffffff",
    "estrela_fraca": "#8b9bb4",
    "lua": "#ead4aa",
    "lua_sombra": "#e4a672",
    "nuvem": "#68386c",
    "nuvem_luz": "#f6757a",
}


def sky() -> Canvas:
    c = Canvas(W, H, palette=PALETTE)
    # o brilho do poente fica logo acima da crista das montanhas (y ≈ 80–110)
    c.gradient(0, 0, W, 70, ["noite", "anil", "azul"])
    c.gradient(0, 70, W, 45, ["azul", "roxo", "magenta", "rosa"])
    c.gradient(0, 115, W, 125, ["rosa", "laranja"])

    # lua com sombra crescente (luz vinda do sol já posto, à direita/baixo)
    c.circle(262, 46, 11, "lua")
    with c.only("lua"):
        c.circle(257, 42, 10, "lua_sombra")
        c.circle(259, 44, 9.5, "lua")
    c.px(258, 41, "lua_sombra").px(264, 50, "lua_sombra").px(261, 52, "lua_sombra")

    # nuvens finas na faixa rosa: elipses achatadas com borda de luz embaixo
    for x, y, w in ((40, 88, 46), (150, 99, 60), (300, 84, 40), (225, 104, 54)):
        c.ellipse(x, y, w / 2, 3, "nuvem")
        c.ellipse(x + 6, y - 2, w / 3, 2.5, "nuvem")
        c.line(x - w // 2 + 4, y + 3, x + w // 2 - 4, y + 3, "nuvem_luz")
    return c


def stars(c: Canvas, twinkle: bool) -> Canvas:
    rng = random.Random(7)  # semente fixa: o céu é sempre o mesmo
    for i in range(70):
        x, y = rng.randrange(W), rng.randrange(90)
        if c.get(x, y) not in (c.color("noite"), c.color("anil")):
            continue
        bright = rng.random() < 0.3
        dim = twinkle and i % 3 == 0
        c.px(x, y, "estrela_fraca" if dim or not bright else "estrela")
        if bright and not dim and y < 90:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c.px(x + dx, y + dy, "estrela_fraca")
    return c


def build():
    base = sky()
    return [stars(base.copy(), False), stars(base.copy(), True)]
