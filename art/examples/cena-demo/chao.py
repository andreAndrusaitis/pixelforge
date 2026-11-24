"""Chão do vale (camada principal, parallax 1): campo, trilha, pinheiros,
cerca e uma cabana com janela acesa no fim da trilha. 640 px de largura:
o dobro da tela, para a câmera passear.

Render: python -m pixelforge render art/examples/cena-demo/chao.py
"""

import math

from pixelforge import Canvas

NAME = "chao"
W, H = 640, 180
PALETTE = {
    "grama_luz": "#3e8948",
    "grama": "#265c42",
    "grama_escura": "#193c3e",
    "terra": "#733e39",
    "terra_escura": "#3e2731",
    "sombra": "#181425",
    "madeira": "#b86f50",
    "madeira_escura": "#733e39",
    "telhado": "#3e2731",
    "telhado_luz": "#68386c",
    "janela": "#feae34",
    "janela_luz": "#fee761",
    "pedra": "#5a6988",
    "pedra_luz": "#8b9bb4",
}


def ground_top(x: int) -> int:
    return round(144 - 4 * math.sin(x / 70) - 2 * math.sin(x / 23 + 1))


def pine(c: Canvas, x: int, base: int, h: int) -> None:
    c.rect(x - 1, base - 6, 3, 7, "sombra")
    for i in range(4):                             # 4 andares de galhos
        top = base - h + i * h // 5
        w = 4 + i * 3
        c.polygon([(x, top), (x - w, top + h // 3), (x + w, top + h // 3)], "grama_escura")
        c.line(x + 1, top + 1, x + w - 1, top + h // 3 - 1, "sombra")   # lado na sombra


def cabin(c: Canvas, x: int, base: int) -> None:
    c.rect(x, base - 26, 44, 26, "madeira")
    for y in range(base - 24, base, 4):            # tábuas
        c.line(x, y, x + 43, y, "madeira_escura")
    c.rect(x + 34, base - 26, 10, 26, "madeira_escura")      # parede na sombra
    c.polygon([(x - 6, base - 25), (x + 22, base - 46), (x + 50, base - 25)], "telhado")
    c.line(x - 6, base - 25, x + 22, base - 46, "telhado_luz")
    c.rect(x + 30, base - 50, 5, 12, "telhado")              # chaminé
    c.rect(x + 6, base - 18, 9, 18, "terra_escura")          # porta
    c.px(x + 13, base - 9, "janela")
    c.rect(x + 21, base - 19, 9, 8, "janela")                # janela acesa
    c.rect(x + 22, base - 18, 3, 3, "janela_luz")
    c.line(x + 25, base - 19, x + 25, base - 12, "madeira_escura")
    c.line(x + 21, base - 15, x + 29, base - 15, "madeira_escura")


def build():
    c = Canvas(W, H, palette=PALETTE)
    tops = [ground_top(x) for x in range(W)]
    for x, top in enumerate(tops):
        c.line(x, top, x, H - 1, "grama")
        c.px(x, top, "grama_luz")
        if x % 3 == 0 and tops[x - 1] >= top:
            c.px(x, top - 1, "grama_luz")
    c.gradient(0, 160, W, 20, ["grama", "grama_escura"])

    # trilha sinuosa até a cabana
    for x in range(0, 468):
        cy = 166 - x * 14 // 468 + round(3 * math.sin(x / 40))
        half = 7 - x * 4 // 468
        c.line(x, cy - half // 2, x, cy + half // 2, "terra")
        c.px(x, cy + half // 2 + 1, "terra_escura")

    # pedras e tufos
    for x, y in ((60, 172), (205, 158), (330, 170), (395, 152), (590, 166)):
        c.ellipse(x, y, 4, 2.5, "pedra")
        c.line(x - 2, y - 2, x + 1, y - 2, "pedra_luz")
    for x in range(5, W, 17):
        y = tops[x] + 6 + (x * 13) % 9
        c.line(x, y, x - 1, y - 2, "grama_luz").line(x + 1, y, x + 2, y - 2, "grama_luz")

    for x, h in ((34, 48), (118, 62), (250, 44), (300, 56), (560, 66), (612, 50)):
        pine(c, x, tops[x] + 2, h)

    cabin(c, 450, tops[472])

    # cerca ao longo da trilha
    for x in range(330, 440, 12):
        base = tops[x] + 3
        c.rect(x, base - 9, 2, 10, "madeira_escura")
    for x0 in range(330, 428, 12):
        c.line(x0, tops[x0] - 3, x0 + 12, tops[x0 + 12] - 3, "madeira")
    return c
