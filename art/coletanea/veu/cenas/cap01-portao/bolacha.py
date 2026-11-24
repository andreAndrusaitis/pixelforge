"""Bolacha, o vira-lata caramelo da casa da frente (cap 01): magrelo, uma orelha
em pé e a outra caída. Olhando para a direita.

Animações: parado (respira, rabo abana), latir (pula na grade, boca aberta) e
sentado (senta, fecha a boca e bate o rabo no chão).
"""

from pixelforge import Canvas

NAME = "bolacha"
FPS = 8
W, H = 36, 30
ANCHOR = [18, 29]
ANIMATIONS = {
    "parado": {"frames": [0, 1, 2, 1], "fps": 6},
    "latir": {"frames": [3, 4, 5, 4], "fps": 10},
    "sentado": {"frames": [6, 7], "fps": 5},
}

PALETTE = {
    "contorno": "#4a2a1c",
    "pelo": "#c98a4b", "pelo_luz": "#e8b06a", "pelo_brilho": "#f6d29a", "pelo_s": "#9a6234",
    "pelo_escuro": "#6b3f26", "branco": "#f1e3c8", "focinho": "#2a1d1a",
    "olho": "#1a1210", "brilho": "#ffffff", "lingua": "#e0707a", "boca": "#5a2a2a",
}


def dog(tail: int = 0, breath: int = 0, bark: int = 0, sit: bool = False) -> Canvas:
    """tail: -1/0/1 posição do rabo; breath: barriga 1 px; bark: 0 fechado, 1 aberto, 2 pulo."""
    c = Canvas(W, H, palette=PALETTE)
    lift = 2 if bark == 2 else 0
    if sit:
        # traseiro no chão, peito alto
        c.ellipse(13, 23, 7, 5, "pelo")                                  # anca
        c.ellipse(12, 21, 5, 3, "pelo_luz")
        c.ellipse(19, 18 - lift, 5, 7, "pelo")                           # peito
        c.ellipse(21, 19, 2, 4, "branco")
        for lx in (18, 22):                                              # patas da frente
            c.rect(lx, 22, 2, 7, "pelo")
            c.px(lx, 28, "pelo_escuro")
        c.rect(8, 27, 7, 2, "pelo_s")                                    # pata de trás
        tx = 6
        c.line(tx, 28, tx - 4, 28 - (1 if tail else 0), "pelo")         # rabo batendo no chão
        c.line(tx - 1, 27, tx - 3, 27 - tail, "pelo_luz")
        hx, hy = 23, 9 - lift
    else:
        # corpo comprido e magro
        c.ellipse(16, 18 - lift + breath, 9, 4, "pelo")
        c.ellipse(15, 16 - lift, 7, 2, "pelo_luz")
        c.line(9, 21 - lift, 21, 21 - lift + breath, "pelo_s")             # barriga
        for i in range(10, 20, 3):                                       # costelas de magrelo
            c.px(i, 19 - lift, "pelo_s")
        legs = [(9, 0), (12, 1), (20, 0), (23, 1)]
        for lx, far in legs:
            top = 20 - lift
            c.rect(lx, top, 2, H - 1 - top - (lift if bark == 2 and lx > 18 else 0),
                   "pelo_s" if far else "pelo")
            c.px(lx, H - 2 - (lift if bark == 2 and lx > 18 else 0), "branco")
        # rabo para cima, abanando
        base = (7, 16 - lift)
        tip = (2 + tail, 9 - lift + abs(tail))
        c.line(base[0], base[1], tip[0], tip[1], "pelo")
        c.line(base[0] + 1, base[1], tip[0] + 1, tip[1] + 1, "pelo_s")
        c.px(tip[0], tip[1], "pelo_brilho")
        hx, hy = 26, 11 - lift
    # pescoço e cabeça
    c.ellipse(hx - 3, hy + 5, 3, 4, "pelo")
    c.ellipse(hx, hy, 5, 4, "pelo")
    c.ellipse(hx - 1, hy - 1, 3, 2, "pelo_luz")
    c.px(hx - 2, hy - 2, "pelo_brilho")
    # focinho comprido
    c.rect(hx + 3, hy, 5, 3, "pelo")
    c.rect(hx + 4, hy + 2, 4, 1, "branco")
    c.rect(hx + 7, hy - 1, 2, 2, "focinho")
    if bark:
        c.rect(hx + 3, hy + 3, 5, 2, "boca")                             # boca aberta
        c.px(hx + 5, hy + 4, "lingua")
        c.px(hx + 6, hy + 4, "lingua")
        c.rect(hx + 4, hy + 5, 4, 1, "pelo")                             # queixo caído
    # olho
    c.px(hx + 1, hy - 1, "olho")
    c.px(hx + 2, hy - 1, "olho")
    c.px(hx + 1, hy - 2, "brilho")
    # orelha em pé (a de trás) e orelha caída (a da frente)
    c.polygon([(hx - 2, hy - 3), (hx, hy - 9), (hx + 1, hy - 3)], "pelo_s")
    c.px(hx, hy - 7, "pelo_escuro")
    c.polygon([(hx - 3, hy - 3), (hx - 6, hy - 1), (hx - 5, hy + 3), (hx - 2, hy)], "pelo_escuro")
    c.px(hx - 4, hy - 1, "pelo_s")
    c.outline("contorno")
    return c


def build():
    return [
        dog(tail=0), dog(tail=1, breath=1), dog(tail=-1),       # parado
        dog(bark=1), dog(bark=2, tail=1), dog(bark=1, tail=-1),  # latir
        dog(sit=True, tail=0), dog(sit=True, tail=1),           # sentado
    ]
