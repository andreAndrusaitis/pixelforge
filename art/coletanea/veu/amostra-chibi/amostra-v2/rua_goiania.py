"""Rua de casas baixas em Goiânia — fim de tarde depois da chuva, 320×180.

Teste do kit de cenário (pixelforge.paint.Scene): céu em manchas rosa e laranja,
nuvens em blocos, perspectiva atmosférica (fundo claro e azulado), casas com laje e
caixa d'água, poste e fios, poste aceso com halo (destaque), calçada e asfalto
molhados com reflexo em faixas quebradas, moldura de mangueira em silhueta, gotas.
Render: python -m pixelforge render art/coletanea/veu/amostra-chibi/amostra-v2/rua_goiania.py
"""

import numpy as np

from pixelforge.paint import Scene, mix

NAME = "rua_goiania"
W, H = 320, 180
HORIZON = 104      # base do fundo distante
STREET = 131       # linha da calçada (pé das casas)

SKY = ["#2b2140", "#43284e", "#6a3256", "#9a425c", "#c45a5e", "#e27c5c", "#f2a066"]
SHADE = "#3a2440"  # sombra violeta comum da cena
LAMP = "#ffd28a"


def house(s: Scene, x: int, w: int, h: int, wall: str, depth: float = 0.15, tank: bool = True,
          gate: bool = True) -> None:
    """Casa térrea com laje, caixa d'água, janela gradeada, portão e muro de chapisco."""
    top = STREET - h
    wall_c = s.haze(mix(wall, SHADE, 0.45), depth)               # fachada contra a luz: sombra
    dark = s.haze(mix(wall, SHADE, 0.7), depth)
    lit = s.haze(mix(wall, "#f2a066", 0.35), depth)                # borda pegando o laranja
    s.put(s.rect(x, top, x + w - 1, STREET - 1), wall_c)
    s.cluster(s.rect(x, top + 3, x + w - 1, STREET - 1), [dark, mix(wall_c, dark, 0.5)], 0.25, (1, 2))
    s.put(s.rect(x, top, x + 1, STREET - 1), lit)                  # quina na luz (esquerda)
    # laje: placa saliente com borda clara do céu e sombra embaixo
    s.put(s.rect(x - 2, top - 3, x + w + 1, top - 1), s.haze("#8a6a7a", depth))
    s.put(s.rect(x - 2, top - 3, x + w + 1, top - 3), s.haze("#e8a08a", depth))
    s.put(s.rect(x, top, x + w - 1, top + 1), dark)
    if tank:                                                        # caixa d'água azul
        tx = x + int(w * 0.62)
        body = s.rect(tx, top - 13, tx + 13, top - 4) | s.ellipse(tx + 6.5, top - 13, 7, 2)
        s.put(body, s.haze("#3c4f78", depth))
        s.put(body & (s.xs <= tx + 3), s.haze("#6f7fa8", depth))
        s.put(s.rect(tx + 11, top - 12, tx + 13, top - 4), s.haze("#2a3354", depth))
        s.put(s.ellipse(tx + 6.5, top - 14, 6, 1.5), s.haze("#9ab0d0", depth))
        s.put(s.rect(tx - 1, top - 4, tx + 14, top - 4), s.haze("#2a2236", depth))
        s.put(s.rect(tx - 6, top - 8, tx - 2, top - 4), s.haze("#7a5a6a", depth))     # casinha da escada
    # janela com grade, uma acesa
    wx = x + 6
    win = s.rect(wx, top + 8, wx + 13, top + 18)
    on = (x // 7) % 3 == 0
    s.put(win, mix(LAMP, "#e08a50", 0.4) if on else s.haze("#1e1626", depth))
    for gx in range(wx, wx + 14, 3):
        s.put(s.rect(gx, top + 8, gx, top + 18), dark)
    s.put(s.rect(wx - 1, top + 19, wx + 14, top + 19), lit)        # peitoril
    if gate:                                                        # portão de garagem
        gx = x + w - 26
        g = s.rect(gx, top + 9, gx + 22, STREET - 1)
        s.put(g, s.haze("#4a3a4e", depth))
        for k in range(gx, gx + 23, 2):
            s.put(s.rect(k, top + 9, k, STREET - 1), s.haze("#33283a", depth))
        s.put(s.rect(gx, top + 9, gx + 22, top + 10), s.haze("#6a5468", depth))


def build():
    s = Scene(W, H, seed=21, haze_color="#c79aaa")

    # --- céu: faixas rosa/laranja, nuvens em blocos iluminadas por baixo ---------------
    s.sky(SKY, 0, HORIZON + 8, wobble=3, step=8)
    s.glow(62, 100, 46, "#ffc078", rings=4)                                          # sol atrás das casas
    s.clouds(70, 26, 120, 16, "#c86478", "#9a4a6a", "#f0a080", puffs=8)
    s.clouds(230, 18, 150, 14, "#b45a74", "#7a3a62", "#e8907a", puffs=9)
    s.clouds(275, 62, 90, 10, "#d87470", "#a8546a", "#f6b080", puffs=6)
    s.streaks(70, 100, "#f6b888", count=10)
    s.streaks(40, 70, "#d8707a", count=6)

    # --- fundo distante: prédios e copas, claros e azulados (perspectiva atmosférica) ---
    far = np.zeros((H, W), dtype=bool)
    x = 0
    while x < W:
        w = int(s.rng.integers(6, 22))
        h = int(s.rng.integers(6, 24))
        far |= s.rect(x, HORIZON - h, x + w, HORIZON + 10)
        x += w + int(s.rng.integers(0, 4))
    s.put(far, s.haze("#5a3a5a", 0.55))
    for k in range(0, W, 9):                                                        # janelinhas distantes
        if far[HORIZON - 4, k] and s.rng.random() < 0.4:
            s.put(s.rect(k, HORIZON - 5, k, HORIZON - 4), s.haze(LAMP, 0.4))
    s.put(s.rect(150, HORIZON - 40, 151, HORIZON) | s.rect(146, HORIZON - 30, 155, HORIZON - 29),
          s.haze("#4a3050", 0.5))                                                   # torre de antena
    for cx in (20, 110, 196, 300):                                                   # copas ao longe
        s.foliage(cx, HORIZON - 4, 12, [s.haze(c, 0.45) for c in ("#3a2a48", "#4a3456", "#5a3e60")], clumps=26)

    s.put(s.rect(0, HORIZON, W - 1, STREET - 1), s.haze("#3a2a44", 0.3))           # chão entre as casas
    # --- casas térreas com laje e caixa d'água --------------------------------------------
    for hx, hw, hh, col, gate in ((-6, 70, 30, "#c9a27a", True), (68, 64, 26, "#9aae8a", False),
                                   (136, 74, 32, "#d6b48a", True), (214, 58, 27, "#c88a7a", False),
                                   (276, 60, 30, "#a8a0b8", True)):
        house(s, hx, hw, hh, col, gate=gate)
    # muro com chapisco na frente das casas
    wall = s.rect(0, STREET - 9, W - 1, STREET - 1)
    s.put(wall, "#4a3446")
    s.cluster(wall, ["#3a2838", "#5a4054"], 0.4, (1, 2))
    s.put(wall & (s.ys == STREET - 9), "#9a6a6a")
    for px in range(40, W, 70):                                                     # pilares do muro
        s.put(s.rect(px, STREET - 11, px + 3, STREET - 1), "#3a2838")
        s.put(s.rect(px, STREET - 11, px, STREET - 1), "#9a6a6a")

    # --- poste, fios, luminária acesa ------------------------------------------------------
    pole = s.rect(232, 52, 234, STREET + 2)
    s.put(pole, "#3a2c3e")
    s.put(s.rect(232, 52, 232, STREET + 2), "#a0707a")                                # borda na luz
    s.put(s.rect(222, 60, 246, 61), "#2e2234")                                         # cruzeta
    for i, (y0, y1, sag) in enumerate(((58, 62, 9), (61, 66, 12), (64, 70, 14))):
        s.wire(0, y0 + 6, 223, y0 + i, sag, "#1e1624")
        s.wire(246, y0 + i, W, y1, sag * 0.7, "#1e1624")
    s.wire(0, 40, W, 52, 16, "#241a2a")
    s.put(s.curve([(234, 66), (240, 63), (246, 66)], 0.6), "#2e2234")                  # braço da luminária
    s.put(s.rect(244, 66, 248, 67), "#2e2234")
    s.glow(246, 69, 16, LAMP, core="#fff2d0", rings=3)

    # --- calçada e asfalto molhados, refletindo -------------------------------------------
    s.put(s.rect(0, STREET, W - 1, STREET + 6), "#5a4256")                             # calçada
    s.put(s.rect(0, STREET, W - 1, STREET), "#c08080")
    s.put(s.rect(0, STREET + 7, W - 1, STREET + 8), "#2a1e30")                         # meio-fio
    s.put(s.rect(0, STREET + 7, W - 1, STREET + 7), "#a87878")
    s.put(s.rect(0, STREET + 9, W - 1, H - 1), "#2a2034")                              # asfalto
    s.reflect(STREET, STREET + 1, STREET + 7, strength=0.35)
    s.reflect(STREET - 1, STREET + 9, H, strength=0.62, gap=3)
    puddles = np.zeros((H, W), dtype=bool)
    for _ in range(14):
        px, py = s.rng.integers(0, W), s.rng.integers(STREET + 12, H)
        puddles |= s.ellipse(px, py, s.rng.integers(6, 22), 1.2)
    s.img[puddles, :3] = np.minimum(255, s.img[puddles, :3].astype(int) + 22).astype(np.uint8)
    s.glow(246, 160, 10, LAMP, rings=2)                                                  # reflexo do poste aceso
    s.put(s.rect(244, 150, 248, 150) | s.rect(245, 155, 247, 155) | s.rect(243, 166, 249, 166), "#f6c888")

    # --- moldura: mangueira em silhueta à esquerda, mato embaixo à direita ---------------
    s.frame("esquerda", "#140c18", height=0.55, seed=4)
    s.foliage(10, 8, 30, ["#120a16", "#1a1020", "#24142a"], clumps=60)
    s.put(s.curve([(0, 70), (6, 50), (14, 30)], 2.5, 1.2), "#120a16")                  # galho
    s.frame("baixo", "#140c18", height=0.25, seed=7, count=14)

    # --- vida: gotas brilhando no fio e no chão ---------------------------------------------
    s.particles(18, ["#ffd8a8", "#f6a8a0"], s.rect(0, STREET + 10, W - 1, H - 1), plus=0.2)
    return s.sprite()
