"""Viajante de capa vermelha com lanterna (sprite de ator, 32x32, olhando para a
direita). Animações: parado (respira), andar (4 passos) e falar (boca).

Render: python -m pixelforge render art/examples/cena-demo/viajante.py
"""

from pixelforge import Canvas

NAME = "viajante"
FPS = 4
ANCHOR = [16, 31]                       # ponto entre os pés
ANIMATIONS = {
    "parado": {"frames": [0, 1], "fps": 2},
    "andar": {"frames": [2, 3, 4, 5], "fps": 8},
    "falar": {"frames": [6, 7], "fps": 6},
}

PALETTE = {
    "contorno": "#181425",
    "capa": "#be4a2f",
    "capa_luz": "#d77643",
    "capa_sombra": "#733e39",
    "pele": "#e8b796",
    "pele_sombra": "#c28569",
    "olho": "#181425",
    "calca": "#3a4466",
    "bota": "#3e2731",
    "mochila": "#b86f50",
    "mochila_sombra": "#733e39",
    "lanterna": "#feae34",
    "lanterna_luz": "#fee761",
    "metal": "#5a6988",
}


def figure(bob: int = 0, legs: tuple[int, int] = (0, 0), lift: tuple[int, int] = (0, 0),
           arm: int = 0, mouth: bool = False) -> Canvas:
    """bob: corpo desce 1 px; legs: deslocamento x (frente, trás); lift: pé no ar; arm: balanço."""
    c = Canvas(32, 32, palette=PALETTE)
    hip = 24 + bob

    # pernas (a de trás primeiro, mais escura)
    for (dx, up), color in (((legs[1], lift[1]), "capa_sombra"), ((legs[0], lift[0]), "calca")):
        x = 15 + dx
        c.rect(x, hip, 2, 30 - hip - up, "calca" if color == "calca" else "bota")
        c.rect(x, 29 - up, 3, 2, "bota")

    # mochila nas costas
    c.rect(9, 13 + bob, 5, 9, "mochila")
    c.rect(9, 19 + bob, 5, 3, "mochila_sombra")
    c.line(10, 12 + bob, 12, 12 + bob, "mochila_sombra")

    # capa: trapézio, luz vindo da direita (lanterna)
    c.polygon([(13, 12 + bob), (20, 12 + bob), (23, hip + 1), (11, hip + 1)], "capa")
    with c.only("capa"):
        c.rect(11, 12, 3, 20, "capa_sombra")                          # costas na sombra
        c.line(21, 14 + bob, 23, hip + 1, "capa_luz")                 # frente pega a luz
        c.line(20, 13 + bob, 22, hip + 1, "capa_luz")
        c.line(16, 15 + bob, 15, hip, "capa_sombra")                  # dobra
        c.line(12, 19 + bob, 22, 19 + bob, "capa_sombra")             # cinto
    c.line(12, hip + 1, 23, hip + 1, "capa_sombra")                   # barra

    # cabeça: capuz + rosto de perfil
    c.circle(16.5, 8 + bob, 5, "capa")
    c.polygon([(13, 4 + bob), (9, 10 + bob), (14, 11 + bob)], "capa")  # ponta do capuz caída atrás
    c.rect(17, 6 + bob, 4, 6, "pele")
    c.px(21, 9 + bob, "pele").px(21, 10 + bob, "pele_sombra")
    c.rect(17, 11 + bob, 3, 1, "pele_sombra")
    c.px(19, 8 + bob, "olho")
    if mouth:
        c.px(20, 11 + bob, "olho")
    with c.only("capa"):
        c.rect(9, 3, 5, 9, "capa_sombra")
    c.line(14, 4 + bob, 18, 3 + bob, "capa_luz")
    c.line(15, 12 + bob, 20, 12 + bob, "capa_sombra")                 # gola sob o rosto

    # braço da frente segurando a lanterna
    hand_x, hand_y = 22 + arm, 18 + bob
    c.line(19, 13 + bob, hand_x, hand_y - 1, "capa")
    c.px(hand_x, hand_y, "pele")
    c.line(hand_x + 1, hand_y, hand_x + 1, hand_y + 1, "metal")
    c.rect(hand_x, hand_y + 2, 3, 3, "lanterna")
    c.px(hand_x + 1, hand_y + 3, "lanterna_luz")

    c.outline("contorno")
    return c


def build():
    return [
        figure(),                                   # 0 parado
        figure(bob=1),                              # 1 parado (respira)
        figure(legs=(3, -3), arm=1),                # 2 passo: perna da frente adiante
        figure(bob=-1, legs=(0, 0), lift=(0, 2)),   # 3 cruzando, pé de trás no ar
        figure(legs=(-3, 3), arm=-1),               # 4 passo trocado
        figure(bob=-1, legs=(0, 0), lift=(2, 0)),   # 5 cruzando
        figure(),                                   # 6 falar (boca fechada)
        figure(mouth=True),                         # 7 falar (boca aberta)
    ]
