"""Retrato do viajante para a caixa de diálogo (48x48): rosto no capuz,
iluminado pela lanterna à direita.

Render: python -m pixelforge render art/examples/cena-demo/retrato_viajante.py
"""

from pixelforge import Canvas

NAME = "retrato_viajante"
PALETTE = {
    "contorno": "#181425",
    "capa": "#be4a2f",
    "capa_luz": "#d77643",
    "capa_sombra": "#733e39",
    "forro": "#3e2731",
    "pele": "#e8b796",
    "pele_luz": "#ead4aa",
    "pele_sombra": "#c28569",
    "cabelo": "#733e39",
    "olho": "#181425",
    "brilho": "#ffffff",
    "boca": "#a22633",
}


def build():
    c = Canvas(48, 48, palette=PALETTE)
    # ombros e capuz
    c.ellipse(24, 50, 22, 12, "capa")
    c.circle(24, 22, 18, "capa")
    c.ellipse(25, 26, 13, 15, "forro")                 # interior escuro do capuz
    with c.only("capa"):
        c.rect(0, 0, 14, 48, "capa_sombra")
        c.line(35, 8, 42, 22, "capa_luz")
        c.line(36, 8, 43, 22, "capa_luz")
        c.line(42, 23, 44, 40, "capa_luz")

    # rosto
    c.ellipse(26, 28, 10, 12, "pele")
    with c.only("pele"):
        c.rect(0, 0, 21, 48, "pele_sombra")            # lado longe da lanterna
        c.ellipse(34, 27, 2.5, 4.5, "pele_luz")
        c.rect(16, 37, 30, 4, "pele_sombra")           # queixo
    # franja saindo do capuz
    c.polygon([(16, 17), (36, 17), (34, 21), (29, 19), (24, 22), (19, 20), (16, 23)], "cabelo")

    # olhos, sobrancelhas, nariz, boca
    for x in (21, 30):
        c.rect(x, 25, 2, 3, "olho")
        c.px(x + 1, 25, "brilho")
        c.line(x - 1, 23, x + 2, 23, "cabelo")
    c.line(27, 28, 27, 31, "pele_sombra")
    c.px(28, 31, "pele_sombra")
    c.line(24, 34, 29, 34, "boca")
    c.px(23, 33, "pele_sombra")

    c.outline("contorno")
    return c
