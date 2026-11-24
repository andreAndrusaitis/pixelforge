"""Seu Geraldo (64 anos, quase 2 m) — sprite chibi de corpo, 64×80, de frente.

Render: python -m pixelforge render art/coletanea/veu/amostra-chibi/geraldo_sprite.py
Quadros: 0 = de chapéu; 1 = sem chapéu, segurando o chapéu no peito. ~76–79 px de altura; pé na linha 79.
"""

import numpy as np

from pixelforge.paint import Paint

NAME = "geraldo_sprite"
W, H = 64, 80
CX = 31.5


def ramps(p: Paint) -> None:
    p.custom_ramp("pele", ["#6b3f2c", "#8a5440", "#a86f52", "#c48a64", "#d6a57e", "#e4bf98"], 3,
                  rim="#d8b49a", outline="#55301f")
    p.custom_ramp("cabelo", ["#8e8a93", "#b4b0b5", "#d2cfcc", "#e6e3dc", "#f6f4ee"], 3, outline="#6f6a72")
    p.custom_ramp("linha", ["#2a1c18", "#3d2a24", "#5a4038"], 1, outline="#1a100d")
    p.custom_ramp("iris", ["#170d0b", "#2e1c14", "#4a2e1d", "#6e4628"], 1)
    p.custom_ramp("branco", ["#9b98a6", "#c3c0c8", "#e2dfe0", "#f6f3ee"], 2)
    p.ramp("chapeu", "#6b4e37", down=3, up=2)
    p.custom_ramp("fita", ["#1f1512", "#33241d", "#4a362a"], 1)
    p.ramp("camisa", "#c9d3dc", down=3, up=1)
    p.ramp("brim", "#3e5577", down=2, up=2)
    p.custom_ramp("cinto", ["#24160f", "#3c2618", "#5a3a26", "#7a5536"], 2)
    p.custom_ramp("fivela", ["#7a6a3c", "#b49a52", "#e3cf8a"], 1)
    p.custom_ramp("botina", ["#120b09", "#1d130f", "#2e211b", "#4a3527", "#7a5c46"], 2, outline="#0b0605")
    p.custom_ramp("cicatriz", ["#c98f74", "#e6b49a", "#f7dccb"], 1)
    p.ramp("boca", "#8e4a42", down=2, up=1)
    p.custom_ramp("brilho", ["#ffffff"], 0)


def hat(p: Paint, cx: float, cy: float, scale: float = 1.0, front_view: bool = True) -> np.ndarray:
    """Chapéu de feltro: aba larga, copa com vinco no topo, fita escura. (cx, cy) = centro da aba."""
    brim = p.ellipse(cx, cy, 18 * scale, 3.4 * scale)
    p.cel(brim, "chapeu", shadow=(3, 1), core=(1, 1), light=(2, 1))
    p.shift(brim & (p.ys >= cy + 1), -1)
    crown = (p.ellipse(cx, cy - 4.5 * scale, 10.5 * scale, 6 * scale) & (p.ys <= cy)) | \
        p.rect(cx - 10 * scale, cy - 5 * scale, cx + 10 * scale, cy - 0.5)
    crown &= ~(p.ellipse(cx, cy - 11.2 * scale, 4 * scale, 2.2 * scale))   # vinco do topo (pinch)
    p.cel(crown, "chapeu", shadow=(4, 1), core=(2, 1), light=(3, 2), rim=True)
    p.set(p.curve([(cx - 3 * scale, cy - 9.5 * scale), (cx, cy - 7.5 * scale), (cx + 3 * scale, cy - 9.5 * scale)], 0.5),
          "chapeu", -2)
    band = crown & (p.ys >= cy - 3 * scale) & (p.ys <= cy - 1)
    p.cel(band, "fita", shadow=(3, 0), core=None, light=(2, 0))
    p.px(int(round(cx - 6 * scale)), int(round(cy - 2)), "fita", 1)            # laço da fita
    return brim | crown


def build():
    return [draw(with_hat=True), draw(with_hat=False)]


def draw(with_hat: bool):
    p = Paint(W, H)
    ramps(p)
    ys, xs = p.ys, p.xs

    # --- botinas engraxadas --------------------------------------------------------------------
    for side in (-1, 1):
        bx = CX + side * 5.8
        boot = (p.ellipse(bx + side * 0.6, 76.5, 6.2, 3.6) & (ys <= 78)) | p.rect(bx - 4, 71, bx + 4, 76)
        p.cel(boot, "botina", shadow=(3, 2), core=(1, 1), light=(2, 2))
        p.set(p.rect(bx - 5.5 + side * 0.6, 78, bx + 6 + side * 0.6, 79) & p.ellipse(bx + side * 0.6, 77, 7, 3.5),
              "botina", -2)                                                        # sola
        p.pixels([(int(bx - 2), 75), (int(bx - 1), 75), (int(bx - 2), 76)], "botina", 2)   # brilho do engraxado
        p.px(int(bx - 1), 74, "brilho", 0)
        p.line(bx - 3, 71, bx + 3, 71, "botina", -1)                                     # cano

    # --- calça de brim ----------------------------------------------------------------------------
    for side in (-1, 1):
        leg = p.poly([(CX + side * 0, 57), (CX + side * 10.5, 57), (CX + side * 9.5, 72), (CX + side * 1, 72)])
        p.cel(leg, "brim", shadow=(3, 0), core=None, light=(2, 0))
        p.line(CX + side * 8.5, 59, CX + side * 8, 71, "brim", 1 if side < 0 else -1)   # costura lateral
        p.line(CX + side * 3, 64, CX + side * 7, 65, "brim", -1)                         # dobra do joelho
        p.line(CX + side * 2.5, 71, CX + side * 9, 71, "brim", -1)                       # barra
    p.line(CX + 0.5, 60, CX + 0.5, 72, "brim", -2)                                      # entreperna
    p.set(p.rect(CX - 1, 57, CX + 1, 60), "brim", -1)

    # --- tronco: ombros largos, barriga, camisa de botão -----------------------------------------
    belly = p.ellipse(CX + 0.5, 50, 16.2, 9.5)
    torso = p.poly([(CX - 15.5, 37), (CX + 15.5, 37), (CX + 14, 58), (CX - 14, 58)]) | \
        p.ellipse(CX, 39.5, 16.8, 5) | belly
    p.cel(torso, "camisa", shadow=(5, 3), core=(2, 2), light=(4, 3), rim=True)
    p.shift(belly & ~p.moved(belly, 0, -2) & (ys >= 52), -1)                             # sob a barriga
    p.shift(p.ellipse(CX - 4, 47, 6, 3) & belly, 1)                                      # luz na barriga
    p.line(CX + 0.5, 37, CX + 0.5, 58, "camisa", -1)                                   # carcela
    for y in (40, 45, 50, 55):
        p.px(int(CX + 1.5), y, "branco", 1)                                              # botões
    for a, b in (((CX - 1, 49), (CX - 5, 48)), ((CX + 2, 49), (CX + 6, 48)), ((CX + 2, 52), (CX + 7, 51))):
        p.line(*a, *b, "camisa", -1)                                                     # repuxado nos botões
    p.line(CX - 10, 42, CX - 7, 45, "camisa", -1)                                       # dobras de tecido
    p.line(CX + 8, 42, CX + 11, 46, "camisa", -2)
    belt = (p.rect(CX - 14, 57, CX + 14, 59) & ~belly) | (p.rect(CX - 14, 57, CX + 14, 58) & (np.abs(xs - CX) > 9))
    p.cel(belt, "cinto", shadow=(3, 0), core=None, light=(2, 0))
    p.cel(p.rect(CX - 1.5, 58, CX + 2.5, 59), "fivela", shadow=(1, 0), core=None, light=None)  # fivela sob a barriga

    # --- braços: manga dobrada, antebraço com cicatriz, mãos enormes ---------------------------
    arms_down = with_hat
    for side in (-1, 1):
        sx = CX + side * 15.5
        if arms_down:
            elbow, wrist = (CX + side * 17.5, 48), (CX + side * 18, 58)
        else:
            elbow, wrist = (CX + side * 17.5, 50), (CX + side * 11, 47)
        sleeve = p.capsule(sx, 39, *elbow, 3.6, 3.2)
        p.cel(sleeve, "camisa", shadow=(2, 1), core=None, light=(1, 1), rim=side > 0)
        fore = p.capsule(elbow[0], elbow[1] + 1, *wrist, 2.9, 2.6)
        p.cel(fore, "pele", shadow=(2, 1), core=None, light=(1, 1))
        # manga dobrada: faixa grossa e clara, com sombra embaixo
        roll = p.ellipse(elbow[0], elbow[1] - 0.5, 4.2, 2.2)
        p.cel(roll, "camisa", shadow=(2, 1), core=None, light=None)
        p.shift(roll & (ys <= elbow[1] - 1), 1)
        p.set(roll & ~p.moved(roll, 0, -1), "camisa", -2)
        p.shift(p.moved(roll, 0, 1) & ~roll & fore, -1, "pele")
        if side > 0:   # cicatriz lisa e brilhante no antebraço esquerdo (direita da tela)
            ex, ey = elbow[0], elbow[1] + 3
            tx, ty = (wrist[0], ey + 5) if arms_down else (ex - 4, ey - 1)
            p.set(p.curve([(ex + 0.5, ey), (tx, ty)], 0.75), "cicatriz", 0)
            p.set(p.curve([(ex + 0.5, ey), ((ex + tx) / 2, (ey + ty) / 2)], 0.45), "cicatriz", 1)
            p.px(int(round(ex)), int(ey + (1 if arms_down else 0)), "brilho", 0, lock=True)
        hx, hy = wrist[0] + (side * 0.5 if arms_down else -side * 1), wrist[1] + (3.5 if arms_down else 0.5)
        hand = p.ellipse(hx, hy, 4.2, 4.6)                                               # mão enorme
        if not arms_down:
            continue
        p.cel(hand, "pele", shadow=(2, 2), core=(1, 1), light=(2, 2))
        for k in range(3):                                                                 # dedos
            p.line(hx - 2 + k * 1.6, hy + 1.5, hx - 2 + k * 1.6, hy + 3.5, "pele", -2)
        p.px(int(round(hx + side * 3.5)), int(round(hy - 1)), "pele", -1)                # polegar

    if not with_hat:   # chapéu no peito, seguro pelas duas mãos
        hat(p, CX, 51, scale=0.78)
        for side in (-1, 1):
            hx, hy = CX + side * 11, 47.5
            hand = p.ellipse(hx, hy, 4.2, 4.6)
            p.cel(hand, "pele", shadow=(2, 2), core=(1, 1), light=(2, 2))
            for k in range(3):
                p.line(hx + side * 0.5 - 1.5 + k * 1.5, hy - 2, hx + side * 0.5 - 1.5 + k * 1.5, hy + 1, "pele", -2)

    # --- pescoço, gola e cabeça ---------------------------------------------------------------------
    neck = p.rect(CX - 5.5, 30, CX + 5.5, 38)
    p.cel(neck, "pele", shadow=(3, 0), core=None, light=None)
    p.shift(neck & (ys <= 34), -1)
    for side in (-1, 1):   # pontas da gola
        p.cel(p.poly([(CX + side * 1, 37), (CX + side * 7.5, 35), (CX + side * 6, 40)]), "camisa",
              shadow=(1, 1), core=None, light=None)
        p.line(CX + side * 1, 37, CX + side * 6, 40, "camisa", -2)
    for side in (-1, 1):
        ear = p.ellipse(CX + side * 13, 19.5, 2.4, 3.4)
        p.cel(ear, "pele", shadow=(1, 1), core=None, light=None)
        p.px(int(round(CX + side * 13.2)), 19, "pele", -2)
    head = p.ellipse(CX, 17.5, 12.8, 13) | p.ellipse(CX, 23, 10.6, 9.6)
    p.cel(head, "pele", shadow=(4, 3), core=(1, 1), light=(3, 3))
    # cabelo branco rente: só nas laterais e nuca quando de chapéu
    cap = p.ellipse(CX, 16.5, 13.4, 13.6)
    dx = np.abs(xs - CX)
    hair = cap & (ys < np.where(dx < 9, 9.5, 12 + (dx - 9) * 2.2)) & ~((dx > 12) & (ys > 17))
    p.cel(hair, "cabelo", shadow=(2, 2), core=None, light=(2, 2))
    for y in range(4, 16, 2):
        for x in range(19 + (y // 2) % 2, 45, 2):
            if hair[y, x]:
                p.shift(p.rect(x, y, x, y), -1)
    # rosto: olhos menores e bondosos, sobrancelha branca, pés de galinha, sulcos leves
    keys = {"k": ("linha", -1), "i": ("iris", 0), "d": ("iris", -1), "w": ("branco", 0), "h": ("brilho", 0)}
    for side, x0 in ((-1, int(CX - 7)), (1, int(CX + 4))):
        p.glyph(x0 - (1 if side < 0 else 0), 18, ["kkkk", "kdhd", "widw", ".ii."], keys, mirror=side > 0)
        p.line(x0 - (0 if side < 0 else 0), 16, x0 + 2, 16 - (side < 0), "cabelo", 0)   # sobrancelha branca
        p.px(x0 + (-2 if side < 0 else 4), 20, "pele", -2)                                  # pé de galinha
    p.pixels([(int(CX), 24), (int(CX + 1), 24)], "pele", -1)                             # nariz largo
    p.px(int(CX + 1), 23, "pele", -1)
    p.px(int(CX - 1), 23, "pele", 1)
    p.set(p.curve([(CX - 2.5, 27.5), (CX, 28), (CX + 2.5, 27.5)], 0.45), "boca", -1)      # sorriso discreto
    p.pixels([(int(CX - 5), 25), (int(CX - 5), 26), (int(CX + 6), 25), (int(CX + 6), 26)], "pele", -1)  # sulcos
    p.shift(p.ellipse(CX + 3, 32, 9, 1.5) & head, -1)
    if with_hat:
        h = hat(p, CX, 9)
        p.shift(p.moved(h, 0, 2) & ~h & head, -1, "pele")                                   # sombra da aba
        p.shift(p.moved(h, 0, 3) & ~h & head & (xs > CX), -1, "pele")
    return p.render()
