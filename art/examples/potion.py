"""Poção 32x32 desenhada com primitivas — exemplo de script para artes maiores.

Render: python -m pixelforge render art/examples/potion.py
"""

from pixelforge import Canvas

PALETTE = {
    "contorno": "#1a1c2c",
    "vidro": "#94b0c2",
    "vidro_escuro": "#566c86",
    "brilho": "#f4f4f4",
    "liquido_escuro": "#5d275d",
    "liquido": "#b13e53",
    "liquido_claro": "#ef7d57",
    "rolha": "#a46422",
    "rolha_escura": "#6b3d1f",
}


def build():
    c = Canvas(32, palette=PALETTE)

    # frasco: corpo redondo + gargalo
    c.circle(15.5, 20, 10, "vidro")
    c.rect(12, 5, 8, 7, "vidro")

    # líquido: abaixo da linha y=15, rampa clara → escura (luz vem de cima)
    c.circle(15.5, 20, 8.5, "liquido")
    with c.only("liquido"):
        c.rect(0, 0, 32, 15, "vidro")
        c.gradient(0, 15, 32, 14, ["liquido_claro", "liquido", "liquido_escuro"])

    # sombra do vidro à direita, brilho à esquerda (luz no canto superior esquerdo)
    with c.only("vidro"):
        c.rect(22, 0, 10, 32, "vidro_escuro")
        c.rect(18, 5, 2, 7, "vidro_escuro")
    c.line(9, 15, 8, 18, "brilho")
    c.line(13, 7, 13, 9, "brilho")

    # rolha
    c.rect(12, 2, 8, 4, "rolha")
    c.rect(12, 5, 8, 1, "rolha_escura")

    c.outline("contorno")
    return c
