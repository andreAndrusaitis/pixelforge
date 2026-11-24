"""Seu Geraldo (64 anos) — retrato chibi detalhado, 112×112. Amostra-alvo do estilo.

Render: python -m pixelforge render art/coletanea/veu/amostra-chibi/geraldo_retrato.py
Quadros: 0 = de chapéu, sorriso contido; 1 = sem chapéu (cabelo branco rente).
"""

import numpy as np

from pixelforge.paint import Paint

NAME = "geraldo_retrato"
FPS = 1
S = 112
CX = 55.5


def ramps(p: Paint) -> None:
    p.custom_ramp("pele", ["#6b3f2c", "#8a5440", "#a86f52", "#c48a64", "#d6a57e", "#e4bf98"], 3,
                  rim="#d8b49a", outline="#55301f")
    p.custom_ramp("cabelo", ["#8e8a93", "#b4b0b5", "#d2cfcc", "#e6e3dc", "#f6f4ee"], 3, outline="#6f6a72")
    p.custom_ramp("linha", ["#24170f", "#3d2a24", "#5a4038"], 1, outline="#1a100d")
    p.custom_ramp("iris", ["#170d0b", "#2e1c14", "#4a2e1d", "#6e4628", "#97663a"], 1)
    p.custom_ramp("branco", ["#9b98a6", "#c3c0c8", "#e2dfe0", "#f6f3ee"], 2, outline="#6c6878")
    p.ramp("chapeu", "#6b4e37", down=3, up=2)
    p.custom_ramp("fita", ["#1f1512", "#33241d", "#4a362a"], 1)
    p.ramp("camisa", "#c9d3dc", down=3, up=1)
    p.ramp("boca", "#8e4a42", down=2, up=1)
    p.custom_ramp("brilho", ["#ffffff"], 0)


def eye(p: Paint, ex: float, ey: float, side: int) -> None:
    """Olho de adulto: pálpebra pesada, íris em 4 tons, brilho duplo, pés de galinha."""
    opening = p.ellipse(ex, ey, 6.4, 5.6) & (p.ys >= ey - 3.5)
    p.set(opening, "branco", 0)
    p.set(opening & (p.ys <= ey - 2), "branco", -1)
    ix, iy = ex - 0.6 * side, ey + 0.6
    iris = p.ellipse(ix, iy, 4.2, 4.8) & opening
    p.set(iris, "iris", 1)
    p.set(iris & (p.ys <= ey - 1), "iris", -1)
    p.set(iris & (p.ys >= ey + 2), "iris", 2)
    p.set(iris & (p.ys >= ey + 4), "iris", 3)
    p.shift(iris & ~p.ellipse(ix, iy, 3.2, 3.8), -1, "iris")
    p.set(p.ellipse(ix, iy, 1.7, 2.2) & opening, "linha", -1)
    p.glyph(int(round(ix - 2.4)), int(round(ey - 2)), ["hh", "hh"], {"h": ("brilho", 0)}, lock=True)
    p.px(int(round(ix + 2)), int(round(ey + 2)), "brilho", 0, lock=True)
    # pálpebra superior pesada caindo para fora
    p.set(p.curve([(ex - 7, ey + 0.5), (ex - 2, ey - 4.6), (ex + 3, ey - 4.4), (ex + 7, ey + 1)], 1.1), "linha", -1)
    p.set(p.curve([(ex - 6 * side, ey - 6.4), (ex, ey - 7.4), (ex + 6.5 * side, ey - 5)], 0.9), "pele", -1)
    p.set(p.curve([(ex - 5 * side, ey - 5.2), (ex + 4 * side, ey - 5)], 0.5), "pele", -2)
    # bolsa embaixo do olho e pés de galinha
    p.set(p.curve([(ex - 4, ey + 6.5), (ex, ey + 7.4), (ex + 4, ey + 6.5)], 0.5), "pele", -1)
    for k in (-1, 1):
        p.line(ex + side * 8.5, ey + k * 0.5, ex + side * 10.5, ey + k * 2.5, "pele", -1)


def build():
    return [draw(True), draw(False)]


def draw(with_hat: bool):
    p = Paint(S, S)
    ramps(p)
    ys, xs = p.ys, p.xs
    dx = np.abs(xs - CX)

    # --- camisa: ombros largos, gola, carcela, bolso ---------------------------------------------
    body = p.ellipse(CX, 136, 66, 46) & (ys >= 90)
    p.cel(body, "camisa", shadow=(8, 4), core=(3, 2), light=(6, 4), rim=True)
    for a, b in (((18, 98), (26, 111)), ((94, 98), (86, 111)), ((40, 104), (44, 111))):
        p.set(p.curve([a, ((a[0] + b[0]) / 2 + 1, (a[1] + b[1]) / 2), b], 0.5), "camisa", -1 if a[0] < CX else -2)
    pocket = p.rect(CX - 26, 100, CX - 13, 111)
    p.shift(pocket & ~p.moved(pocket, -1, -1), -1)
    p.set(p.rect(CX - 26, 99, CX - 13, 101), "camisa", 0)
    p.line(CX - 26, 101, CX - 13, 101, "camisa", -2)
    neck = p.rect(CX - 13, 78, CX + 13, 98) & p.ellipse(CX, 90, 15, 20)
    p.cel(neck, "pele", shadow=(5, 0), core=None, light=None)
    p.shift(neck & (ys <= 87), -1)
    p.set(p.curve([(CX - 4, 95), (CX, 101), (CX + 4, 95)], 0.6), "pele", -1)            # primeiro botão aberto
    for side in (-1, 1):   # gola de ponta
        collar = p.poly([(CX + side * 2, 99), (CX + side * 15, 89), (CX + side * 18, 92), (CX + side * 11, 104)])
        p.cel(collar, "camisa", shadow=(2, 1), core=None, light=(2, 1))
        p.separate(collar, "camisa", -1)
    p.line(CX + 0.5, 101, CX + 0.5, 111, "camisa", -2)                                   # carcela
    for y in (104, 110):
        p.pixels([(int(CX + 1), y), (int(CX + 2), y)], "branco", 1)

    # --- orelhas e cabeça -------------------------------------------------------------------------
    for side in (-1, 1):
        ear = p.ellipse(CX + side * 29, 58, 5, 7.6)
        p.cel(ear, "pele", shadow=(2, 1) if side < 0 else (3, 2), core=None, light=(2, 2))
        p.set(p.curve([(CX + side * 30, 54), (CX + side * 31.4, 58), (CX + side * 29.6, 63)], 0.6), "pele", -2)
    head = p.ellipse(CX, 49, 29.5, 31) | p.ellipse(CX, 63, 24.5, 19.5)
    p.cel(head, "pele", shadow=(7, 4), core=(2, 2), light=(5, 6))
    p.shift(p.ellipse(CX - 14, 66, 5, 3) & head, 1)                                     # maçã do rosto
    p.shift(p.ellipse(CX + 6, 82, 15, 2.5) & head, -1)                                  # sob o queixo

    # cabelo branco rente (só nas têmporas quando de chapéu)
    cap = p.ellipse(CX, 47, 31, 32.5)
    hair = cap & (ys < np.where(dx < 18, 28, 28 + (dx - 18) * 2.6)) & ~((dx > 27.5) & (ys > 51))
    if with_hat:
        hair &= ys >= 34
    p.cel(hair, "cabelo", shadow=(4, 3), core=None, light=(4, 4))
    rng = np.random.default_rng(5)
    for y in range(14, 54, 2):
        for x in range(22 + (y // 2) % 2, 92, 2):
            if hair[y, x] and rng.random() < 0.45:
                p.shift(p.rect(x, y, x, y), -1)
    p.shift(p.moved(hair, 0, 1) & ~hair & head, -1, "pele")

    # rosto liso, bem barbeado
    EY = 58
    eye(p, CX - 13, EY, -1)
    eye(p, CX + 13, EY, 1)
    for side in (-1, 1):   # sobrancelhas brancas, grossas
        bx = CX + side * 13
        brow = p.curve([(bx - side * 7, 48.5), (bx, 46.6), (bx + side * 7.5, 48.6)], 1.5, 1.1)
        p.cel(brow, "cabelo", shadow=(1, 1), core=None, light=None)
        p.set(brow & ~p.moved(brow, 0, -1), "cabelo", -2)
    # nariz largo, narinas
    p.set(p.curve([(CX + 3, 60), (CX + 4, 66), (CX + 2, 68)], 0.55), "pele", -1)
    p.set(p.ellipse(CX, 67, 4.5, 2) & head, "pele", 0)
    p.pixels([(int(CX - 1), 65), (int(CX), 65)], "pele", 2)
    p.pixels([(int(CX - 3), 68), (int(CX + 3), 68), (int(CX + 4), 68)], "pele", -2)
    # sulcos e sorriso contido
    for side in (-1, 1):
        p.set(p.curve([(CX + side * 6, 66), (CX + side * 9, 71), (CX + side * 8.5, 75)], 0.5), "pele", -1)
    p.set(p.curve([(CX - 6.5, 73), (CX, 75), (CX + 6.5, 73)], 0.6), "boca", -1)
    p.set(p.curve([(CX - 3, 77), (CX + 3, 77)], 0.5), "pele", -1)
    p.pixels([(int(CX - 7), 72), (int(CX + 7), 72)], "pele", -2)

    if with_hat:   # chapéu de feltro marrom, aba larga, vinco no topo
        brim = p.ellipse(CX, 35, 50, 7.5)
        p.cel(brim, "chapeu", shadow=(6, 2), core=(2, 1), light=(4, 2), rim=True)
        p.shift(brim & (ys >= 37), -1)
        p.set(brim & ~p.moved(brim, 0, 1) & (ys <= 31), "chapeu", 1)
        crown = (p.ellipse(CX, 22, 27, 16) & (ys <= 34)) | p.rect(CX - 26, 20, CX + 26, 33)
        crown &= ~p.ellipse(CX, 3, 12, 6)
        p.cel(crown, "chapeu", shadow=(7, 3), core=(3, 1), light=(5, 4), rim=True)
        p.set(p.curve([(CX - 9, 10), (CX, 15), (CX + 9, 10)], 0.7), "chapeu", -2)       # vinco
        p.set(p.curve([(CX - 9, 11), (CX, 16), (CX + 9, 11)], 0.5), "chapeu", 1)
        band = crown & (ys >= 26) & (ys <= 32)
        p.cel(band, "fita", shadow=(6, 0), core=None, light=(4, 0))
        p.cel(p.ellipse(CX - 18, 29, 3, 3.5), "fita", shadow=(1, 1), core=None, light=None)   # laço
        # textura de feltro e sombra da aba no rosto
        for y in range(8, 42, 2):
            for x in range(8 + (y // 2) % 2, 104, 3):
                if (crown | brim)[y, x] and rng.random() < 0.3:
                    p.shift(p.rect(x, y, x, y), -1, "chapeu")
        p.shift(p.moved(brim, 0, 3) & ~brim & head, -1, "pele")
        p.shift(p.moved(brim, 0, 2) & ~brim & head, -1, "pele")
    return p.render()
