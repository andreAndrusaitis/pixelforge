"""A rua de Martim em Goiânia, fim de tarde depois do temporal (cap 01).

Da esquerda para a direita: a padaria da esquina com a luz acesa, a rua
transversal (por onde o homem vira a esquina), casas baixas de muro e laje, a
casa da frente (portão do Bolacha) e, no fim, a casa da avó: muro chapiscado e
portão de grade verde descascando. Calçada molhada, asfalto com poças.
Parallax 1; mundo de 1280x360 (o dobro da tela hd3).
"""

import random

from pixelforge import Canvas

NAME = "rua"
W, H = 1280, 360
BASE = 282          # pé do muro / começo da calçada
CURB = 314          # meio-fio
PALETTE = {
    "contorno": "#2a2235",
    "asfalto": "#34313f", "asfalto_luz": "#4a4656", "asfalto_escuro": "#25222e",
    "poca": "#c98a8a", "poca_luz": "#f7c08a", "poca_ceu": "#7d76a8",
    "calcada": "#8e8288", "calcada_luz": "#a99ca0", "calcada_escura": "#6f6470", "junta": "#5d5361",
    "meiofio": "#b8adae", "meiofio_sombra": "#7a6f78",
    "chapisco": "#c9b79b", "chapisco_luz": "#e2d1b2", "chapisco_sombra": "#a28f78", "chapisco_escuro": "#857260",
    "reboco_rosa": "#d9a39a", "reboco_rosa_s": "#b7827d", "reboco_azul": "#9fb2c8", "reboco_azul_s": "#7f91aa",
    "reboco_verde": "#a9c2a0", "reboco_verde_s": "#87a083", "reboco_amarelo": "#e8cf8f", "reboco_amarelo_s": "#c4aa6f",
    "telha": "#b0584a", "telha_luz": "#d07a5c", "telha_sombra": "#7e3b3c",
    "laje": "#9a8e8e", "laje_luz": "#bdb0ac",
    "caixa": "#4f7fc0", "caixa_luz": "#86b0e3", "caixa_sombra": "#365b93",
    "janela_luz": "#ffd27a", "janela_vidro": "#7a86b0", "grade": "#2f2a3c",
    "porta": "#7a4a3a", "porta_luz": "#9b6248",
    "portao_cinza": "#6e7380", "portao_cinza_luz": "#9aa0ad",
    "quintal": "#3d3548", "quintal_luz": "#564b62",
    "padaria": "#efe0c0", "padaria_s": "#cdb994", "toldo_v": "#c9473f", "toldo_b": "#f3ece0",
    "vitrine": "#ffd98a", "vitrine_luz": "#fff3c4", "pao": "#d88a3c", "pao_s": "#a8622e", "balcao": "#8a5a3c",
    "letreiro": "#2f5f9e", "letra": "#fff3c4",
    "poste": "#7c7a85", "poste_s": "#5a5866", "fio": "#2a2235", "lampada": "#fff1b8",
    "planta": "#4f8a4a", "planta_luz": "#7cb75c", "terra": "#6b4a3a",
    "pingo": "#c6d3ea",
}

FONT = {  # 3x5 para o letreiro
    "P": ["##.", "#.#", "##.", "#..", "#.."], "A": [".#.", "#.#", "###", "#.#", "#.#"],
    "D": ["##.", "#.#", "#.#", "#.#", "##."], "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "I": ["###", ".#.", ".#.", ".#.", "###"],
}


def text(c: Canvas, x: int, y: int, s: str, color: str) -> None:
    for ch in s:
        for j, row in enumerate(FONT[ch]):
            for i, k in enumerate(row):
                if k == "#":
                    c.px(x + i, y + j, color)
        x += 4


def chapisco(c: Canvas, x: int, y: int, w: int, h: int, rnd: random.Random) -> None:
    c.rect(x, y, w, h, "chapisco")
    for _ in range(w * h // 5):
        c.px(x + rnd.randrange(w), y + rnd.randrange(h),
             rnd.choice(["chapisco_luz", "chapisco_sombra", "chapisco_sombra", "chapisco_escuro"]))
    c.line(x, y, x + w - 1, y, "chapisco_luz")                  # capa do muro
    c.line(x, y + 1, x + w - 1, y + 1, "chapisco_luz")
    c.line(x, y + 2, x + w - 1, y + 2, "chapisco_sombra")
    for yy in range(y + h - 10, y + h):                         # respingo da chuva no pé
        for xx in range(x, x + w):
            if rnd.random() < 0.35:
                c.px(xx, yy, "chapisco_escuro")


def caixa_dagua(c: Canvas, x: int, y: int) -> None:
    c.rect(x, y, 22, 16, "caixa")
    c.rect(x + 16, y, 6, 16, "caixa_sombra")
    c.rect(x + 2, y + 1, 3, 13, "caixa_luz")
    c.rect(x - 2, y - 4, 26, 4, "caixa_luz")
    c.line(x - 2, y - 1, x + 23, y - 1, "caixa_sombra")
    c.rect(x + 8, y - 6, 6, 2, "caixa_sombra")


def varal(c: Canvas, x0: int, x1: int, y: int, rnd: random.Random) -> None:
    c.line(x0, y - 10, x0, y + 6, "poste_s")
    c.line(x1, y - 10, x1, y + 6, "poste_s")
    c.line(x0, y - 9, x1, y - 8, "fio")
    x = x0 + 4
    while x < x1 - 8:
        w = rnd.randint(5, 9)
        col = rnd.choice(["toldo_v", "reboco_azul", "reboco_amarelo", "toldo_b", "reboco_verde"])
        c.rect(x, y - 8, w, rnd.randint(7, 12), col)
        c.line(x, y - 8, x + w - 1, y - 8, "fio")
        x += w + rnd.randint(2, 5)


def janela(c: Canvas, x: int, y: int, w: int, h: int, acesa: bool) -> None:
    c.rect(x - 2, y - 2, w + 4, h + 4, "chapisco_luz")
    c.rect(x, y, w, h, "janela_luz" if acesa else "janela_vidro")
    if not acesa:
        c.line(x + 1, y + 1, x + 3, y + 1, "pingo")
    for gx in range(x + 3, x + w, 4):
        c.line(gx, y, gx, y + h - 1, "grade")
    c.line(x, y + h // 2, x + w - 1, y + h // 2, "grade")
    c.rect(x - 3, y + h + 2, w + 6, 2, "chapisco_sombra")


def casa(c: Canvas, x: int, w: int, cor: str, rnd: random.Random, laje: bool, acesa: bool) -> None:
    top = BASE - 112
    c.rect(x, top, w, BASE - top, cor)
    c.rect(x + w - 6, top, 6, BASE - top, cor + "_s")
    for _ in range(w * 4):                                      # textura de reboco
        c.px(x + rnd.randrange(w), top + rnd.randrange(BASE - top), cor + "_s")
    if laje:
        c.rect(x - 3, top - 6, w + 6, 6, "laje")
        c.line(x - 3, top - 6, x + w + 2, top - 6, "laje_luz")
        caixa_dagua(c, x + rnd.randint(6, w - 30), top - 22)
        if rnd.random() < 0.7:
            varal(c, x + 4, x + w - 6, top - 10, rnd)
    else:
        c.polygon([(x - 8, top + 2), (x + w // 2, top - 30), (x + w + 7, top + 2)], "telha")
        half = w / 2 + 8
        for i in range(4, 30, 5):                               # fiadas de telha, dentro do triângulo
            inset = round(i * half / 32)
            c.line(x - 8 + inset + 1, top + 2 - i, x + w + 7 - inset - 1, top + 2 - i, "telha_luz")
        c.line(x - 8, top + 2, x + w // 2, top - 30, "telha_luz")
        c.line(x + w // 2, top - 30, x + w + 7, top + 2, "telha_sombra")
    janela(c, x + 12, top + 26, 22, 18, acesa)


def poste(c: Canvas, x: int) -> None:
    c.rect(x, 70, 5, BASE - 70 + 8, "poste")
    c.rect(x + 3, 70, 2, BASE - 70 + 8, "poste_s")
    c.rect(x - 14, 78, 34, 3, "poste_s")
    c.rect(x + 4, 92, 20, 3, "poste_s")
    c.rect(x + 20, 95, 7, 4, "poste")
    c.rect(x + 21, 99, 5, 2, "lampada")


def padaria(c: Canvas, x: int, rnd: random.Random) -> None:
    top = BASE - 130
    c.rect(x, top, 220, BASE - top, "padaria")
    c.rect(x + 214, top, 6, BASE - top, "padaria_s")
    for _ in range(1600):
        c.px(x + rnd.randrange(220), top + rnd.randrange(BASE - top), "padaria_s")
    c.rect(x - 4, top - 6, 228, 6, "laje")
    c.line(x - 4, top - 6, x + 223, top - 6, "laje_luz")
    caixa_dagua(c, x + 150, top - 22)
    c.rect(x + 40, top + 10, 120, 18, "letreiro")
    c.rect(x + 41, top + 11, 118, 1, "reboco_azul")
    text(c, x + 86, top + 16, "PADARIA", "letra")
    for i in range(0, 220, 10):                                   # toldo listrado
        cor = "toldo_v" if (i // 10) % 2 == 0 else "toldo_b"
        c.rect(x + i, top + 40, 10, 14, cor)
        c.polygon([(x + i, top + 54), (x + i + 9, top + 54), (x + i + 5, top + 58)], cor)
    c.line(x, top + 40, x + 219, top + 40, "telha_sombra")
    c.rect(x + 12, top + 66, 140, BASE - top - 74, "vitrine")      # vitrine acesa
    c.rect(x + 14, top + 68, 136, 8, "vitrine_luz")
    for row, yy in enumerate([top + 84, top + 100]):              # prateleiras de pão
        c.line(x + 14, yy + 7, x + 149, yy + 7, "balcao")
        for i in range(10):
            px = x + 20 + i * 13 + row * 6
            c.ellipse(px, yy + 4, 5, 3, "pao")
            c.line(px - 3, yy + 2, px + 2, yy + 2, "vitrine_luz")
            c.line(px - 4, yy + 6, px + 4, yy + 6, "pao_s")
    c.rect(x + 12, BASE - 22, 140, 14, "balcao")
    c.rect(x + 166, top + 66, 40, BASE - top - 66, "porta")        # porta de enrolar aberta
    c.rect(x + 168, top + 68, 36, BASE - top - 68, "vitrine")
    c.rect(x + 166, top + 62, 40, 4, "poste_s")


def calcada_e_asfalto(c: Canvas, rnd: random.Random) -> None:
    c.rect(0, BASE, W, CURB - BASE, "calcada")
    for x in range(0, W + 8, 24):                                 # juntas da calçada
        c.line(x, BASE + 1, x - 8, CURB - 1, "junta")
    c.line(0, BASE, W - 1, BASE, "calcada_escura")
    c.line(0, BASE + 1, W - 1, BASE + 1, "calcada_luz")
    for _ in range(2200):
        c.px(rnd.randrange(W), rnd.randrange(BASE + 2, CURB), rnd.choice(["calcada_luz", "calcada_escura"]))
    c.rect(0, CURB, W, 4, "meiofio")
    c.line(0, CURB + 4, W - 1, CURB + 4, "meiofio_sombra")
    c.rect(0, CURB + 5, W, H - CURB - 5, "asfalto")
    for _ in range(5000):
        c.px(rnd.randrange(W), rnd.randrange(CURB + 5, H), rnd.choice(["asfalto_luz", "asfalto_escuro"]))
    for px, w in [(60, 70), (300, 46), (520, 90), (790, 60), (1000, 110), (1200, 50)]:   # poças
        y = rnd.randint(CURB + 14, H - 14)
        c.ellipse(px, y, w // 2, 5, "poca_ceu")
        c.ellipse(px, y + 1, w // 2 - 4, 3, "poca")
        c.line(px - w // 4, y, px + w // 5, y, "poca_luz")
    for px, w in [(130, 28), (660, 22), (930, 30)]:              # poça na calçada
        c.ellipse(px, BASE + 18, w // 2, 3, "poca_ceu")
        c.line(px - w // 4, BASE + 18, px + w // 6, BASE + 18, "poca_luz")


def build() -> Canvas:
    rnd = random.Random(11)
    c = Canvas(W, H, palette=PALETTE)
    calcada_e_asfalto(c, rnd)
    padaria(c, 0, rnd)
    # rua transversal (a esquina): asfalto subindo entre a padaria e a primeira casa
    c.polygon([(214, BASE), (306, BASE), (276, 214), (244, 214)], "calcada_escura")
    c.polygon([(222, BASE), (298, BASE), (272, 214), (248, 214)], "asfalto_luz")
    for y in range(218, BASE, 4):                                 # textura que afina com a distância
        for _ in range(3):
            c.px(rnd.randint(250 - (y - 214) // 3, 270 + (y - 214) // 3), y, "asfalto_escuro")
    for y0 in range(220, BASE, 14):                               # faixa amarela tracejada
        k = (y0 - 214) // 20
        c.rect(259, y0, 2, 3 + k, "janela_luz")
    c.ellipse(268, BASE - 14, 10, 2, "poca_ceu")
    c.line(262, BASE - 14, 270, BASE - 14, "poca_luz")
    poste(c, 304)
    cores = ["reboco_rosa", "reboco_azul", "reboco_amarelo", "reboco_verde"]
    x, i = 320, 0
    while x < 930:
        w = rnd.randint(92, 118)
        w = min(w, 940 - x) if 940 - x > 60 else w
        casa(c, x, w, cores[i % 4], rnd, laje=(i % 3 != 1), acesa=(i == 2))
        chapisco(c, x - 2, BASE - 52, w + 4, 52, rnd)
        if 700 <= x <= 840:                                       # casa da frente: portão do Bolacha
            c.rect(x + 30, BASE - 56, 44, 56, "quintal")
            for gx in range(x + 31, x + 74, 5):
                c.line(gx, BASE - 56, gx, BASE - 1, "portao_cinza")
                c.px(gx, BASE - 57, "portao_cinza_luz")
            c.rect(x + 30, BASE - 59, 44, 3, "portao_cinza_luz")
            c.rect(x + 30, BASE - 30, 44, 2, "portao_cinza")
        else:
            c.rect(x + w - 32, BASE - 70, 22, 70, "porta")         # portãozinho de chapa
            c.rect(x + w - 30, BASE - 68, 18, 66, "porta_luz")
            c.line(x + w - 21, BASE - 68, x + w - 21, BASE - 3, "porta")
        if rnd.random() < 0.5:                                    # vaso de planta
            px = x + 8
            c.rect(px, BASE - 10, 10, 10, "terra")
            c.ellipse(px + 5, BASE - 15, 8, 6, "planta")
            c.ellipse(px + 4, BASE - 17, 4, 3, "planta_luz")
        x += w + 4
        i += 1
    poste(c, 948)
    # casa da avó: fachada, laje com caixa d'água, muro chapiscado e vão do portão
    casa(c, 962, 210, "reboco_azul", rnd, laje=True, acesa=False)
    chapisco(c, 958, BASE - 64, 230, 64, rnd)
    c.rect(1022, BASE - 66, 64, 66, "quintal")
    c.rect(1022, BASE - 66, 64, 8, "quintal_luz")
    c.rect(1018, BASE - 72, 4, 72, "chapisco_sombra")             # pilares
    c.rect(1086, BASE - 72, 4, 72, "chapisco_sombra")
    c.rect(1017, BASE - 74, 6, 3, "chapisco_luz")
    c.rect(1085, BASE - 74, 6, 3, "chapisco_luz")
    c.rect(1190, BASE - 120, 90, 120, "reboco_rosa")              # vizinho do fim
    chapisco(c, 1188, BASE - 52, 92, 52, rnd)
    for y0, y1 in [(80, 86), (94, 98)]:                           # fios elétricos
        c.line(0, y0 + 10, 304, y0, "fio")
        c.line(309, y0, 948, y1, "fio")
        c.line(953, y1, W - 1, y1 + 6, "fio")
    return c
