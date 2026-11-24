"""Retrato 64x64 (busto) a partir da foto de referência.

Proporções medidas na foto recortada; cores amostradas e estilizadas.
Luz vindo da esquerda/cima (como na foto). Render:
    python -m pixelforge render art/retrato.py
"""

from pixelforge import Canvas

PALETTE = {
    "k": "#2a1d1a",  # contorno
    # cabelo (castanho, rampa com leve deslocamento para quente nas luzes)
    "h0": "#33241c",
    "h1": "#4f3a2c",
    "h2": "#6f5440",
    "h3": "#987558",
    "h4": "#bf9b78",
    # pele
    "s0": "#9c6455",
    "s1": "#c98d78",
    "s2": "#e6b49c",
    "s3": "#f6d2bd",
    "blush": "#e39f90",
    # olhos
    "ew": "#f1ebe4",
    "iris": "#7f9488",
    "pupil": "#2a1d1a",
    "brow": "#6f5440",
    # boca
    "m": "#5e2627",
    "teeth": "#fbf5ea",
    "teeth2": "#d9cfc2",
    "lip": "#c4747a",
    # camiseta
    "t0": "#5f6c7a",
    "t1": "#7f8e9c",
    "t2": "#a6b4c1",
    "t3": "#c6d2dc",
}


def build():
    c = Canvas(64, palette=PALETTE)

    # --- camiseta e pescoço -------------------------------------------------
    c.polygon([(3, 63), (6, 55), (12, 51), (22, 48), (40, 48), (50, 51), (56, 55), (60, 63)], "t2")
    with c.only("t2"):
        c.rect(44, 48, 20, 16, "t1")                       # lado na sombra
        c.polygon([(50, 52), (56, 56), (60, 63), (53, 63)], "t0")
        c.polygon([(5, 58), (10, 53), (16, 51), (12, 56), (8, 63), (5, 63)], "t3")  # ombro iluminado
    c.line(14, 57, 15, 63, "t1")                           # dobras
    c.line(47, 56, 46, 63, "t0")
    c.ellipse(31, 48.5, 9, 4.5, "t3")                      # gola
    with c.only("t3"):
        c.rect(38, 44, 10, 10, "t2")
    c.ellipse(31, 48, 7, 3.2, "s1")                        # abertura do pescoço
    c.rect(26, 39, 11, 10, "s2")                           # pescoço
    with c.only("s2"):
        c.rect(33, 39, 4, 10, "s1")
    c.rect(26, 41, 11, 2, "s1")                            # sombra do queixo

    # --- orelhas -------------------------------------------------------------
    c.ellipse(18.5, 29, 2.2, 3.6, "s2")
    c.ellipse(44, 29, 2.2, 3.6, "s1")
    c.px(18, 28, "s1").px(18, 29, "s1").px(44, 28, "s0").px(44, 29, "s0")

    # --- rosto ---------------------------------------------------------------
    c.ellipse(31, 26, 12, 14, "s2")
    c.polygon([(20, 31), (42, 31), (38, 40), (33, 43), (29, 43), (24, 40)], "s2")
    with c.only("s2"):
        c.polygon([(39, 14), (44, 14), (44, 34), (40, 40), (36, 42), (39, 34)], "s1")  # lado direito
        c.rect(21, 20, 2, 11, "s3")                                                   # lado da luz
        c.line(29, 42, 33, 42, "s1")
    c.line(19, 26, 19, 30, "s1").line(43, 26, 43, 30, "s0")                           # dobra orelha/rosto

    # --- cabelo --------------------------------------------------------------
    # laterais terminam acima das orelhas; volume ondulado em cima, mais cheio à esquerda
    hair = [(19, 23), (17, 19), (15, 14), (16, 10), (19, 6), (23, 4), (27, 2), (31, 3), (34, 1),
            (38, 2), (42, 4), (45, 8), (47, 13), (46, 19), (45, 23), (43, 23), (43, 19), (41, 17),
            (37, 16), (33, 15), (29, 16), (26, 19), (24, 21), (22, 22), (21, 24)]
    c.polygon(hair, "h2")
    c.polygon([(23, 14), (27, 13), (28, 17), (26, 20), (24, 21)], "h2")   # mecha caindo na testa
    c.rect(43, 22, 1, 3, "h1").rect(20, 22, 1, 3, "h1")                  # costeletas
    with c.only("h2"):
        c.polygon([(42, 4), (45, 8), (47, 13), (46, 19), (45, 23), (43, 23), (43, 19), (41, 15)], "h1")
        c.polygon([(15, 14), (17, 19), (19, 23), (21, 24), (22, 22), (19, 18), (17, 13)], "h1")
        c.line(25, 15, 31, 12, "h1")                                         # separação das mechas
        c.line(31, 12, 38, 13, "h1")
        c.line(20, 12, 25, 9, "h1")
        c.line(33, 7, 40, 8, "h1")
    with c.only("h1"):
        c.line(45, 12, 46, 19, "h0")
        c.line(16, 15, 18, 20, "h0")
    # luzes (ondas)
    c.line(19, 9, 23, 6, "h3").line(24, 5, 28, 4, "h4")
    c.line(30, 4, 33, 3, "h3").line(35, 4, 38, 4, "h3")
    c.line(26, 9, 30, 8, "h3").line(31, 8, 34, 8, "h4")
    c.line(20, 13, 22, 11, "h3").line(35, 11, 38, 11, "h3")
    c.px(25, 17, "h3").px(26, 16, "h3")

    # sombra do cabelo na testa
    for x in range(20, 44):
        for y in range(10, 30):
            if c.get(x, y) in (c.color("h1"), c.color("h2"), c.color("h0")) and c.get(x, y + 1) in (
                c.color("s2"), c.color("s3")
            ):
                c.px(x, y + 1, "s1")

    # --- sobrancelhas e olhos ---------------------------------------------
    c.line(22, 23, 27, 22, "brow").line(34, 22, 39, 23, "brow")
    for x0 in (23, 34):
        c.line(x0, 25, x0 + 4, 25, "k")                    # pálpebra
        c.px(x0, 26, "ew").px(x0 + 1, 26, "iris").px(x0 + 2, 26, "pupil")
        c.px(x0 + 3, 26, "iris").px(x0 + 4, 26, "ew")
        c.px(x0 + 1, 27, "s1").px(x0 + 2, 27, "s1").px(x0 + 3, 27, "s1")  # bochecha empurrando (sorriso)
    c.px(25, 25, "k").px(36, 25, "k")

    # --- nariz -------------------------------------------------------------
    c.line(32, 27, 32, 31, "s1")
    c.px(30, 30, "s3").px(30, 31, "s3")
    c.px(28, 32, "s1").px(29, 33, "s0").px(32, 33, "s0").px(33, 32, "s1")
    c.line(30, 33, 31, 33, "s1")

    # --- bochechas e linhas do sorriso ------------------------------------
    c.rect(21, 31, 2, 1, "blush").rect(40, 31, 2, 1, "blush")
    c.px(24, 33, "s1").px(23, 34, "s1").px(38, 33, "s1").px(39, 34, "s1")

    # --- boca (sorriso aberto com dentes) ---------------------------------
    c.px(24, 34, "m").px(38, 34, "m")
    c.line(25, 35, 37, 35, "m")
    c.line(26, 36, 36, 36, "teeth").px(25, 36, "m").px(37, 36, "m")
    c.line(27, 37, 35, 37, "teeth").px(26, 37, "m").px(36, 37, "m")
    c.px(27, 37, "teeth2").px(35, 37, "teeth2").px(26, 36, "teeth2").px(36, 36, "teeth2")
    c.line(28, 38, 34, 38, "m")
    c.line(29, 39, 33, 39, "lip")
    c.px(30, 40, "s1").px(31, 40, "s1").px(32, 40, "s1")

    c.outline("k")
    return c
