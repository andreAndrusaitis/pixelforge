"""Seu Geraldo — busto de retrato para diálogo, 112×112, amostra v2.

3/4 para a esquerda, chapéu de feltro com a aba sombreando os olhos, rosto liso,
cabelo branco rente na têmpora, camisa de botão. Luz de borda laranja de trás/esquerda.
Render: python -m pixelforge render art/coletanea/veu/amostra-chibi/amostra-v2/geraldo_busto.py
"""

import numpy as np

from pixelforge.paint import Paint

NAME = "geraldo_busto"
S = 112

RAMPS = {
    "pele": (["#47292a", "#76493b", "#9c674d", "#bf8762", "#d29f78"], 2, "#f2aa74", "#2c1718"),
    "cabelo": (["#6a6672", "#98949e", "#c6c2c2", "#e4e0d8"], 2, "#ffe0c0", "#3e3a44"),
    "linha": (["#150d0e", "#26181a"], 0, "#26181a", "#0b0607"),
    "chapeu": (["#22160f", "#38281d", "#56402f", "#765a43"], 2, "#de8a52", "#120b08"),
    "fita": (["#120b09", "#1f150f", "#2e2018"], 1, "#5a3a26", "#0b0605"),
    "camisa": (["#3a3c4c", "#5a5f70", "#7b8293", "#9ea6b2"], 2, "#f0b88a", "#1e1f2a"),
    "botao": (["#e8e4dc"], 0, "#ffffff", "#2e3040"),
    "boca": (["#4f2827", "#6b3833", "#875048"], 1, "#875048", "#2c1718"),
}


def build():
    p = Paint(S, S)
    for name, (colors, base, rim, outline) in RAMPS.items():
        p.custom_ramp(name, colors, base, rim=rim, outline=outline)
    ys, xs = p.ys, p.xs
    P = p.poly

    # --- camisa de botão, ombros largos ------------------------------------------------------------
    body = P([(0, 111), (2, 96), (22, 86), (52, 83), (84, 86), (104, 95), (111, 104), (111, 111)])
    p.set(body, "camisa", 0)
    p.set(body & P([(66, 85), (84, 86), (104, 95), (111, 104), (111, 111), (74, 111), (72, 96)]), "camisa", -1)
    p.set(body & P([(2, 96), (22, 86), (28, 90), (12, 104), (2, 106)]), "camisa", 1)            # ombro na luz
    p.set(body & P([(30, 96), (40, 94), (42, 111), (30, 111)]), "camisa", -1)                   # prega
    p.set(body & P([(84, 98), (96, 101), (94, 111), (86, 111)]), "camisa", -2)
    pocket = P([(70, 98), (84, 98), (84, 111), (70, 111)])
    p.shift(pocket, -1)
    p.line(70, 98, 84, 98, "camisa", -2)
    p.line(51, 92, 49, 111, "camisa", -2)                                                         # carcela
    for y in (98, 106):
        p.pixels([(50, y), (51, y)], "botao", 0)
    p.texture(body, -1, 0.1, seed=6, stroke=(3, 1))

    # --- pescoço, gola, cabeça (3/4 para a esquerda) ----------------------------------------------
    neck = P([(42, 70), (70, 70), (71, 90), (41, 90)])
    p.set(neck, "pele", -1)
    p.set(neck & (xs <= 46), "pele", 0)
    p.set(neck & (ys <= 78), "pele", -2)                                                          # sombra do queixo
    for pts, t in (([(34, 86), (50, 90), (42, 99)], 1), ([(50, 90), (70, 83), (68, 96)], -1)):
        p.set(P(pts), "camisa", t)                                                                # pontas da gola
    head = p.ellipse(58, 50, 22, 24) | P([(37, 48), (79, 50), (77, 64), (70, 74), (60, 79),
                                          (48, 79), (40, 73), (36, 62)])
    p.set(head, "pele", 0)
    p.set(head & P([(64, 46), (80, 50), (77, 64), (70, 74), (64, 66)]), "pele", -1)            # lado de trás na sombra
    p.set(head & P([(40, 73), (60, 77), (58, 80), (46, 80)]), "pele", -1)                       # sob o queixo
    p.set(head & P([(38, 54), (46, 54), (46, 64), (39, 64)]), "pele", 1)                        # bochecha na luz
    nose = P([(38, 52), (30, 62), (37, 65)])
    p.set(nose, "pele", 0)
    p.set(P([(31, 61), (37, 62), (37, 65)]), "pele", -1)
    p.pixels([(33, 63), (34, 63)], "pele", -2)
    ear = p.ellipse(78, 57, 4.5, 7.5)
    p.set(ear, "pele", -1)
    p.set(P([(77, 53), (79, 54), (79, 61), (77, 62)]), "pele", -2)
    # cabelo branco rente na têmpora e na nuca
    sideburn = P([(70, 43), (75.5, 43), (74.5, 53), (72, 55), (71, 50)])                       # costeleta curta
    nape = P([(81, 44), (84, 47), (83.5, 64), (80, 66), (82, 56)])                              # atrás da orelha
    hair = (sideburn | nape) & ~p.ellipse(78, 57, 4.5, 7.5)
    p.set(hair, "cabelo", 0)
    p.set(hair & (xs >= 81), "cabelo", -1)
    p.texture(hair, -1, 0.35, seed=2, stroke=(1, 1))
    # rosto liso: sulcos leves, boca, olhos na sombra da aba
    p.set(P([(40, 68), (50, 67), (50, 68.5), (40, 69.5)]), "boca", 0)
    p.pixels([(42, 70), (43, 70), (44, 70)], "boca", 2)
    p.set(p.curve([(46, 60), (51, 66), (51, 70)], 0.5), "pele", -1)                              # sulco
    p.pixels([(39, 66), (52, 72)], "pele", -1)
    p.set(P([(43, 50), (47, 49.5), (47, 51), (43, 51.5)]), "linha", 0)                          # olhos (na sombra)
    p.set(P([(55, 50), (60, 49.5), (60, 51), (55, 51.5)]), "linha", 0)
    p.pixels([(44, 52), (45, 52), (56, 52), (57, 52), (58, 52)], "pele", -2)                    # bolsa sob os olhos
    p.pixels([(61, 49), (62, 50)], "pele", -2)                                                   # pé de galinha

    # --- chapéu de feltro: aba larga caída na frente, copa com vinco, fita -------------------------
    brim = P([(6, 44), (22, 36), (44, 33), (80, 33), (102, 37), (106, 41), (90, 44), (60, 45), (30, 46.5)])
    crown = P([(30, 37), (31, 20), (38, 10), (54, 7), (70, 9), (78, 18), (81, 36)])
    crown &= ~P([(46, 6), (60, 6), (54, 12)])                                                     # vinco (pinch)
    p.set(crown, "chapeu", 0)
    p.set(crown & P([(62, 8), (78, 18), (81, 36), (66, 36)]), "chapeu", -1)
    p.set(crown & P([(31, 22), (38, 11), (44, 10), (40, 30), (31, 34)]), "chapeu", 1)
    p.line(46, 9, 56, 15, "chapeu", -2)                                                            # vinco
    p.line(56, 15, 62, 10, "chapeu", -2)
    band = crown & (ys >= 28) & (ys <= 35)
    p.set(band, "fita", 0)
    p.set(band & (xs <= 38), "fita", 1)
    p.set(P([(34, 28), (39, 27), (39, 35), (34, 36)]), "fita", 2)                                  # laço
    p.set(brim, "chapeu", 0)
    p.set(brim & (ys >= 41), "chapeu", -1)
    p.set(brim & P([(70, 33), (102, 37), (106, 41), (90, 44), (70, 44)]), "chapeu", -1)
    p.set(brim & P([(6, 44), (22, 36), (32, 35), (16, 43)]), "chapeu", 1)
    p.texture(brim | crown, -1, 0.15, seed=9, stroke=(2, 1))
    shadow = (p.moved(brim, 0, 7) | p.moved(brim, 0, 4)) & ~brim & head                           # aba nos olhos
    p.shift(shadow, -1, "pele")
    p.shift(p.moved(brim, 0, 3) & ~brim & head, -1, "pele")

    p.rim_light(dirs=((1, 0),), width=1, second=True)                               # azul do céu do outro lado
    p.rim_light(dirs=((-1, 0), (0, -1)), width=2, reach=8)
    return p.render(outline="seletivo")
