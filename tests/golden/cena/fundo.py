"""Fundo da cena de referência (golden): céu em faixas, morros e chão, 320x90."""

from pixelforge import Canvas

NAME = "fundo"
W, H = 320, 90
PALETTE = {"ceu1": "#3a4466", "ceu2": "#5a6988", "morro": "#265c42", "chao": "#733e39",
           "pedra": "#b86f50", "casa": "#c0cbdc", "porta": "#181425"}


def build():
    c = Canvas(W, H, palette=PALETTE)
    c.rect(0, 0, W, 40, "ceu1").rect(0, 40, W, 30, "ceu2")
    for x in range(W):
        top = 52 + (x * 7 // 13) % 9 - (x // 40) % 3
        c.line(x, top, x, 69, "morro")
    c.rect(0, 70, W, 20, "chao")
    for x in range(3, W, 17):
        c.px(x, 74 + x % 11, "pedra")
    c.rect(250, 44, 40, 26, "casa").rect(266, 56, 8, 14, "porta")
    return c
