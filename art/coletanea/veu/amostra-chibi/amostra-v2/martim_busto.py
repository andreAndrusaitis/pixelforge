"""Martim — busto de retrato para diálogo, 112×112, amostra v2.

3/4 para a direita, rosto discreto (sem olho de anime): a expressão vem da
sobrancelha grossa, da boca e da cabeça um pouco baixa. Luz de borda laranja
de trás/esquerda; frente na sombra fria.
Render: python -m pixelforge render art/coletanea/veu/amostra-chibi/amostra-v2/martim_busto.py
"""

import numpy as np

from pixelforge.paint import Paint

NAME = "martim_busto"
S = 112

RAMPS = {
    "pele": (["#3c2427", "#6a4236", "#8e5c43", "#ad7650", "#c48d63"], 2, "#ee9e5e", "#2a1619"),
    "cabelo": (["#110c11", "#1d151a", "#2c2125", "#45342f"], 2, "#b0693f", "#09060a"),
    "linha": (["#160d11", "#241519", "#3a2622"], 0, "#241519", "#09060a"),
    "moletom": (["#2b2b3b", "#43465a", "#5f6375", "#7f8292"], 2, "#dc9c6c", "#1a1a26"),
    "cordao": (["#8a8a98", "#c4c2c4", "#e2ddd6"], 1, "#ffd0a0", "#4a4a58"),
    "branco": (["#8c8a96", "#bdbac0", "#dedad4"], 1, "#ffe0c0", "#4a4a58"),
    "boca": (["#4a2526", "#6a3532", "#8a4a42"], 1, "#8a4a42", "#2a1619"),
}


def build():
    p = Paint(S, S)
    for name, (colors, base, rim, outline) in RAMPS.items():
        p.custom_ramp(name, colors, base, rim=rim, outline=outline)
    ys, xs = p.ys, p.xs
    P = p.poly

    # --- moletom: ombros caídos, capuz amontoado, cordão -----------------------------------------
    body = P([(4, 111), (10, 92), (28, 80), (60, 77), (84, 83), (100, 96), (107, 111)])
    p.set(body, "moletom", 0)
    p.set(body & P([(64, 79), (84, 83), (100, 96), (107, 111), (72, 111), (76, 94)]), "moletom", -1)
    p.set(body & P([(10, 92), (28, 80), (34, 84), (20, 100), (8, 104)]), "moletom", 1)          # ombro na luz
    p.set(body & P([(24, 100), (34, 96), (38, 111), (26, 111)]), "moletom", -1)                 # dobra do peito
    p.set(body & P([(78, 98), (90, 102), (86, 111), (80, 111)]), "moletom", -2)
    hood = P([(14, 84), (24, 68), (40, 63), (50, 70), (44, 82), (30, 90)])
    p.set(hood, "moletom", 0)
    p.set(hood & P([(26, 72), (42, 66), (46, 74), (36, 82)]), "moletom", -2)                   # dentro do capuz
    p.set(hood & P([(14, 84), (22, 70), (26, 74), (18, 84)]), "moletom", 1)
    collar = P([(46, 78), (64, 74), (74, 79), (66, 86), (52, 86)])
    p.set(collar, "moletom", -1)
    p.set(P([(50, 79), (64, 77), (66, 80), (52, 82)]), "branco", 0)                             # camiseta da escola
    p.line(56, 86, 55, 106, "cordao", 0)
    p.line(66, 85, 68, 102, "cordao", -1)
    p.set(p.rect(54, 106, 56, 109), "cordao", -1)
    p.set(p.rect(67, 102, 69, 105), "cordao", -1)
    p.pixels([(56, 85), (66, 84)], "moletom", -2)                                               # ilhós
    p.texture(body | hood, -1, 0.1, seed=3, stroke=(3, 1))

    # --- pescoço e cabeça ------------------------------------------------------------------------
    neck = P([(46, 62), (62, 64), (63, 80), (47, 80)])
    p.set(neck, "pele", -1)
    p.set(neck & (xs <= 50), "pele", 0)
    head = p.ellipse(52, 40, 21, 23) | P([(34, 44), (72, 40), (74.5, 52), (69, 63), (61, 70),
                                          (53, 71), (44, 66), (37, 58)])
    p.set(head, "pele", 0)
    p.set(head & P([(62, 44), (74, 41), (75, 52), (69, 63), (62, 69), (64, 56)]), "pele", -1)   # frente na sombra fria
    p.set(head & P([(44, 63), (60, 68), (54, 71.5), (44, 67)]), "pele", -1)                     # sob o queixo
    p.set(head & P([(38, 46), (46, 46), (46, 58), (40, 58)]), "pele", 1)                         # maçã na luz
    nose = P([(71, 45), (77, 55), (71.5, 57.5)])
    p.set(nose, "pele", 0)
    p.set(P([(72, 53), (77, 55), (72, 57.5)]), "pele", -1)
    p.pixels([(73, 56), (74, 56)], "pele", -2)
    ear = p.ellipse(36.5, 49, 4.5, 7)
    p.set(ear, "pele", 0)
    p.set(P([(36, 45), (38, 46), (38, 53), (36, 54)]), "pele", -2)
    # cabelo crespo na máquina, em blocos de 3 tons
    cap = p.ellipse(52, 38.5, 22.5, 23.5)
    hair = cap & (ys < 29 + np.clip(66 - xs, 0, None) * 0.52) & ~p.ellipse(36.5, 49, 6, 8.5)
    p.set(hair, "cabelo", 0)
    p.set(hair & P([(38, 18), (58, 15), (66, 22), (52, 26), (38, 28)]), "cabelo", 1)          # topo na luz
    p.set(hair & P([(28, 34), (38, 30), (42, 46), (30, 50)]), "cabelo", -1)                    # nuca
    rng = np.random.default_rng(11)
    for y in range(16, 50, 3):
        for x in range(28 + (y % 2) * 2, 72, 4):
            if hair[y, x] and hair[y, x + 1]:
                d = 1 if rng.random() < 0.45 else -1
                p.shift(p.rect(x, y, x + 1, y + 1) & hair, d)                                    # cachinhos em bloco
    p.line(64, 30, 70, 31, "cabelo", -1)                                                         # linha do corte
    # rosto discreto
    p.set(P([(57, 40), (68, 37.5), (69.5, 40.5), (58, 43.5)]), "linha", 1)                      # sobrancelha grossa
    p.set(P([(57, 41.5), (68, 39), (69, 40.5), (58, 43.5)]), "linha", 0)
    p.set(P([(43, 42.5), (52, 41.5), (52.5, 44), (44, 45)]), "linha", 1)
    p.set(P([(60, 47), (65, 46), (65, 48), (60, 48.5)]), "linha", 0)                             # olho perto
    p.pixels([(66, 46), (59, 48)], "pele", -2)
    p.set(P([(46, 48), (50, 47.5), (50, 49), (46, 49.5)]), "linha", 0)                           # olho longe
    p.set(P([(59, 50), (65, 49.5), (65, 50.5), (59, 51)]), "pele", -1)                           # pálpebra de baixo
    p.set(P([(62, 62), (68, 61), (68, 62.5), (62, 63.2)]), "boca", 0)                             # boca fechada
    p.pixels([(64, 64), (65, 64)], "boca", 1)
    p.pixels([(61, 61)], "pele", -2)

    p.rim_light(dirs=((1, 0),), width=1, second=True)                               # azul do céu do outro lado
    p.rim_light(dirs=((-1, 0), (0, -1)), width=2, reach=8)
    return p.render(outline="seletivo")
