"""Martim (12 anos, pequeno e magro) — corpo inteiro final (~96 px), estilo "pintado".

Guia direto: ref 21 (moletom grande, postura largada em A, calça larga com dobras
grandes, olhos escondidos) e ref 22 (luz de borda dupla). A ficha dá crespo na máquina
(sem franja): os olhos ficam na sombra da sobrancelha grossa, cabeça um pouco baixa.
Luz: fim de tarde depois da chuva, laranja de trás/esquerda + azul do céu à direita.
Render: python -m pixelforge render art/coletanea/veu/final/martim.py

Marcos (y): topo 5 · queixo 28 · ombros 31–34 (o da esquerda mais baixo) ·
barra 60–62 (quadril esquerdo mais alto: peso na perna de trás) · joelho 79 · chão 101.
"""

import numpy as np

from pixelforge.paint import Paint

NAME = "martim_final"
W, H = 64, 104
FPS = 4


def setup(p: Paint) -> None:
    p.hue_ramp("pele", "#9a6345", 3, 2, hue=16, rim="#ec9a5c", outline="#2a1418", rim2="#8a7ea8")
    p.hue_ramp("cabelo", "#2e2226", 3, 2, hue=20, rim="#a8653f", outline="#0a060a", rim2="#4a4a6a")
    p.custom_ramp("linha", ["#0f080c", "#1a0f13", "#2a1a1c"], 0, rim="#2a1a1c", outline="#09060a")
    p.custom_ramp("olho", ["#2e1a18", "#4a2a24"], 0, rim="#4a2a24", outline="#1a0c0c")    # marrom-escuro, não preto
    p.hue_ramp("moletom", "#5e6274", 3, 2, hue=14, rim="#de9c6c", outline="#16141f", rim2="#7c8cc0")
    p.custom_ramp("cordao", ["#7a7a8a", "#a8a6ae", "#cfcac4", "#ebe4da"], 2, rim="#ffd0a0", outline="#3a3a48")
    p.custom_ramp("camiseta", ["#7c7a8a", "#aaa6ae", "#d0cac4", "#ebe5dc"], 2, rim="#ffd8b0", outline="#3a3a48")
    p.hue_ramp("calca", "#2c3147", 3, 2, hue=18, rim="#b07050", outline="#0a0b12", rim2="#5a6aa0")
    p.custom_ramp("tenis", ["#4a4652", "#6e6a72", "#9a948e", "#bfb7a8", "#ddd3c0"], 3, rim="#f6c08a",
                  outline="#2a2830", rim2="#9aa8d0")
    p.custom_ramp("sola", ["#6e6c74", "#a6a29a", "#d6d0c4", "#efe9de"], 2, rim="#ffd8a8", outline="#2a2830")
    p.custom_ramp("boca", ["#3a1c1e", "#5a2c2a", "#7a4038"], 1, rim="#7a4038", outline="#2a1418")
    p.custom_ramp("celular", ["#101018", "#1c1e2a", "#3a4a6a", "#8ab8d8"], 1, rim="#3a4a6a", outline="#08080c")


def figure(pose: dict | None = None) -> Paint:
    """pose: {"respira": 0|1, "olhos": "abertos"|"fechados", "boca": 0|1, "passo": -3..3}."""
    pose = pose or {}
    up = pose.get("respira", 0)
    step = pose.get("passo", 0)
    p = Paint(W, H)
    setup(p)
    ys, xs = p.ys, p.xs
    P = p.poly

    def Q(points, dy=up):
        return P([(x, y + dy) for x, y in points])

    fs = -step

    # --- calça larga em A: perna de trás com o peso, a da frente aberta ------------------------
    far_leg = P([(21, 60), (32, 61.5), (30.5, 75), (29 + fs * 0.5, 87), (28.5 + fs, 94), (19 + fs, 94),
                 (19.5 + fs * 0.5, 87), (21, 75)])
    p.set(far_leg, "calca", -1)
    p.set(far_leg & P([(21, 60), (25, 60.5), (23, 87), (20, 87)]), "calca", 0)
    for pts, t in (([(21, 64), (28, 63), (26, 69), (21.5, 70)], 1),
                   ([(24, 71), (31, 69), (30, 74), (25, 75.5)], -2),
                   ([(20.5, 78), (27, 76.5), (24.5, 81)], 0),
                   ([(25, 81), (29.5, 80), (29, 85)], -2)):
        p.set(far_leg & P(pts), "calca", t)
    p.set(far_leg & (ys >= 86) & (ys <= 88), "calca", 0)
    p.set(far_leg & (ys >= 89) & (ys <= 90), "calca", -3)
    p.set(far_leg & (ys >= 91), "calca", -1)
    near_leg = P([(31, 61.5), (41.5, 60.5), (44.5, 69), (45.5 + step * 0.5, 79), (46 + step, 87),
                  (46.5 + step, 94), (37.5 + step, 94), (37.5 + step, 87), (36, 79), (33, 70)])
    p.set(near_leg, "calca", 0)
    p.set(near_leg & P([(39, 60.5), (41.5, 60.5), (44.5, 69), (45.5, 79), (46, 87), (42.5, 83), (42, 70)]), "calca", -1)
    for pts, t in (([(33, 66), (38, 66.5), (37.5, 74), (35, 73)], 1),             # joelho na luz
                   ([(35.5, 75), (45, 73.5), (44.5, 78), (37, 79.5)], -3),        # dobra atrás do joelho
                   ([(37, 80.5), (43.5, 79.5), (41.5, 83)], -1),
                   ([(37, 84.5), (46, 83), (46.5, 87.5), (37.5, 88.5)], 1),        # sobra amontoada
                   ([(37, 89.5), (46.5, 89), (46.5, 91), (37.5, 91.5)], -3),
                   ([(40.5, 92), (46.5, 92), (46.5, 94), (40.5, 94)], -1)):
        p.set(near_leg & P(pts), "calca", t)
    p.set(P([(31, 62), (34, 62), (33.5, 72), (31.5, 66)]), "calca", -3)            # entreperna
    # aresta clara em cima de cada dobra (o tecido vira para a luz antes de afundar)
    calca = p.rid == p._r("calca")
    base = p.ramps[p._r("calca")].base
    deep = calca & (p.tone <= base - 2)
    lip = calca & ~deep & p.moved(deep, 0, -1) & (p.tone <= base)
    p.tone[lip] = base + 1

    # --- tênis claros com a sola colada --------------------------------------------------------
    for pts, x0, x1, dx in (([(17, 93), (27.5, 93), (30.5, 97), (31, 100), (16.5, 100), (16.5, 96)], 16.5, 31, fs),
                            ([(36.5, 93), (45.5, 93), (49, 97), (50, 100), (36.5, 100)], 36.5, 50, step)):
        shoe = P([(x + dx, y) for x, y in pts])
        x0, x1 = x0 + dx, x1 + dx
        p.set(shoe, "tenis", 0)
        p.set(shoe & (ys <= 95), "tenis", 1)
        p.set(shoe & (xs <= x0 + 2) & (ys <= 97), "tenis", 2)
        p.set(shoe & (xs >= x1 - 4) & (ys >= 97), "tenis", -1)
        p.line(x0 + 3, 95, x0 + 7, 94.5, "tenis", -3)
        p.px(int(x0 + 5), 96, "tenis", -2)
        p.set(p.rect(x0, 101, x1, 101) | p.rect(x0 + 1, 100, x1 - 1, 100), "sola", 0)
        p.line(x0 + 1, 100, x1 - 1, 100, "sola", -1)                                   # emenda da cola
        p.pixels([(x0 + 3, 101), (x1 - 3, 100), (x1 - 2, 100)], "tenis", -3)            # cola soltando
        p.set(shoe & (xs >= x1 - 2) & (ys >= 99), "sola", -2)

    # --- moletom grande, ombro esquerdo caído, barra inclinada ------------------------------------
    torso = Q([(21, 34), (28, 31), (37, 30), (43.5, 31), (45.5, 42), (46, 59.5), (41, 62), (31, 62.5),
               (20.5, 60.5), (20, 46)])
    p.set(torso, "moletom", 0)
    p.set(torso & Q([(36, 31), (43.5, 31), (45.5, 42), (46, 59.5), (41, 62), (38.5, 61), (40, 44)]), "moletom", -1)
    p.set(torso & Q([(41, 33), (44.5, 36), (45.5, 48), (43, 50), (42.5, 40)]), "moletom", -2)
    p.set(torso & Q([(21, 34), (27, 32), (25.5, 45), (20.5, 47)]), "moletom", 1)
    for pts, t in (([(24, 41), (29, 39.5), (30, 47), (26.5, 48)], -1),
                   ([(28.5, 35), (31.5, 35), (30.5, 43), (28.5, 42)], -1),
                   ([(22, 57), (29, 56.5), (26, 60)], 1),
                   ([(30, 57), (38, 56.5), (35, 61)], -2),
                   ([(28, 49), (33, 48.5), (30, 52)], 1)):
        p.set(torso & Q(pts), "moletom", t)
    hem = torso & (ys >= 57 + up + (xs - 20) * 0.08)
    p.shift(hem, -1)
    for x in range(21, 46, 2):
        p.px(x, int(59 + up + (x - 20) * 0.1), "moletom", -3)                       # ribana inclinada
    p.shift(torso & Q([(26, 38), (40, 37), (41, 46), (27, 46.5)]) & (xs >= 31), -1)       # sombra sob o peito
    for a, b in (((30, 31), (24.5, 40)), ((35.5, 31), (40.5, 39))):                       # costura raglan
        p.line(a[0], a[1] + up, b[0], b[1] + up, "moletom", -2)
    pocket = Q([(27, 47), (41.5, 46.5), (44, 57), (26, 58)])
    p.set(pocket, "moletom", 0)
    p.set(pocket & (xs >= 38), "moletom", -1)
    p.set(pocket & Q([(35, 48), (41, 47.5), (40, 52), (36, 52)]), "moletom", 1)          # mão no bolso (volume)
    p.line(27, 47 + up, 41.5, 46.5 + up, "moletom", -3)
    p.line(27, 48 + up, 37, 47.5 + up, "moletom", 1)                                        # borda do bolso na luz
    p.line(28, 57 + up, 43, 56.5 + up, "moletom", -2)
    # braço da frente dobrado, mão no bolso
    near_arm = Q([(37, 30.5), (43, 32.5), (46.5, 45), (44, 51.5), (37, 51), (41, 45.5), (39.5, 37)])
    p.set(near_arm, "moletom", -1)
    p.set(near_arm & Q([(37, 30.5), (42, 32), (42, 41), (39.5, 37)]), "moletom", 0)
    p.set(near_arm & Q([(41, 45.5), (46.5, 45), (44, 51.5), (40, 49.5)]), "moletom", -3)
    p.line(41.5, 41 + up, 45, 40 + up, "moletom", -3)
    p.line(38, 50 + up, 43, 50 + up, "moletom", -3)
    # braço de trás solto ao lado do corpo, mão com o celular
    far_arm = Q([(18.5, 34.5), (24, 33), (25, 46), (23.5, 57), (17.5, 57.5), (17, 46)])
    p.set(far_arm, "moletom", 0)
    p.set(far_arm & (xs <= 19.5), "moletom", 1)
    p.set(far_arm & Q([(22, 36), (24, 34.5), (25, 46), (23.5, 56), (22, 50)]), "moletom", -1)
    for y0 in (43, 49):                                                                   # dobras da manga
        p.line(18, y0 + up, 23, y0 + 1.5 + up, "moletom", -2)
    p.set(Q([(17.5, 55), (23.5, 55), (23.5, 58.5), (17.5, 58.5)]), "moletom", -1)         # punho
    for x in (18, 20, 22):
        p.px(x, 57 + up, "moletom", -3)
    hand = Q([(17.5, 58.5), (23.5, 58.5), (24, 63.5), (21.5, 65.5), (18, 64.5), (17, 61.5)])
    p.set(hand, "pele", 0)
    p.set(hand & (xs >= 22), "pele", -1)
    p.set(Q([(19.5, 60), (22.5, 60), (22.5, 66.5), (19.5, 66.5)]), "celular", 0)          # celular
    p.set(Q([(20, 61), (22, 61), (22, 65), (20, 65)]), "celular", 1)
    p.px(21, 62 + up, "celular", 2)
    p.pixels([(18, 61 + up), (18, 63 + up), (23, 62 + up)], "pele", 1)                    # dedos por cima
    # capuz grande caído nos ombros, cordão, gola da camiseta
    hood = Q([(19, 35), (22, 30), (28, 28.8), (34, 29.2), (39.5, 30.5), (38, 35.5), (31, 37.5), (23, 38)])
    p.set(hood, "moletom", 0)
    p.set(hood & Q([(24, 30.5), (34, 30), (33, 34.5), (27, 35.5)]), "moletom", -3)
    p.set(hood & Q([(19, 35), (22, 30), (25, 31.5), (21, 37)]), "moletom", 1)
    p.set(hood & Q([(34, 30.5), (39.5, 30.5), (38, 35.5), (34, 34.5)]), "moletom", -1)
    p.shift(torso & ~hood & p.moved(hood, 0, 2) & ~p.moved(hood, 0, 0), -1)               # sombra do capuz no colo
    p.set(Q([(29, 33.5), (35, 33), (36, 35.5), (30, 36)]), "camiseta", 0)
    p.line(31, 36.5 + up, 30.5, 45 + up, "cordao", 0)
    p.line(35, 36.5 + up, 36, 43 + up, "cordao", -1)
    p.pixels([(30, 46 + up), (36, 44 + up)], "cordao", -2)

    # --- pescoço e cabeça (um pouco baixa) ----------------------------------------------------------
    hy = up + 1
    neck = Q([(29, 26), (34.5, 26), (34.5, 31), (29, 31)])
    p.set(neck, "pele", -1)
    p.set(neck & (xs <= 30), "pele", 0)
    head = p.ellipse(32, 16 + hy, 9, 9.5) | Q([(24.5, 17), (41, 15.5), (41.8, 21), (39.5, 25.5), (36.5, 28.2),
                                               (32, 28.2), (28.5, 25.5), (25, 21.5)], hy)
    p.set(head, "pele", 0)
    p.set(head & Q([(36.5, 17), (41.5, 15.5), (41.8, 21), (39.5, 25.5), (36.5, 28), (37.5, 22)], hy), "pele", -1)
    p.set(head & Q([(28.5, 24.5), (36, 26), (32, 28.4), (28.5, 26)], hy), "pele", -2)
    p.set(head & Q([(25.5, 18), (29, 18), (29.5, 23), (26.5, 23)], hy), "pele", 1)
    p.set(Q([(41, 18), (43.2, 21.5), (41, 22.5)], hy), "pele", 0)
    p.set(Q([(41.5, 21), (43.2, 21.5), (41.2, 22.6)], hy), "pele", -1)
    ear = p.ellipse(26.2, 19.5 + hy, 1.8, 2.8)
    p.set(ear, "pele", 0)
    p.pixels([(26, 19 + hy), (26, 20 + hy)], "pele", -2)
    cap = p.ellipse(32, 15.2 + hy, 9.8, 10)
    hair = cap & (ys < 12 + hy + np.clip(39 - xs, 0, None) * 0.55) & ~p.ellipse(26.2, 19.5 + hy, 2.4, 3.4)
    p.set(hair, "cabelo", 0)
    rimtop = hair & ~p.moved(hair, 0, 1)
    tx, ty = np.nonzero(rimtop.T)
    for x, y in zip(tx, ty):                                                   # tufos crespos de 2–3 px na silhueta
        if x % 4 == 1 and y > 0:                                               # carocinho de 1 px, não espeto
            p.px(int(x), int(y) - 1, "cabelo", 0 if x < 33 else -1)
    for cx, cy in ((28, 7), (31, 6), (34, 6.5), (27, 10), (30, 9), (25, 13)):   # brilho em grupos de 1–3 px
        p.pixels([(cx, cy + hy), (cx + 1, cy + hy)] + ([(cx, cy + 1 + hy)] if cx % 2 else []), "cabelo", 2)
    p.set(hair & Q([(22, 15), (26, 13), (26.5, 21), (23, 22)], hy), "cabelo", -1)
    rng = np.random.default_rng(5)
    for y in range(5, 23, 2):
        for x in range(23 + (y // 2) % 2, 41, 2):
            if 0 <= y + hy < H and hair[y + hy, x] and rng.random() < 0.45:
                p.px(x, y + hy, "cabelo", 1 if rng.random() < 0.5 else -1)
    p.line(34, 13 + hy, 40, 12 + hy, "cabelo", -1)
    # rosto: faixa de sombra da sobrancelha, olhos de 1–2 px, boca
    p.set(Q([(32.5, 15.5), (40, 14.5), (40, 17.5), (33, 18)], hy) & head, "pele", -2)
    p.set(Q([(28.5, 16), (31.5, 15.8), (31.5, 18.3), (28.5, 18.5)], hy) & head, "pele", -2)
    p.pixels([(34, 15 + hy), (35, 15 + hy), (36, 14 + hy), (37, 14 + hy), (38, 14 + hy), (35, 14 + hy),
              (39, 14 + hy)], "linha", 0)
    p.pixels([(29, 16 + hy), (30, 16 + hy), (31, 15 + hy)], "linha", 0)
    if pose.get("olhos", "abertos") == "abertos":
        p.pixels([(36, 17 + hy), (37, 17 + hy), (38, 17 + hy)], "olho", 0)
        p.pixels([(29, 18 + hy), (30, 18 + hy)], "olho", 1)
    else:
        p.pixels([(36, 18 + hy), (37, 18 + hy), (30, 18 + hy)], "pele", -3)
    if pose.get("boca", 0):
        p.set(Q([(37, 24), (39.5, 23.8), (39.5, 25.5), (37.5, 25.6)], hy), "boca", 0)
    else:
        p.pixels([(37, 24 + hy), (38, 24 + hy), (39, 24 + hy)], "boca", 1)
    p.px(36, 23 + hy, "pele", -2)
    p.pixels([(40, 22 + hy), (41, 23 + hy)], "pele", -2)                                    # sombra do nariz

    # --- acabamento: pinceladas direcionais + mistura nas fronteiras, luz de borda dupla -----------
    cloth = (p.rid == p._r("moletom")) | (p.rid == p._r("calca"))
    p.texture(cloth, -1, 0.035, seed=3, stroke=(3, 1))
    p.texture(cloth, 1, 0.02, seed=8, stroke=(2, 1))
    p.painterly(cloth, edge=0.5, speck=0.0, dither=0.005, seed=11)
    p.painterly(~cloth, edge=0.25, speck=0.0, seed=12)
    p.rim_spots([(40, 28, 47, 36), (42, 44, 48, 52)], second=True, dirs=((1, 0),))         # fria: ombro e cotovelo
    p.rim_spots([(20, 0, 34, 12), (16, 28, 25, 40), (15, 44, 21, 56), (15, 92, 24, 101)])  # quente: 4 pontos
    return p


def build():
    return grow(figure().render(outline="seletivo", dark_open=True))


GROW_ROWS = (76, 82, 88)    # canela mais longa: ~99 px (Geraldo fica ~1,4× a altura)


def grow(sprite):
    """Duplica linhas da canela (o desenho não muda; a figura cresce pelo chão)."""
    from pixelforge.sprite import Sprite
    rows = []
    for y in range(sprite.height):
        rows.append(sprite.pixels[y])
        if y in GROW_ROWS:
            rows.append(sprite.pixels[y])
    px = np.stack(rows[len(GROW_ROWS):], axis=0)
    return Sprite(px)
