"""Martim (12 anos, pequeno e magro) — sprite chibi de corpo, 64×64, de frente.

Render: python -m pixelforge render art/coletanea/veu/amostra-chibi/martim_sprite.py
~54 px de altura (2,3 cabeças); pé na linha 63.
"""

import numpy as np

from pixelforge.paint import Paint

NAME = "martim_sprite"
W, H = 64, 64
CX = 31.5


def ramps(p: Paint) -> None:
    p.custom_ramp("pele", ["#5e3527", "#7d4a35", "#9a6143", "#b47a52", "#cc966b", "#ddb085"], 3,
                  rim="#c9a48c", outline="#4a2820")
    p.custom_ramp("cabelo", ["#120c0f", "#1d1418", "#2a1d1a", "#3d2b25", "#57403a"], 2,
                  rim="#5c5a6e", outline="#0b0709")
    p.custom_ramp("linha", ["#140c0e", "#23161a", "#3a2826"], 1, outline="#0b0709")
    p.custom_ramp("iris", ["#170d0b", "#2e1c14", "#4a2e1d", "#6e4628"], 1)
    p.custom_ramp("branco", ["#9b98a6", "#c3c0c8", "#e2dfe0", "#f6f3ee"], 2, outline="#6c6878")
    p.ramp("moletom", "#8b93a1", down=3, up=2)
    p.ramp("calca", "#3a4466", down=2, up=2)
    p.custom_ramp("tenis", ["#8f887c", "#b5ae9f", "#d9d4c7", "#efebe2"], 2, outline="#5d574f")
    p.custom_ramp("sola", ["#a9a49a", "#d6d2c8", "#f4f1ea"], 1, outline="#5d574f")
    p.ramp("boca", "#8e4a42", down=2, up=1)
    p.custom_ramp("brilho", ["#ffffff"], 0)


def build():
    p = Paint(W, H)
    ramps(p)
    ys, xs = p.ys, p.xs
    dx = np.abs(xs - CX)

    # --- tênis claros com a sola colada (emenda visível) ---------------------------------
    for side in (-1, 1):
        sx = CX + side * 4.5
        shoe = p.ellipse(sx + side * 0.8, 60.5, 5.2, 3.2) & (ys <= 62)
        p.cel(shoe, "tenis", shadow=(2, 2), core=None, light=(2, 2))
        sole = p.rect(sx - 5 + side * 0.8, 62, sx + 5 + side * 0.8, 63) & p.ellipse(sx + side * 0.8, 61, 6, 3.5)
        p.cel(sole, "sola", shadow=(2, 0), core=None, light=None)
        p.line(sx - 4 + side * 0.8, 62, sx + 4 + side * 0.8, 62, "tenis", -2)   # emenda da cola
        p.px(int(sx + side * 3), 61, "tenis", -2)                                # sola descolando
        p.line(sx - 1.5, 59, sx + 1.5, 59, "tenis", -1)                          # cadarço
        p.px(int(round(sx)), 58, "tenis", 1)

    # --- calça escura -------------------------------------------------------------------------
    for side in (-1, 1):
        leg = p.poly([(CX + side * 1, 46), (CX + side * 7.5, 46), (CX + side * 7, 58), (CX + side * 1.5, 58)])
        p.cel(leg, "calca", shadow=(2, 0), core=None, light=(2, 0))
        p.line(CX + side * 2.5, 52, CX + side * 5.5, 53, "calca", -1)          # dobra no joelho
    p.set(p.rect(CX - 1, 46, CX + 1, 48), "calca", -1)                        # gancho

    # --- braço de trás (esquerda da tela fica na luz) e moletom -----------------------------
    hood = p.ellipse(CX, 34.5, 10.5, 3.6)
    p.cel(hood, "moletom", shadow=(2, 1), core=None, light=(1, 1))
    p.shift(hood, -1)
    torso = p.poly([(CX - 8, 34), (CX + 8, 34), (CX + 10, 46), (CX - 10, 46)]) | p.ellipse(CX, 37, 9.5, 4)
    p.cel(torso, "moletom", shadow=(4, 2), core=(2, 1), light=(3, 2), rim=True)
    hem = p.rect(CX - 10, 45, CX + 10, 47) & p.poly([(CX - 10, 44), (CX + 10, 44), (CX + 10, 48), (CX - 10, 48)])
    p.cel(hem, "moletom", shadow=(3, 0), core=None, light=None)
    p.shift(hem, -1)
    for x in range(int(CX - 9), int(CX + 10), 2):                               # ribana da barra
        p.px(x, 46, "moletom", -2)
    pocket = p.poly([(CX - 6, 40), (CX + 6, 40), (CX + 7.5, 45), (CX - 7.5, 45)])
    p.shift(pocket, -1)
    p.line(CX - 6, 40, CX + 6, 40, "moletom", -2)                             # boca do bolso canguru
    p.line(CX - 6, 40, CX - 7.5, 44, "moletom", 1)
    p.line(CX + 6, 40, CX + 7.5, 44, "moletom", -3)
    # gola: camiseta branca da escola aparecendo + cordão do capuz
    p.cel(p.ellipse(CX, 34, 4.2, 2.2) & (ys >= 34), "branco", shadow=(1, 1), core=None, light=None)
    for side in (-1, 1):
        p.line(CX + side * 2.5, 36, CX + side * 3, 40, "branco", -1 if side > 0 else 0)
        p.px(int(round(CX + side * 3)), 41, "branco", -2)

    # --- braços: mangas compridas, punho de ribana, mãos à mostra ---------------------------------
    for side in (-1, 1):
        sleeve = p.capsule(CX + side * 9, 36, CX + side * 11.5, 44, 2.6, 2.2)
        p.cel(sleeve, "moletom", shadow=(2, 1), core=None, light=(1, 1), rim=side > 0)
        p.separate(sleeve, "moletom", -1)
        cuff = p.ellipse(CX + side * 11.7, 45, 2.2, 1.2)
        p.set(cuff, "moletom", -1)
        hand = p.ellipse(CX + side * 11.8, 47.5, 2.1, 2.2)
        p.cel(hand, "pele", shadow=(1, 1), core=None, light=None)
        p.px(int(round(CX + side * 12.5)), 48, "pele", -2)                      # dedos
        p.px(int(round(CX + side * 11)), 49, "pele", -1)

    # --- pescoço e cabeça -------------------------------------------------------------------------
    neck = p.rect(CX - 3, 30, CX + 3, 34)
    p.cel(neck, "pele", shadow=(2, 0), core=None, light=None)
    p.shift(neck & (ys <= 33), -1)
    for side in (-1, 1):
        ear = p.ellipse(CX + side * 11.8, 23.5, 2.2, 3)
        p.cel(ear, "pele", shadow=(1, 1), core=None, light=None)
        p.px(int(round(CX + side * 12)), 23, "pele", -2)
    head = p.ellipse(CX, 20.5, 11.8, 11.5) | p.ellipse(CX, 26, 8.6, 7.4)
    p.cel(head, "pele", shadow=(3, 2), core=(1, 1), light=(3, 3))
    p.shift(p.ellipse(CX - 7, 26, 2, 1.5) & head, 1)

    # cabelo crespo na máquina
    cap = p.ellipse(CX, 20, 12.5, 12.4)
    line = np.where(dx < 6.5, 14.2, np.where(dx < 9.5, 14.8 + (dx - 6.5) * 0.6, 17.5 + (dx - 9.5) * 3))
    hair = cap & (ys < line) & ~((dx > 10.8) & (ys > 20))
    p.cel(hair, "cabelo", shadow=(2, 2), core=(1, 1), light=(3, 3))
    p.set(hair & ~p.moved(hair, -1, 0) & (ys < 19), "cabelo", 1)   # luz de borda só no lado direito
    rng = np.random.default_rng(3)
    for y in range(9, 21, 2):
        for x in range(19 + (y // 2) % 2, 45, 2):
            if hair[y, x] and rng.random() < 0.5:
                p.shift(p.rect(x, y, x, y), 1)
    p.shift(p.moved(hair, 0, 1) & ~hair & head, -1, "pele")

    # rosto: olhos grandes (4×5), sobrancelha grossa, boca pequena
    keys = {"k": ("linha", -1), "i": ("iris", 0), "d": ("iris", -1), "l": ("iris", 1), "w": ("branco", 0),
            "h": ("brilho", 0)}
    eye_rows = ["kkkk", "kdhd", "widi", "wiil", ".ll."]
    for side, x0 in ((-1, int(CX - 7.5)), (1, int(CX + 3.5))):
        p.glyph(x0, 20, eye_rows, keys, mirror=side > 0)
        p.px(x0 + (2 if side < 0 else 1), 21, "brilho", 0, lock=True)
        p.px(x0 + (4 if side > 0 else -1), 20, "linha", -1)                   # ponta do cílio
        p.line(x0, 17, x0 + 3, 17, "linha", 0)                                   # sobrancelha grossa
        p.line(x0 + (0 if side < 0 else 1), 18, x0 + (2 if side < 0 else 3), 18, "linha", 0)
    p.px(int(CX + 1), 26, "pele", -1)                                            # nariz
    p.line(CX - 1, 28, CX + 1, 28, "boca", -1)
    return p.render()
