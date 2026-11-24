"""Lajes ao longe (parallax 0.35): telhados e lajes do bairro em silhueta contra o
poente, cada uma com sua caixa d'água, antena e varal esquecido. Emendável em x.
"""

import random

from pixelforge import Canvas

NAME = "lajes"
W, H = 640, 160
PALETTE = {
    "sil": "#5a4a73", "sil_escura": "#46385e", "sil_luz": "#7c6493",
    "caixa": "#6f86b8", "caixa_luz": "#9fb4dd", "fio": "#3b2f52",
    "roupa1": "#d77a8f", "roupa2": "#e7c46b", "roupa3": "#86b6c9", "janela": "#ffcf7a",
}


def build() -> Canvas:
    rnd = random.Random(7)
    c = Canvas(W, H, palette=PALETTE)
    x = 0
    while x < W:
        w = rnd.randint(34, 70)
        top = rnd.randint(40, 95)
        c.rect(x, top, w, H - top, "sil")
        c.line(x, top, x + w - 1, top, "sil_luz")
        c.rect(x + w - 4, top, 4, H - top, "sil_escura")
        kind = rnd.random()
        if kind < 0.35:                                   # telhado de duas águas
            c.polygon([(x - 2, top), (x + w // 2, top - 14), (x + w + 1, top)], "sil_escura")
            c.line(x - 2, top, x + w // 2, top - 14, "sil_luz")
        if rnd.random() < 0.8:                            # caixa d'água
            cx = x + rnd.randint(6, max(7, w - 16))
            c.rect(cx, top - 11, 12, 11, "caixa")
            c.rect(cx - 1, top - 13, 14, 3, "caixa_luz")
            c.line(cx + 2, top - 9, cx + 2, top - 2, "caixa_luz")
        if rnd.random() < 0.5:                            # antena
            ax = x + rnd.randint(4, w - 4)
            c.line(ax, top - 22, ax, top, "fio")
            c.line(ax - 5, top - 18, ax + 5, top - 18, "fio")
        if rnd.random() < 0.55:                           # varal com roupa
            vx = x + 3
            c.line(vx, top - 7, vx + w - 8, top - 6, "fio")
            for i in range(rnd.randint(2, 4)):
                px = vx + 4 + i * 8
                c.rect(px, top - 6, 4, rnd.randint(4, 7), rnd.choice(["roupa1", "roupa2", "roupa3"]))
        for _ in range(rnd.randint(0, 2)):                # janela já acesa
            wx, wy = x + rnd.randint(4, w - 8), rnd.randint(top + 8, H - 12)
            c.rect(wx, wy, 3, 4, "janela")
        x += w + rnd.randint(-4, 2)
    return c
