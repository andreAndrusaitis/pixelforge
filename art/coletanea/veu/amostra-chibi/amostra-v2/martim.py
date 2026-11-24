"""Martim (12 anos, pequeno e magro) — corpo inteiro, amostra v2 (~96 px, 5,5 cabeças).

Fim de tarde depois da chuva: luz laranja de trás/esquerda (luz de borda quente),
frente na sombra fria. Mãos no bolso canguru, peso na perna de trás, joelho solto.
Render: python -m pixelforge render art/coletanea/veu/amostra-chibi/amostra-v2/martim.py

Marcos (y): topo 6 · queixo 23 · ombro 26 · cotovelo 41 · barra do moletom 57 ·
joelho 76 · tornozelo 93 · chão 101.
"""

import numpy as np

from pixelforge.paint import Paint

NAME = "martim_v2"
W, H = 64, 104

# rampas: escuro (violeta) → sombra fria → base → luz; `rim` = luz de borda laranja
RAMPS = {
    "pele": (["#3c2427", "#6a4236", "#8e5c43", "#ad7650"], 2, "#e89a5c", "#2a1619"),
    "cabelo": (["#110c11", "#1d151a", "#2c2125", "#45342f"], 2, "#a8653f", "#09060a"),
    "linha": (["#170e12", "#241519"], 0, "#241519", "#09060a"),
    "moletom": (["#2b2b3b", "#43465a", "#5f6375", "#7f8292"], 2, "#d99a6c", "#1a1a26"),
    "cordao": (["#8a8a98", "#c4c2c4", "#e2ddd6"], 1, "#ffd0a0", "#4a4a58"),
    "calca": (["#14151f", "#1e2132", "#2b3149", "#3c4563"], 2, "#a86a50", "#0b0b12"),
    "tenis": (["#5a5866", "#8e8a8c", "#bdb6aa", "#d9d1c0"], 2, "#f6c08a", "#34323c"),
    "sola": (["#7c7a80", "#b4b0a8", "#e0dbd0"], 1, "#ffd8a8", "#34323c"),
    "boca": (["#4a2526", "#6a3532"], 1, "#6a3532", "#2a1619"),
}


def setup(p: Paint) -> None:
    for name, (colors, base, rim, outline) in RAMPS.items():
        p.custom_ramp(name, colors, base, rim=rim, outline=outline)


def build():
    p = Paint(W, H)
    setup(p)
    ys, xs = p.ys, p.xs
    P = p.poly

    # --- calça larga (como o 21): a de trás reta (peso), a da frente com o joelho solto;
    #     tecido sobrando amontoa em dobras grandes no tornozelo ---------------------------------
    far_leg = P([(22.5, 57), (31.5, 57), (31, 74), (31.5, 86), (30.5, 93), (23, 93), (22.5, 86), (23.5, 74)])
    p.set(far_leg, "calca", -1)
    p.set(far_leg & (xs <= 25), "calca", 0)
    for pts, t in (([(23, 63), (28, 61), (27, 66), (23, 68)], 0), ([(26, 70), (31, 68), (30, 73)], -2),
                   ([(22.5, 84), (29, 82), (31.5, 86), (24, 87)], 0), ([(23, 88), (31, 87.5), (30.5, 90), (23, 90.5)], -2)):
        p.set(far_leg & P(pts), "calca", t)
    near_leg = P([(30.5, 57), (39, 57), (41.5, 66), (42, 76), (41.5, 86), (40, 93), (32.5, 93), (33, 86),
                  (34.5, 77), (32.5, 68)])
    p.set(near_leg, "calca", 0)
    p.set(near_leg & P([(36.5, 57), (39, 57), (41.5, 66), (42, 76), (41.5, 86), (39, 82), (39, 70)]), "calca", -1)
    p.set(near_leg & P([(32.5, 64), (37, 65), (36, 72), (33.5, 71)]), "calca", 1)          # joelho na luz
    for pts, t in (([(34, 74), (41, 72), (40, 76), (35, 77)], -2),                         # dobra atrás do joelho
                   ([(33.5, 80), (39, 78), (38, 81)], -1),
                   ([(33, 84), (41.5, 82), (41.5, 86), (34, 87)], 1),                       # sobra na barra
                   ([(33, 88), (40.5, 87.5), (40, 90.5), (33, 90.5)], -2)):
        p.set(near_leg & P(pts), "calca", t)
    p.set(near_leg & P([(30.5, 58), (33, 58), (33, 68), (31, 62)]), "calca", -2)           # entreperna

    # --- tênis claros, sola colada (emenda irregular) ----------------------------------------------
    for pts, x0, x1 in (([(23, 91), (30, 91), (33, 95.5), (33.5, 99), (22, 99), (22, 94)], 22, 33),
                        ([(33, 91), (39, 91), (42.5, 95.5), (43.5, 99), (33, 99)], 33, 43)):
        shoe = P(pts)
        p.set(shoe, "tenis", 0)
        p.set(shoe & (ys <= 93), "tenis", 1)
        p.set(shoe & (xs >= x1 - 3) & (ys >= 96), "tenis", -1)
        p.set(p.rect(x0, 100, x1, 101), "sola", 0)
        p.line(x0, 99, x1, 99, "sola", -1)                                         # emenda da cola
        p.pixels([(x0 + 2, 100), (x1 - 2, 99), (x1 - 1, 99)], "tenis", -2)          # cola falhando
        p.line(x0 + 3, 93, x0 + 6, 93, "tenis", -2)                                # cadarço

    # --- braço de trás (atrás do tronco), moletom, braço da frente -----------------------------
    far_arm = P([(20.5, 28), (25, 27), (26, 38), (28.5, 44), (25, 47), (19.5, 42)])
    p.set(far_arm, "moletom", 0)
    p.set(far_arm & (xs <= 21.5), "moletom", 1)
    torso = P([(21.5, 27), (28, 25), (36, 25), (42, 28), (43.5, 38), (43.5, 57), (21, 58), (20.5, 41)])
    p.set(torso, "moletom", 0)
    p.set(torso & P([(36, 26), (42, 28), (43.5, 38), (43.5, 57), (38, 57), (39, 40)]), "moletom", -1)
    p.set(torso & P([(21.5, 27), (26, 26), (25, 38), (21, 41)]), "moletom", 1)          # costas na luz
    p.shift(torso & (ys >= 54), -1)
    for x in range(21, 44, 2):
        p.px(x, 56, "moletom", -2)                                                    # ribana da barra
    pocket = P([(26, 42), (40, 41.5), (42.5, 52), (25, 53)])
    p.set(pocket, "moletom", 0)
    p.set(pocket & (xs >= 37), "moletom", -1)
    p.line(26, 42, 40, 41.5, "moletom", -2)                                            # boca do bolso
    p.set(pocket & P([(26, 44), (33, 43), (30, 48)]), "moletom", 1)                    # mão dentro do bolso
    p.line(27, 52, 41, 51.5, "moletom", -1)
    near_arm = P([(36, 26), (41.5, 28), (45, 40), (42, 47), (35, 46.5), (39, 40.5), (38, 32)])
    p.set(near_arm, "moletom", -1)
    p.set(near_arm & P([(36, 26), (40, 27.5), (40.5, 36), (38, 32)]), "moletom", 0)
    p.set(near_arm & P([(39, 40.5), (45, 40), (42, 47), (38.5, 45)]), "moletom", -2)   # dobra no cotovelo
    p.line(40, 37, 43, 36, "moletom", -2)
    p.line(36, 45, 41, 45, "moletom", -2)                                              # punho entrando no bolso
    # capuz amontoado nas costas + gola
    hood = P([(21, 27), (25, 22.5), (30, 22), (32, 25.5), (29, 30), (23, 31)])
    p.set(hood, "moletom", 0)
    p.set(hood & P([(25, 24), (31, 23.5), (30.5, 28), (27, 29)]), "moletom", -2)       # dentro do capuz
    p.set(hood & P([(21, 27), (24.5, 23), (25.5, 26), (22, 30)]), "moletom", 1)
    collar = P([(30.5, 24), (37, 24), (38.5, 27), (32, 28)])
    p.set(collar, "moletom", -1)
    p.line(31, 28, 30.5, 36, "cordao", 0)                                              # cordão
    p.line(34, 28, 35, 35, "cordao", -1)
    p.pixels([(30, 37), (35, 36)], "cordao", -1)
    # dobras grandes do moletom largo (formas, não linhas)
    p.set(torso & P([(23, 34), (27, 33), (28.5, 41), (26, 41.5)]), "moletom", -1)         # sob o braço de trás
    p.set(torso & P([(28, 29), (30, 29), (29, 37), (27.5, 36)]), "moletom", -1)           # peito afundado
    p.set(torso & P([(22, 53.5), (27, 53), (25, 55)]), "moletom", 1)                       # barra caída na luz
    p.set(torso & P([(30, 53), (36, 52.5), (34, 55.5)]), "moletom", -2)
    p.set(near_arm & P([(39.5, 30), (42.5, 31), (41, 34)]), "moletom", -2)                 # prega no ombro
    p.set(far_arm & P([(21, 39), (25, 38.5), (24, 41)]), "moletom", -1)
    p.texture(torso | near_arm, -1, 0.1, seed=4, stroke=(2, 1))

    # --- pescoço, cabeça em 3/4, orelha, cabelo na máquina -----------------------------------------
    neck = p.rect(29, 21, 33, 25)
    p.set(neck, "pele", -1)
    head = p.ellipse(31.5, 13, 6.8, 7) | P([(26, 14), (38.5, 13), (39, 17), (37.5, 21), (35, 23),
                                             (31.5, 23), (28, 20.5)])
    p.set(head, "pele", 0)
    p.set(head & P([(36, 15), (39, 13.5), (39, 17), (37.5, 21), (36, 19.5)]), "pele", -1)   # frente na sombra
    p.set(head & P([(29, 20.5), (35, 22), (31.5, 23.2), (28.5, 21)]), "pele", -1)            # sob o queixo
    p.set(P([(38.5, 15), (40, 17.5), (38.5, 18)]), "pele", -1)                               # nariz
    ear = p.ellipse(27.3, 15.5, 1.5, 2.3)
    p.set(ear, "pele", 0)
    p.px(27, 15, "pele", -2)
    p.px(27, 16, "pele", -1)
    cap = p.ellipse(31.5, 12.6, 7.4, 7.3)
    hair = cap & (ys < 9.5 + np.clip(36.5 - xs, 0, None) * 0.55) & ~p.ellipse(27.3, 15.5, 2.1, 2.9)
    p.set(hair, "cabelo", 0)
    p.set(hair & P([(28, 5), (35, 5.5), (36.5, 8.5), (31, 9), (27.5, 8)]), "cabelo", 1)   # topo na luz
    p.set(hair & P([(23, 12), (27, 11), (27.5, 17), (24, 18)]), "cabelo", -1)             # nuca
    for x, y in ((29, 6), (32, 7), (26, 9), (34, 8), (28, 11), (31, 10)):
        p.px(x, y, "cabelo", 1 if (x + y) % 2 else -1)                                    # cachinhos em bloco
    # rosto discreto: sobrancelha grossa, olhos de 1–2 px, boca
    p.pixels([(34, 12), (35, 12), (36, 12), (35, 11), (36, 11)], "linha", 0)
    p.pixels([(29, 12), (30, 12), (31, 12)], "linha", 0)
    p.pixels([(35, 14), (35, 15), (30, 14)], "linha", 0)
    p.pixels([(36, 19), (37, 19)], "boca", 0)

    # --- luz de borda quente (de trás/esquerda) e contorno seletivo --------------------------------
    p.rim_light(dirs=((1, 0),), width=1, second=True)                               # azul do céu do outro lado
    p.rim_light(dirs=((-1, 0), (0, -1)), width=1)
    return p.render(outline="seletivo")
