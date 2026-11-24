"""Capim do primeiro plano (camada `frente`, parallax 1.3): silhuetas escuras
que balançam com o vento (2 frames). Emendável (repetir "x").

Render: python -m pixelforge render art/examples/cena-demo/frente.py
"""

from pixelforge import Canvas

NAME = "frente"
FPS = 3
W, H = 320, 26
PALETTE = {"capim": "#181425", "capim_luz": "#193c3e"}


def tufts(lean: int) -> Canvas:
    c = Canvas(W, H, palette=PALETTE)
    c.rect(0, H - 4, W, 4, "capim")
    x, i = 2, 0
    while x < W - 2:
        tall = 10 + (x * 11) % 13
        for blade in (-2, 0, 2):
            h = tall - abs(blade) * 2
            top_x = x + blade + lean * (1 + abs(blade) // 2)
            c.line(x + blade // 2, H - 4, top_x, H - 4 - h, "capim")
        c.px(x + lean, H - 4 - tall + 1, "capim_luz")
        x += 9 + (i * 5) % 11
        i += 1
    return c


def build():
    return [tufts(-1), tufts(1)]
