"""Seu Geraldo (64 anos, quase 2 m) — corpo inteiro, amostra v2 (~140 px, 6 cabeças).

3/4 virado para a esquerda (o antebraço esquerdo, com a cicatriz, fica do lado de quem olha).
Quadro 0: de chapéu (aba fazendo sombra nos olhos), mão no quadril.
Quadro 1: sem chapéu, segurando o chapéu no peito; cabelo branco rente à mostra.
Luz: fim de tarde depois da chuva, laranja de trás/esquerda.
Render: python -m pixelforge render art/coletanea/veu/amostra-chibi/amostra-v2/geraldo.py

Marcos (y): copa 4 · topo da cabeça 8 · queixo 32 · ombro 38 · barriga 66 · cinto 79 ·
entreperna 85 · joelho 111 · tornozelo 136 · chão 145.
"""

import numpy as np

from pixelforge.paint import Paint

NAME = "geraldo_v2"
W, H = 80, 148

RAMPS = {
    "pele": (["#47292a", "#76493b", "#9c674d", "#bf8762"], 2, "#f2aa74", "#2c1718"),
    "cabelo": (["#6a6672", "#98949e", "#c6c2c2", "#e4e0d8"], 2, "#ffe0c0", "#3e3a44"),
    "linha": (["#150d0e", "#26181a"], 0, "#26181a", "#0b0607"),
    "chapeu": (["#22160f", "#38281d", "#56402f", "#765a43"], 2, "#de8a52", "#120b08"),
    "fita": (["#120b09", "#1f150f"], 1, "#5a3a26", "#0b0605"),
    "camisa": (["#3a3c4c", "#5a5f70", "#7b8293", "#9ea6b2"], 2, "#f0b88a", "#1e1f2a"),
    "botao": (["#e8e4dc"], 0, "#ffffff", "#2e3040"),
    "brim": (["#15182a", "#22293e", "#323c56", "#475270"], 2, "#a8705a", "#0a0b14"),
    "cinto": (["#1b110b", "#301f17", "#4a3222"], 1, "#b07040", "#0d0805"),
    "fivela": (["#6d5c33", "#b39a55"], 1, "#f0d890", "#2a2214"),
    "botina": (["#0e0908", "#1b120e", "#2c1f19", "#463226"], 2, "#c47a4e", "#060403"),
    "brilho": (["#f2dcc6"], 0, "#ffffff", "#060403"),
    "cicatriz": (["#cf9a80", "#f2c8ad"], 0, "#ffe8d8", "#2c1718"),
    "boca": (["#4f2827", "#6b3833"], 1, "#6b3833", "#2c1718"),
}


def setup(p: Paint) -> None:
    for name, (colors, base, rim, outline) in RAMPS.items():
        p.custom_ramp(name, colors, base, rim=rim, outline=outline)


def hat_at(p: Paint, ox: float, oy: float, held: bool = False) -> np.ndarray:
    """Chapéu de feltro. (ox, oy) = centro da aba. `held`: visto de frente, na mão (aba como elipse)."""
    P = p.poly
    if held:
        brim = p.ellipse(ox, oy, 13.5, 4.5)
        crown = P([(ox - 8, oy + 1), (ox - 7.5, oy - 7), (ox - 3, oy - 9.5), (ox + 4, oy - 9.5),
                   (ox + 7.5, oy - 7), (ox + 8, oy + 1)])
    else:
        brim = P([(ox - 19.5, oy + 1.5), (ox - 11, oy - 2), (ox + 11, oy - 2), (ox + 19, oy + 0.5),
                  (ox + 15, oy + 3), (ox, oy + 3.5), (ox - 15, oy + 3.5)])
        crown = P([(ox - 11, oy - 1), (ox - 10.5, oy - 8.5), (ox - 6, oy - 12.5), (ox + 6, oy - 12.5),
                   (ox + 10.5, oy - 9.5), (ox + 12, oy - 1)])
    p.set(brim, "chapeu", 0)
    p.set(brim & (p.ys >= oy + 1), "chapeu", -1)
    p.set(brim & (p.xs >= ox + 8), "chapeu", -1)
    p.set(crown, "chapeu", 0)
    p.set(crown & (p.xs >= ox + 3), "chapeu", -1)
    p.set(crown & (p.xs <= ox - 6) & (p.ys <= oy - 4), "chapeu", 1)
    p.line(ox - 3, oy - 10.5, ox + 2, oy - 8.5, "chapeu", -2)                       # vinco do topo
    band = crown & (p.ys >= oy - 3.5) & (p.ys <= oy - 1)
    p.set(band, "fita", 0)
    p.set(band & (p.xs <= ox - 5), "fita", 1)
    p.texture(brim | crown, -1, 0.18, seed=9, stroke=(1, 1))                        # feltro
    return brim | crown


def build():
    return [draw(True), draw(False)]


def draw(with_hat: bool):
    p = Paint(W, H)
    setup(p)
    ys, xs = p.ys, p.xs
    P = p.poly

    # --- botinas engraxadas -------------------------------------------------------------------
    for pts, shine in (([(26, 134), (37, 134), (37.5, 140), (37, 144), (16, 144), (17, 140), (22, 137.5)], (21, 139)),
                       ([(43, 134), (54, 134), (54.5, 144), (35.5, 144), (36.5, 140), (40, 137.5)], (40, 139))):
        boot = P(pts)
        p.set(boot, "botina", 0)
        p.set(boot & (ys >= 141), "botina", -1)
        p.set(p.rect(min(x for x, _ in pts), 144, max(x for x, _ in pts), 145) & p.rect(0, 0, 80, 148), "botina", -2)
        p.pixels([shine, (shine[0] + 1, shine[1]), (shine[0] + 1, shine[1] - 1)], "brilho", 0)   # graxa
        p.pixels([(shine[0] + 4, shine[1] - 2), (shine[0] + 8, 136)], "botina", 1)
        p.line(pts[0][0], 134.5, pts[1][0], 134.5, "botina", -1)                                     # cano

    # --- calça de brim ---------------------------------------------------------------------------
    far_leg = P([(23.5, 81), (39, 81), (38, 110), (37, 135), (26, 135), (25.5, 110)])
    near_leg = P([(38, 80), (57.5, 80), (56, 110), (54, 135), (43, 135), (41.5, 110)])
    p.set(far_leg, "brim", 0)
    p.set(far_leg & (xs >= 33), "brim", -1)
    p.set(near_leg, "brim", 0)
    p.set(near_leg & (xs >= 50), "brim", -1)
    p.set(near_leg & P([(42, 82), (46, 82), (44, 108), (42, 108)]), "brim", 1)             # coxa na luz
    for leg, x0, x1 in ((far_leg, 25, 38), (near_leg, 42, 56)):
        p.set(leg & P([(x0 + 2, 108), (x1 - 1, 106), (x1 - 2, 112), (x0 + 3, 113)]), "brim", -1)   # joelho
        p.line(x0 + 3, 110, x1 - 3, 109, "brim", 1)
        for y in (128, 131):                                                                         # barra empilhada
            p.line(x0 + 1, y, x1 - 1, y + 1, "brim", -2)
    p.line(55, 84, 53.5, 133, "brim", -2)                                                          # costura lateral
    p.set(P([(37, 84), (40, 84), (39.5, 100)]), "brim", -2)                                        # entreperna
    p.texture(far_leg | near_leg, -1, 0.12, seed=2, stroke=(1, 2))

    # --- tronco: ombros largos, barriga, camisa de botão -------------------------------------------
    torso = P([(21, 41), (29, 36), (51, 36), (59, 40.5), (60.5, 58), (58, 80.5), (25, 81), (22, 62)])
    belly = p.ellipse(36.5, 66, 15.5, 13.5)
    shirt = torso | belly
    p.set(shirt, "camisa", 0)
    p.set(shirt & P([(48, 37), (59, 40.5), (60.5, 58), (58, 80.5), (47, 80), (50, 60)]), "camisa", -1)  # lado da sombra
    p.set(belly & P([(22, 62), (35, 55), (40, 62), (30, 75), (22, 72)]), "camisa", 1)              # barriga na luz
    p.set(shirt & P([(22, 72), (35, 75.5), (48, 76), (47, 80), (25, 80.5)]), "camisa", -1)         # sob a barriga
    p.set(shirt & P([(26, 48), (33, 46), (30, 54)]), "camisa", -1)                                  # prega do peito
    for a, b in (((37, 60), (45, 57)), ((36, 66), (45, 64)), ((35, 72), (43, 71)), ((38, 55), (28, 58))):
        p.line(*a, *b, "camisa", -1)                                                                # repuxado nos botões
    # pregas grandes: tecido puxado dos ombros para a barriga, sobra no flanco
    for pts, t in (([(30, 38), (35, 38), (30, 50), (27, 49)], 1), ([(44, 39), (49, 38), (47, 52), (44, 50)], -1),
                   ([(25, 52), (29, 54), (24, 62)], -1), ([(50, 62), (57, 60), (56, 70), (51, 70)], -2),
                   ([(41, 70), (47, 68), (46, 75)], -1), ([(53, 42), (58, 43), (56, 50)], -2)):
        p.set(shirt & P(pts), "camisa", t)
    p.texture(shirt, -1, 0.12, seed=7, stroke=(2, 1))
    p.line(39, 37, 35.5, 50, "camisa", -2)                                                          # carcela
    p.line(35.5, 50, 35, 78, "camisa", -2)
    for y in (43, 51, 59, 67, 75):
        p.px(36 if y > 48 else 38, y, "botao", 0)
    pocket = P([(44, 45), (51, 45), (51, 52), (44, 52)])
    p.shift(pocket, -1)
    p.line(44, 45, 51, 45, "camisa", -2)
    # cinto sob a barriga
    belt = (p.rect(23, 78, 58, 81) & ~belly) | (p.rect(44, 77, 58, 80))
    p.set(belt, "cinto", 0)
    p.set(belt & (xs >= 50), "cinto", -1)
    p.set(P([(29, 79), (33, 79), (33, 81), (29, 81)]), "fivela", 0)

    # --- braços: manga dobrada, mãos enormes, cicatriz no antebraço esquerdo ---------------------
    def sleeve(points, cuff_y, cuff_x0, cuff_x1):
        s = P(points)
        p.set(s, "camisa", 0)
        p.set(s & (xs >= (cuff_x0 + cuff_x1) / 2 + 1), "camisa", -1)
        cuff = s & (ys >= cuff_y) & (ys <= cuff_y + 3)                                              # manga dobrada
        p.set(cuff, "camisa", 1)
        p.set(cuff & (ys == cuff_y + 3), "camisa", -2)
        return s

    def hand(points, knuckles):
        h = P(points)
        p.set(h, "pele", 0)
        p.set(h & (xs >= np.mean([x for x, _ in points]) + 1), "pele", -1)
        for a, b in knuckles:
            p.line(*a, *b, "pele", -2)
        return h

    if with_hat:
        # braço de trás: cotovelo para fora, mão enorme no quadril
        sleeve([(21, 41), (27, 40), (23, 52), (16, 58), (12.5, 55), (17, 45)], 52, 12, 22)
        fore = P([(12.5, 56), (17, 58), (27, 72), (23, 76), (11, 61)])
        p.set(fore, "pele", 0)
        p.set(fore & (ys >= 66) & (xs >= 20), "pele", -1)
        hand([(21, 70), (30, 72), (32, 79), (27, 82), (21, 79)], [((24, 74), (28, 80)), ((27, 73), (30, 79))])
        # braço da frente: solto ao lado do corpo, antebraço com a cicatriz
        sleeve([(51, 37), (59, 40.5), (62.5, 55), (63, 61), (55, 61), (54, 50)], 56, 54, 63)
        fore = P([(55, 61), (63, 61), (63.5, 72), (62.5, 82), (55.5, 82), (55, 72)])
        p.set(fore, "pele", 0)
        p.set(fore & (xs >= 60), "pele", -1)
        p.set(P([(56.5, 65), (58.5, 64), (61.5, 75), (59.5, 76)]), "cicatriz", 0)                    # cicatriz lisa
        p.pixels([(57, 66), (58, 68), (59, 70)], "cicatriz", 0)
        p.px(58, 67, "brilho", 0, lock=True)                                                         # brilho da cicatriz
        hand([(54, 81), (63.5, 81), (65, 88), (63, 95), (56, 95), (53.5, 89)],
             [((56, 90), (56, 95)), ((59, 90), (59, 95)), ((62, 89), (62, 94))])
    else:
        # os dois braços dobrados, mãos enormes segurando o chapéu no peito
        sleeve([(21, 41), (27, 40), (25, 52), (18, 58), (14.5, 54), (17, 45)], 52, 14, 24)
        p.set(P([(14.5, 55), (19, 58), (31, 58), (30, 63), (16, 61)]), "pele", 0)
        sleeve([(51, 37), (59, 40.5), (62.5, 54), (61, 60), (54, 59), (54, 48)], 54, 54, 62)
        fore = P([(54, 58), (61.5, 59), (55, 66), (46, 64), (48, 60)])
        p.set(fore, "pele", 0)
        p.set(fore & (ys >= 62), "pele", -1)
        p.set(P([(58, 60), (59.5, 60.5), (53, 64), (52, 63)]), "cicatriz", 0)
        p.px(56, 61, "brilho", 0, lock=True)
        hat_at(p, 39, 57, held=True)
        hand([(27, 52), (34, 52), (35, 60), (31, 63), (26, 59)], [((29, 54), (29, 60)), ((32, 54), (32, 60))])
        hand([(44, 53), (51, 53), (52, 60), (48, 64), (43, 60)], [((46, 55), (46, 61)), ((49, 55), (49, 61))])

    # --- pescoço, gola, cabeça (3/4 para a esquerda) ----------------------------------------------
    neck = P([(35, 29), (47, 29), (48, 38), (35, 38)])
    p.set(neck, "pele", -1)
    p.set(neck & (xs <= 37), "pele", 0)
    for pts in ([(32, 36), (40, 38.5), (35.5, 43)], [(40, 38.5), (48, 35), (47, 41)]):
        c = P(pts)
        p.set(c, "camisa", 1 if pts[0][0] < 35 else -1)                                            # pontas da gola
    head = p.ellipse(41, 19.5, 10, 11.5) | P([(31.5, 19), (48.5, 20), (47.5, 27.5), (43.5, 32),
                                               (37.5, 32.5), (33, 29.5), (31, 24.5)])
    p.set(head, "pele", 0)
    p.set(head & P([(44, 14), (51, 16), (50, 26), (47.5, 28), (44, 25)]), "pele", -1)             # lado de trás na sombra
    p.set(head & P([(34, 29), (44, 30), (42, 32.5), (37, 32.5)]), "pele", -1)                     # sob o queixo
    p.set(P([(32, 20.5), (29.5, 25), (32, 26)]), "pele", 0)                                        # nariz
    p.px(31, 25, "pele", -1)
    ear = p.ellipse(49.5, 22.5, 2, 3.2)
    p.set(ear, "pele", -1)
    p.px(50, 22, "pele", -2)
    # rosto liso, bem barbeado: só o essencial
    p.pixels([(33, 29), (34, 29), (35, 29), (36, 29.4)], "boca", 0)                               # boca
    p.pixels([(36, 27), (37, 28)], "pele", -1)                                                     # sulco
    p.pixels([(34, 20), (40, 20), (41, 20)], "linha", 0)                                           # olhos (1–2 px)
    # cabelo branco rente
    cap = p.ellipse(41.5, 18.5, 10.8, 12)
    if with_hat:
        hair = cap & (xs >= 45) & (ys >= 13) & (ys <= 24) & ~p.ellipse(49.5, 22.5, 2.6, 3.8)
    else:
        hair = cap & (ys < 12 + np.clip(xs - 35, 0, None) * 0.55) & ~p.ellipse(49.5, 22.5, 2.6, 3.8)
        p.pixels([(33, 16), (34, 16), (35, 16), (39, 16), (40, 16), (41, 16)], "cabelo", 1)         # sobrancelhas brancas
    p.set(hair, "cabelo", 0)
    p.set(hair & (xs <= 40) & (ys <= 12), "cabelo", 1)
    p.set(hair & (xs >= 48), "cabelo", -1)
    p.texture(hair, -1, 0.3, seed=1, stroke=(1, 1))
    if with_hat:
        h = hat_at(p, 40, 13.5)
        shadow = p.moved(h, 0, 4) & ~h & head                                                       # aba sombreando os olhos
        p.shift(shadow, -1, "pele")
        p.set(shadow & P([(30, 17), (45, 17), (45, 19), (30, 19)]), "pele", -2)
        p.pixels([(34, 20), (40, 20)], "linha", 0)
        p.px(41, 20, "pele", -2)

    # --- luz de borda quente e contorno seletivo -------------------------------------------------
    p.rim_light(dirs=((1, 0),), width=1, second=True)                               # azul do céu do outro lado
    p.rim_light(dirs=((-1, 0), (0, -1)), width=1)
    return p.render(outline="seletivo")
