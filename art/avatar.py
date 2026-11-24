"""Avatar ícone 64x64 (personagem a partir da foto em refs/foto.jpg).

Briefing: avatar ícone · 64x64 · cores da foto em 3 tons por material ·
cel shading + contorno · cenário simples (rua da foto) · idle (respiração).
Identidade medida em art/avatar_guia.json: cabelo ondulado com volume e franja
caindo à esquerda, rosto levemente virado (orelha direita visível), sorriso largo
com dentes, olhos claros verde-acinzentados, camiseta cinza-azulada gola redonda.

Render: python -m pixelforge render art/avatar.py --formats png,gif
"""

from pixelforge import Canvas

FPS = 4

PALETTE = {
    "k": "#241a16",  # contorno
    # cabelo (castanho; luz quente, sombra fria)
    "h0": "#2e221c", "h1": "#4a372d", "h2": "#6b4f40", "h3": "#957357",
    # pele
    "s1": "#b47f6c", "s2": "#dcae98", "s3": "#f0cdb9", "blush": "#de9a8e",
    # olhos
    "ew": "#f1ebe4", "iris": "#86a092", "irisd": "#5d7468", "pupil": "#241a16",
    # boca
    "m": "#5a2626", "m2": "#8a3b3e", "teeth": "#f6f0e6", "teeth2": "#d2c6b8", "lip": "#c4707a",
    # camiseta
    "c0": "#6d7c8c", "c1": "#9aaab9", "c2": "#c4d3e0",
    # cenário (dessaturado e claro, para o personagem se destacar)
    "sky": "#c9dbea", "cloud": "#eef4f8",
    "g0": "#55764a", "g1": "#71935a", "g2": "#9bb878",
    "trunk": "#6a5a4c", "wall": "#c2bd7c", "wall2": "#a9a468", "trim": "#e8e5d2",
    "post": "#e3bf3a", "post2": "#b8952a", "fence": "#c7bfae", "fence2": "#aaa18f",
    "road": "#9a9da2", "walk": "#b49a8c",
}


def background() -> Canvas:
    c = Canvas(64, palette=PALETTE).clear("sky")
    # nuvem
    c.ellipse(9, 9, 7, 3, "cloud").ellipse(15, 7, 5, 3, "cloud")
    # prédio verde-amarelado à direita, com friso claro
    c.rect(44, 16, 20, 30, "wall").rect(44, 38, 20, 8, "wall2").rect(44, 27, 20, 1, "trim")
    # árvore grande no alto à direita
    c.circle(53, 5, 10, "g1").circle(63, 13, 7, "g1").circle(41, 2, 6, "g1")
    with c.only("g1"):
        c.rect(0, 9, 64, 10, "g0")
    c.circle(49, 2, 4, "g2").circle(58, 4, 3, "g2")
    # árvore à esquerda
    c.rect(5, 20, 3, 26, "trunk")
    c.circle(7, 15, 8, "g1").circle(15, 11, 5, "g1")
    with c.only("g1"):
        c.rect(0, 18, 20, 6, "g0")
    c.circle(5, 11, 3, "g2").circle(14, 9, 2, "g2")
    # chão: rua e calçada
    c.polygon([(0, 42), (18, 40), (18, 63), (0, 63)], "road")
    c.polygon([(18, 40), (30, 40), (30, 63), (18, 63)], "walk")
    # cerca e poste amarelo (detalhes da foto)
    c.rect(46, 44, 18, 20, "fence")
    for x in range(48, 64, 4):
        c.line(x, 44, x, 63, "fence2")
    c.rect(56, 31, 4, 13, "post").rect(56, 31, 4, 1, "post2").rect(59, 32, 1, 12, "post2")
    return c


def character() -> Canvas:
    c = Canvas(64, palette=PALETTE)

    # --- camiseta e pescoço ---------------------------------------------
    c.polygon([(2, 63), (4, 58), (10, 53), (18, 50), (26, 48), (38, 48), (46, 50), (54, 53),
               (60, 58), (62, 63)], "c1")
    with c.only("c1"):
        c.polygon([(4, 58), (10, 53), (18, 50), (14, 56), (9, 63), (3, 63)], "c2")      # luz à esquerda
        c.polygon([(46, 50), (54, 53), (60, 58), (62, 63), (52, 63), (48, 56)], "c0")  # sombra à direita
    c.line(15, 57, 16, 63, "c0").line(49, 57, 48, 63, "c0")                            # dobras
    c.ellipse(32, 50, 9, 4.5, "c2")                                                     # gola
    with c.only("c2"):
        c.rect(38, 46, 10, 8, "c1")
    c.ellipse(32, 49.5, 7, 3.2, "s1")
    c.rect(26, 40, 13, 10, "s2")                                                        # pescoço
    with c.only("s2"):
        c.rect(34, 40, 5, 10, "s1")
    c.rect(26, 42, 13, 2, "s1")                                                         # sombra do queixo

    # --- orelhas --------------------------------------------------------
    c.ellipse(19.5, 29, 1.6, 3, "s2")
    c.ellipse(46, 29, 2.4, 3.8, "s2")
    c.px(46, 28, "s1").px(46, 29, "s1").px(46, 30, "s1")

    # --- rosto ----------------------------------------------------------
    c.ellipse(32, 27, 12.5, 15, "s2")
    c.polygon([(20, 30), (45, 30), (42, 38), (36, 44), (31, 45), (26, 43), (22, 38)], "s2")
    with c.only("s2"):
        c.polygon([(40, 12), (46, 12), (46, 34), (41, 41), (36, 44), (40, 34)], "s1")   # lado na sombra
        c.rect(21, 18, 3, 14, "s3")                                                       # lado da luz
        c.line(29, 44, 33, 44, "s1")
    c.line(20, 27, 20, 31, "s1").line(45, 27, 45, 31, "s1")                               # dobra orelha/rosto

    # --- cabelo: volume ondulado, franja caindo à esquerda --------------
    hair = [(19, 30), (17, 24), (16, 17), (17, 11), (19, 7), (22, 4), (25, 4), (27, 1), (30, 3),
            (33, 0), (36, 2), (39, 0), (42, 3), (45, 4), (47, 8), (49, 11), (50, 16), (49, 19),
            (50, 23), (48, 27), (47, 30), (45, 27),
            (44, 21), (42, 17), (38, 15), (34, 15), (30, 16), (27, 15), (24, 16), (22, 19),
            (21, 24), (21, 30)]
    c.polygon(hair, "h2")
    c.polygon([(22, 14), (28, 13), (30, 16), (27, 19), (24, 21), (22, 20)], "h2")       # mecha na testa
    with c.only("h2"):
        c.polygon([(42, 3), (45, 5), (48, 9), (50, 14), (50, 20), (49, 26), (47, 30), (45, 27),
                   (44, 20), (41, 14), (44, 9)], "h1")                                   # lado na sombra
        c.polygon([(17, 24), (19, 30), (21, 30), (21, 24), (19, 20)], "h1")
        c.polygon([(24, 16), (27, 15), (30, 16), (27, 19), (24, 21), (22, 20)], "h1")    # sombra sob a franja
        # ondas: separação entre mechas
        c.line(19, 13, 23, 9, "h1").line(23, 9, 27, 8, "h1")
        c.line(29, 11, 33, 8, "h1").line(33, 8, 38, 9, "h1")
        c.line(38, 9, 41, 12, "h1").line(26, 13, 30, 12, "h1")
    with c.only("h1"):
        c.line(48, 12, 49, 22, "h0").line(17, 18, 18, 25, "h0")
    # luzes nas ondas (topo à esquerda)
    c.line(20, 9, 23, 6, "h3").line(24, 5, 28, 4, "h3").line(29, 5, 32, 4, "h3")
    c.line(25, 10, 28, 9, "h3").line(34, 4, 37, 3, "h3").line(31, 10, 33, 9, "h3")
    c.line(19, 14, 21, 12, "h3")

    # sombra do cabelo na testa
    for x in range(20, 46):
        for y in range(10, 32):
            if c.get(x, y) in (c.color("h1"), c.color("h2"), c.color("h0")) and \
                    c.get(x, y + 1) in (c.color("s2"), c.color("s3")):
                c.px(x, y + 1, "s1")

    # --- sobrancelhas e olhos (claros, enfatizados) ---------------------
    c.line(23, 22, 28, 21, "h1").line(36, 21, 41, 22, "h1")
    for x0 in (24, 36):
        c.line(x0, 24, x0 + 4, 24, "k")                       # pálpebra / cílios
        c.px(x0 + 4, 23, "k") if x0 == 36 else c.px(x0, 23, "k")
        c.px(x0, 25, "ew").px(x0 + 1, 25, "iris").px(x0 + 2, 25, "pupil")
        c.px(x0 + 3, 25, "iris").px(x0 + 4, 25, "ew")
        c.px(x0 + 1, 26, "irisd").px(x0 + 2, 26, "irisd").px(x0 + 3, 26, "iris")   # íris com 2 linhas
        c.px(x0 + 1, 27, "s1").px(x0 + 2, 27, "s1").px(x0 + 3, 27, "s1")   # bochecha do sorriso
    c.px(26, 25, "ew").px(38, 25, "ew")                        # brilho na pupila (luz à esquerda)
    c.px(27, 25, "pupil").px(39, 25, "pupil")

    # --- nariz ----------------------------------------------------------
    c.line(33, 27, 33, 30, "s1")
    c.px(31, 29, "s3").px(31, 30, "s3")
    c.px(29, 31, "s1").px(30, 32, "m2").px(33, 32, "m2").px(34, 31, "s1")
    c.line(31, 32, 32, 32, "s1")

    # --- bochechas e linhas do sorriso -----------------------------------
    c.rect(22, 31, 2, 1, "blush").rect(41, 31, 2, 1, "blush")
    c.px(23, 33, "s1").px(42, 33, "s1")

    # --- sorriso largo com dentes ---------------------------------------
    c.px(24, 34, "m").px(40, 34, "m")
    c.line(25, 35, 39, 35, "m")
    c.line(26, 36, 38, 36, "teeth").px(25, 36, "m").px(39, 36, "m")
    c.line(27, 37, 37, 37, "teeth").px(26, 37, "m").px(38, 37, "m")
    c.line(36, 36, 38, 36, "teeth2").line(35, 37, 37, 37, "teeth2")      # dentes na sombra
    c.line(28, 38, 36, 38, "m2").px(27, 38, "m").px(37, 38, "m")
    c.line(29, 39, 35, 39, "lip")
    c.px(31, 40, "s1").px(32, 40, "s1").px(33, 40, "s1")

    c.outline("k")
    return c


def build():
    bg = background()
    char = character()
    frames = []
    # idle: respiração lenta — personagem sobe/desce 1px
    for dy in (0, 0, 1, 1):
        frame = bg.copy()
        frame.paste(char.copy().shift(0, dy))
        frames.append(frame)
    return frames
