"""Martim (12 anos) — retrato chibi detalhado, 112×112. Amostra-alvo do estilo.

Render: python -m pixelforge render art/coletanea/veu/amostra-chibi/martim_retrato.py
Quadros: 0 = neutro, 1 = rindo (covinha de um lado só).
"""

import numpy as np

from pixelforge.paint import Paint

NAME = "martim_retrato"
FPS = 1
S = 112
CX = 55.5


def ramps(p: Paint) -> None:
    p.custom_ramp("pele", ["#5e3527", "#7d4a35", "#9a6143", "#b47a52", "#cc966b", "#ddb085"], 3,
                  rim="#c9a48c", outline="#4a2820")
    p.custom_ramp("cabelo", ["#120c0f", "#1d1418", "#2a1d1a", "#3d2b25", "#57403a"], 2,
                  rim="#5c5a6e", outline="#0b0709")
    p.custom_ramp("linha", ["#140c0e", "#23161a", "#3a2826"], 1, outline="#0b0709")
    p.custom_ramp("iris", ["#170d0b", "#2e1c14", "#4a2e1d", "#6e4628", "#97663a"], 1)
    p.custom_ramp("branco", ["#9b98a6", "#c3c0c8", "#e2dfe0", "#f6f3ee"], 2, outline="#6c6878")
    p.ramp("moletom", "#8b93a1", down=3, up=2)
    p.ramp("cordao", "#e7e9ec", down=3, up=1)
    p.ramp("boca", "#8e4a42", down=2, up=2)
    p.custom_ramp("brilho", ["#ffffff"], 0)
    p.custom_ramp("rubor", ["#b5614f"], 0)


def eye(p: Paint, ex: float, ey: float, side: int, happy: bool) -> None:
    """Olho grande: esclera, íris em 4 tons, pupila, brilho duplo, cílio grosso e pálpebra.
    `side` aponta para o canto externo (-1 = esquerda da tela)."""
    if happy:
        # olho fechado de riso: arco grosso, ponta do cílio para fora
        p.set(p.curve([(ex - 6.5, ey + 2), (ex, ey - 4.5), (ex + 6.5, ey + 2)], 1.2), "linha", -1)
        p.px(int(round(ex + 7.5 * side)), int(ey + 1), "linha", -1)
        p.set(p.curve([(ex - 5, ey + 5.5), (ex + 5, ey + 5.5)], 0.5), "pele", 1)  # bochecha subindo
        return
    opening = p.ellipse(ex, ey, 6.6, 7.6) & (p.ys >= ey - 6)
    p.set(opening, "branco", 0)
    p.set(opening & (p.ys <= ey - 4), "branco", -1)
    ix, iy = ex - 0.8 * side, ey + 0.8
    iris = p.ellipse(ix, iy, 5.0, 6.6) & opening
    p.set(iris, "iris", 1)
    p.set(iris & (p.ys <= ey - 3), "iris", -1)
    p.set(iris & (p.ys > ey - 3) & (p.ys <= ey - 1), "iris", 0)
    p.set(iris & (p.ys >= ey + 3), "iris", 2)
    p.set(iris & (p.ys >= ey + 5), "iris", 3)
    p.shift(iris & ~p.ellipse(ix, iy, 4.0, 5.6), -1, "iris")        # anel escuro da íris
    p.set(p.ellipse(ix, iy - 0.3, 2.0, 3.0) & opening, "linha", -1)  # pupila
    hx, hy = int(round(ix - 2.6)), int(round(ey - 3))
    p.glyph(hx, hy, ["hh.", "hhh", "hh."], {"h": ("brilho", 0)}, lock=True)   # brilho grande
    p.glyph(int(round(ix + 2)), int(round(ey + 3)), ["h", "h"], {"h": ("brilho", 0)}, lock=True)
    # cílio superior grosso (2–3 px) com ponta para fora
    p.set(p.curve([(ex - 7, ey - 1), (ex - 3, ey - 7.2), (ex + 3, ey - 7.2), (ex + 7, ey - 1)], 1.3), "linha", -1)
    p.set(p.curve([(ex + 6 * side, ey - 3), (ex + 8.5 * side, ey - 5)], 0.6), "linha", -1)
    # dobra da pálpebra e cílio de baixo (só no canto externo)
    p.set(p.curve([(ex - 4.5, ey - 9.5), (ex + 1, ey - 10.4), (ex + 5, ey - 9.2)], 0.5), "pele", -1)
    p.set(p.curve([(ex + 2.5 * side, ey + 7.2), (ex + 6 * side, ey + 5)], 0.5), "linha", 0)
    p.set(p.curve([(ex - 3 * side, ey + 8), (ex + 2 * side, ey + 8)], 0.5), "pele", -1)


def build():
    return [draw(False), draw(True)]


def draw(happy: bool):
    p = Paint(S, S)
    ramps(p)
    ys, xs = p.ys, p.xs
    dx = np.abs(xs - CX)

    # --- capuz amontoado atrás do pescoço e corpo do moletom -------------------------------------
    U = -6  # tudo do moletom sobe 6 px (pescoço curto, cabeça grande)
    hood = p.ellipse(CX, 92 + U, 35, 13) & (ys <= 100 + U)
    p.cel(hood, "moletom", shadow=(5, 3), core=(2, 2), light=(3, 3))
    p.shift(hood, -1)
    p.set(p.curve([(CX - 31, 89 + U), (CX - 18, 83 + U), (CX - 2, 82 + U)], 0.6), "moletom", 0)  # dobras do capuz
    p.set(p.curve([(CX + 31, 89 + U), (CX + 18, 83 + U), (CX + 4, 82 + U)], 0.6), "moletom", -2)
    p.set(p.curve([(CX - 26, 93 + U), (CX - 16, 88 + U)], 0.5), "moletom", -2)
    body = (p.ellipse(CX, 130 + U, 57, 41) | p.ellipse(CX, 116 + U, 42, 24)) & (ys >= 92 + U)
    p.cel(body, "moletom", shadow=(7, 4), core=(3, 2), light=(5, 5), rim=True)
    for a, b in (((25, 93), (35, 111)), ((13, 101), (19, 111)), ((86, 93), (76, 111)), ((98, 101), (92, 111))):
        p.set(p.curve([a, ((a[0] + b[0]) / 2 + 1.5, (a[1] + b[1]) / 2), b], 0.5), "moletom", -1 if a[0] < CX else -2)

    # --- pescoço, camiseta, gola do moletom e cordão ---------------------------------------------
    neck = p.rect(CX - 9.5, 72, CX + 9.5, 98 + U) & p.ellipse(CX, 82, 11, 20)
    p.cel(neck, "pele", shadow=(4, 0), core=None, light=None)
    p.shift(neck & (ys <= 80), -1)                       # sombra do queixo
    shirt = p.ellipse(CX, 100 + U, 13, 9) & (ys >= 92 + U)
    p.cel(shirt, "branco", shadow=(3, 2), core=None, light=None)
    collar = p.ellipse(CX, 92.5 + U, 12, 6.5) & ~p.ellipse(CX, 91 + U, 9.5, 5) & (ys >= 92 + U)
    p.cel(collar, "branco", shadow=(2, 1), core=None, light=None)
    p.shift(p.ellipse(CX, 91 + U, 9.5, 5) & neck & (ys >= 93 + U), -1)
    neckline = p.ellipse(CX, 95 + U, 18, 9) & ~p.ellipse(CX, 94 + U, 14, 7.5) & (ys >= 92 + U)
    p.cel(neckline, "moletom", shadow=(3, 2), core=None, light=(2, 2))
    p.separate(neckline, "branco", -1)
    for side in (-1, 1):
        x0 = CX + side * 7.5
        p.set(p.curve([(x0, 101 + U), (x0 + side * 1.5, 106), (x0 + side * 0.5, 110)], 0.75),
              "cordao", 0 if side < 0 else -1)
        p.px(int(round(x0)), 109 + (side > 0), "cordao", -2)  # ponteira do cordão
        p.px(int(round(x0)), 100 + U, "moletom", -3)          # ilhós
        p.px(int(round(x0)) + (1 if side > 0 else -1), 100 + U, "moletom", -2)

    # --- orelhas e cabeça ---------------------------------------------------------------------------
    for side in (-1, 1):
        ear = p.ellipse(CX + side * 29.5, 55, 4.8, 7.2)
        p.cel(ear, "pele", shadow=(2, 1) if side < 0 else (3, 2), core=None, light=(2, 2))
        p.set(p.curve([(CX + side * 30.5, 51), (CX + side * 31.6, 55), (CX + side * 30, 59.5)], 0.6), "pele", -2)
        p.set(p.curve([(CX + side * 29, 53.5), (CX + side * 29.3, 57)], 0.5), "pele", -1)
    head = p.ellipse(CX, 45, 30, 31) | p.ellipse(CX, 59, 22.5, 19.4)
    p.cel(head, "pele", shadow=(6, 4), core=(2, 2), light=(5, 6))
    p.shift(p.ellipse(CX + 6, 77, 12, 3) & head, -1)      # sombra embaixo do queixo
    # luz: testa, maçã do rosto esquerda, ponta do queixo
    p.shift(p.ellipse(CX - 12, 37, 9, 4) & head, 1)
    p.shift(p.ellipse(CX - 18, 60, 4, 3) & head, 1)
    p.shift(p.ellipse(CX - 2, 75, 3, 1.2) & head, 1)
    for side in (-1, 1):                                  # rubor: três tracinhos diagonais
        for k in range(3):
            x = int(CX + side * 17) - 3 + k * 3
            p.pixels([(x + 1, 62), (x, 63)], "rubor", 0)

    # --- cabelo crespo, cortado na máquina --------------------------------------------------------
    cap = p.ellipse(CX, 44, 31.5, 33)
    line = np.where(dx < 16, 29.5 + (dx / 16) ** 2 * 1.2,
                    np.where(dx < 23.5, 30.7 + (dx - 16) * 0.9, 37.5 + (dx - 23.5) * 5))
    hair = cap & (ys < line) & ~((dx > 27.5) & (ys > 47))
    p.cel(hair, "cabelo", shadow=(5, 4), core=(2, 2), light=(5, 6), rim=True)
    band = p.crescent(cap, 4, 7) & ~p.crescent(cap, 2, 3) & hair     # faixa de brilho
    p.shift(band, 1)
    rng = np.random.default_rng(12)
    for y in range(9, 50, 2):
        for x in range(22 + (y // 2) % 2 * 2, 92, 3):
            jx, jy = x + int(rng.integers(0, 2)), y
            if not (hair[jy, jx] and hair[jy, min(jx + 1, S - 1)]):
                continue
            if band[jy, jx]:                                # cachinho claro na faixa de luz
                p.shift(p.rect(jx, jy, jx + 1, jy), 1)
            elif rng.random() < 0.6:
                p.shift(p.rect(jx, jy, jx, jy), 1)
                if hair[jy + 1, jx + 1]:
                    p.shift(p.rect(jx + 1, jy + 1, jx + 1, jy + 1), -1)
    p.set(hair & ~p.moved(hair, 0, -1) & (dx < 23), "cabelo", -1)     # linha do corte, nítida
    p.shift(p.moved(hair, 0, 1) & ~hair & head, -1, "pele")           # sombra da franja curta

    # --- rosto --------------------------------------------------------------------------------------
    EY = 51
    eye(p, CX - 13.5, EY, -1, happy)
    eye(p, CX + 13.5, EY, 1, happy)
    for side in (-1, 1):                                  # sobrancelhas grossas
        bx = CX + side * 13.5
        lift = -1.5 if happy else 0
        brow = p.curve([(bx - side * 7.5, 39 + lift), (bx - side * 1, 37 + lift), (bx + side * 7, 38.8 + lift)], 1.7, 1.2)
        p.set(brow, "linha", 0)
        p.set(brow & ~p.moved(brow, 0, 1), "linha", 1)
    # nariz: sombra do lado direito, luz na ponta
    p.set(p.curve([(CX + 2.5, 56), (CX + 3, 61), (CX + 1.5, 63)], 0.55), "pele", -1)
    p.pixels([(int(CX - 1), 61), (int(CX), 61)], "pele", 2)
    p.pixels([(int(CX + 1), 64), (int(CX + 2), 64)], "pele", -2)
    if happy:
        mouth = p.ellipse(CX, 68.5, 7, 4) & (ys >= 68)
        p.set(mouth, "boca", -2)
        p.set(p.rect(CX - 5, 68, CX + 5, 69) & mouth, "branco", 1)
        p.set(p.ellipse(CX + 0.5, 72, 3.2, 1.6) & mouth, "boca", 1)
        p.set(p.curve([(CX - 8, 67.2), (CX, 68.2), (CX + 8, 67)], 0.6), "boca", -1)
        # covinha só de um lado (esquerda da tela)
        p.set(p.curve([(CX - 10.5, 66), (CX - 11, 68.5), (CX - 10.2, 70.5)], 0.5), "pele", -2)
    else:
        p.set(p.curve([(CX - 4.5, 69), (CX, 69.6), (CX + 4.5, 68.6)], 0.55), "boca", -1)
        p.pixels([(int(CX - 1), 71), (int(CX), 71), (int(CX + 1), 71)], "pele", -1)
    return p.render()
