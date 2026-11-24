"""Fonte bitmap embutida (5×7, largura variável) com os acentos do português.

Cada glifo é uma grade de linhas: 0–6 é a altura das maiúsculas, 7–8 são as
descendentes (g, j, p, q, y, vírgula, cedilha). Minúsculas têm altura-x 5 (linhas
2–6) e recebem o acento nas linhas −1 e 0; maiúsculas acentuadas usam duas linhas
acima (−2 e −1), que caem no espaço entre linhas. Letras acentuadas são montadas
de letra-base + acento, então qualquer combinação nova custa uma linha da tabela.
"""

from __future__ import annotations

import numpy as np

CAP = 7            # altura das maiúsculas
ASCENT = 2         # linhas acima, para acentos de maiúsculas
DESCENT = 2
LINE_HEIGHT = CAP + DESCENT + ASCENT    # 11 px por linha de texto
SPACING = 1        # px entre letras
SPACE = 3          # largura do espaço

_G = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "J": ["..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "a": [".....", ".....", ".###.", "....#", ".####", "#...#", ".####"],
    "b": ["#....", "#....", "####.", "#...#", "#...#", "#...#", "####."],
    "c": ["....", "....", ".###", "#...", "#...", "#...", ".###"],
    "d": ["....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"],
    "e": [".....", ".....", ".###.", "#...#", "#####", "#....", ".###."],
    "f": ["..##", ".#..", "###.", ".#..", ".#..", ".#..", ".#.."],
    "g": [".....", ".....", ".####", "#...#", "#...#", "#...#", ".####", "....#", ".###."],
    "h": ["#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"],
    "i": ["#", ".", "#", "#", "#", "#", "#"],
    "ı": [".", ".", "#", "#", "#", "#", "#"],            # i sem pingo (base de í, ì, î)
    "j": ["..#", "...", ".##", "..#", "..#", "..#", "..#", "..#", "##."],
    "k": ["#...", "#...", "#..#", "#.#.", "##..", "#.#.", "#..#"],
    "l": ["##.", ".#.", ".#.", ".#.", ".#.", ".#.", "..#"],
    "m": [".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"],
    "n": ["....", "....", "###.", "#..#", "#..#", "#..#", "#..#"],
    "o": ["....", "....", ".##.", "#..#", "#..#", "#..#", ".##."],
    "p": ["....", "....", "###.", "#..#", "#..#", "#..#", "###.", "#...", "#..."],
    "q": ["....", "....", ".###", "#..#", "#..#", "#..#", ".###", "...#", "...#"],
    "r": ["...", "...", "#.#", "##.", "#..", "#..", "#.."],
    "s": ["....", "....", ".###", "#...", ".##.", "...#", "###."],
    "t": [".#..", ".#..", "###.", ".#..", ".#..", ".#..", "..##"],
    "u": ["....", "....", "#..#", "#..#", "#..#", "#..#", ".###"],
    "v": [".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "w": [".....", ".....", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#."],
    "x": ["....", "....", "#..#", "#..#", ".##.", "#..#", "#..#"],
    "y": ["....", "....", "#..#", "#..#", "#..#", "#..#", ".###", "...#", ".##."],
    "z": ["....", "....", "####", "...#", ".##.", "#...", "####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": [".#.", "##.", ".#.", ".#.", ".#.", ".#.", "###"],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    ".": [".", ".", ".", ".", ".", ".", "#"],
    ",": ["..", "..", "..", "..", "..", "..", ".#", "#."],
    "!": ["#", "#", "#", "#", "#", ".", "#"],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    ":": [".", ".", ".", "#", ".", ".", "#"],
    ";": ["..", "..", "..", ".#", "..", "..", ".#", "#."],
    "-": ["...", "...", "...", "...", "###", "...", "..."],
    "—": [".....", ".....", ".....", ".....", "#####", ".....", "....."],
    "'": ["#", "#"],
    '"': ["#.#", "#.#"],
    "(": [".#", "#.", "#.", "#.", "#.", "#.", ".#"],
    ")": ["#.", ".#", ".#", ".#", ".#", ".#", "#."],
    "/": ["....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."],
    "…": [".....", ".....", ".....", ".....", ".....", ".....", "#.#.#"],
    "+": [".....", ".....", "..#..", "..#..", "#####", "..#..", "..#.."],
    "=": ["....", "....", "....", "####", "....", "####", "...."],
    "*": [".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."],
    "%": ["##..#", "##..#", "...#.", "..#..", ".#...", "#..##", "#..##"],
    "#": [".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."],
    "_": [".....", ".....", ".....", ".....", ".....", ".....", ".....", "#####"],
    "«": [".....", ".....", "..#.#", ".#.#.", "#.#..", ".#.#.", "..#.#"],
    "»": [".....", ".....", "#.#..", ".#.#.", "..#.#", ".#.#.", "#.#.."],
    "¿": ["..#..", ".....", "..#..", ".#...", "#....", "#...#", ".###."],
    "¡": ["#", ".", "#", "#", "#", "#", "#"],
}

# acentos: (linhas, deslocamento extra em x)
_ACCENTS = {
    "agudo": ["..#", ".#."],
    "grave": ["#..", ".#."],
    "circunflexo": [".#.", "#.#"],
    "til": [".#.#", "#.#."],
    "trema": ["...", "#.#"],
}
_COMPOSED = {
    "á": ("a", "agudo"), "à": ("a", "grave"), "â": ("a", "circunflexo"), "ã": ("a", "til"), "ä": ("a", "trema"),
    "é": ("e", "agudo"), "è": ("e", "grave"), "ê": ("e", "circunflexo"), "ë": ("e", "trema"),
    "í": ("ı", "agudo"), "ì": ("ı", "grave"), "î": ("ı", "circunflexo"), "ï": ("ı", "trema"),
    "ó": ("o", "agudo"), "ò": ("o", "grave"), "ô": ("o", "circunflexo"), "õ": ("o", "til"), "ö": ("o", "trema"),
    "ú": ("u", "agudo"), "ù": ("u", "grave"), "û": ("u", "circunflexo"), "ü": ("u", "trema"),
    "ñ": ("n", "til"),
    "Á": ("A", "agudo"), "À": ("A", "grave"), "Â": ("A", "circunflexo"), "Ã": ("A", "til"), "Ä": ("A", "trema"),
    "É": ("E", "agudo"), "È": ("E", "grave"), "Ê": ("E", "circunflexo"), "Ë": ("E", "trema"),
    "Í": ("I", "agudo"), "Ì": ("I", "grave"), "Î": ("I", "circunflexo"), "Ï": ("I", "trema"),
    "Ó": ("O", "agudo"), "Ò": ("O", "grave"), "Ô": ("O", "circunflexo"), "Õ": ("O", "til"), "Ö": ("O", "trema"),
    "Ú": ("U", "agudo"), "Ù": ("U", "grave"), "Û": ("U", "circunflexo"), "Ü": ("U", "trema"),
    "Ñ": ("N", "til"),
}
_ALIASES = {"“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", " ": " "}


class Glyph:
    __slots__ = ("width", "pixels")

    def __init__(self, width: int, pixels: list[tuple[int, int]]):
        self.width = width          # avanço sem o espaçamento
        self.pixels = pixels        # (x, y) com y relativo ao topo das maiúsculas


def _from_rows(rows: list[str], top: int = 0) -> list[tuple[int, int]]:
    return [(x, y + top) for y, row in enumerate(rows) for x, ch in enumerate(row) if ch == "#"]


def _build() -> dict[str, Glyph]:
    glyphs = {ch: Glyph(len(rows[0]), _from_rows(rows)) for ch, rows in _G.items()}
    for ch, (base, accent) in _COMPOSED.items():
        g = glyphs[base]
        rows = _ACCENTS[accent]
        width = max(g.width, len(rows[0]))
        dx = (width - len(rows[0]) + 1) // 2
        bx = (width - g.width) // 2
        top = -2 if base.isupper() else -1    # minúsculas: 1 linha de folga sobre a altura-x
        accent_px = [(x + dx, y) for x, y in _from_rows(rows, top)]
        glyphs[ch] = Glyph(width, [(x + bx, y) for x, y in g.pixels] + accent_px)
    for ch, base in (("ç", "c"), ("Ç", "C")):
        g = glyphs[base]
        cx = (g.width - 2) // 2 + 1
        glyphs[ch] = Glyph(g.width, g.pixels + [(cx, 7), (cx - 1, 8)])
    return glyphs


GLYPHS = _build()
FALLBACK = GLYPHS["?"]


def glyph(ch: str) -> Glyph:
    ch = _ALIASES.get(ch, ch)
    return GLYPHS.get(ch, FALLBACK)


def text_width(text: str, scale: int = 1) -> int:
    width = 0
    for i, ch in enumerate(text):
        width += SPACE if ch == " " else glyph(ch).width
        if i < len(text) - 1:
            width += SPACING
    return width * scale


def draw_text(canvas: np.ndarray, x: int, y: int, text: str, color, scale: int = 1,
              shadow=None) -> int:
    """Escreve `text` com o topo das maiúsculas em `y`. Devolve a largura usada.
    `shadow`: cor de uma sombra 1 px abaixo/à direita (legibilidade)."""
    if shadow is not None:
        draw_text(canvas, x + scale, y + scale, text, shadow, scale)
    h, w = canvas.shape[:2]
    cx = x
    color = np.array(color[:3], dtype=np.uint8)
    for ch in text:
        if ch == " ":
            cx += (SPACE + SPACING) * scale
            continue
        g = glyph(ch)
        for gx, gy in g.pixels:
            px, py = cx + gx * scale, y + gy * scale
            x0, y0, x1, y1 = max(px, 0), max(py, 0), min(px + scale, w), min(py + scale, h)
            if x0 < x1 and y0 < y1:
                canvas[y0:y1, x0:x1, :3] = color
        cx += (g.width + SPACING) * scale
    return cx - x


def wrap(text: str, max_width: int, scale: int = 1) -> list[str]:
    """Quebra por palavras (e em `\\n`); palavra maior que a linha é cortada."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}" if current else word
            if text_width(candidate, scale) <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            while text_width(word, scale) > max_width:
                cut = len(word)
                while cut > 1 and text_width(word[:cut], scale) > max_width:
                    cut -= 1
                lines.append(word[:cut])
                word = word[cut:]
            current = word
        lines.append(current)
    return lines
