"""Títulos (cartela de abertura, "Capítulo 7 — ...") e legendas/narração sobre o vídeo.

Os dois usam a fonte bitmap da cena (`font`), em pixel inteiro. O título entra e
sai em degraus de dithering ordenado (sem cores novas); com `fundo` vira cartela
opaca, sem ele fica sobre a cena com sombra. Legendas ficam centralizadas embaixo
(ou em cima), com contorno de 1 px para ler sobre qualquer fundo, e sobem sozinhas
quando a caixa de diálogo ocupa a parte de baixo.
"""

from __future__ import annotations

import numpy as np

from . import font
from .dialog import BORDER, BOX, NAME_TEXT, ui_scale
from .effects import _bayer, _steps
from .script import Caption, Title

TITLE_SCALE = 2          # título em fonte dobrada (sobre a escala da interface)
TITLE_STEPS = 4          # degraus do fade do texto
SIDE = 16                # px de margem lateral do texto
OUTLINE = (24, 20, 37)   # contorno das legendas e sombra do título
OFFSETS = [(dx, dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]


def title_alpha(title: Title, elapsed: float, left: float) -> float:
    """Quanto do texto aparece (0–1, em degraus) `elapsed` s depois de entrar e `left` s antes de sair."""
    if title.fade <= 0:
        return 1.0
    return float(_steps(np.float32(min(1.0, elapsed / title.fade, left / title.fade)), TITLE_STEPS))


def draw_title(canvas: np.ndarray, title: Title, elapsed: float, left: float) -> None:
    h, w = canvas.shape[:2]
    s = ui_scale((w, h))
    big = TITLE_SCALE * s
    if title.background is not None:
        canvas[:] = title.background
    alpha = title_alpha(title, elapsed, left)
    if alpha <= 0:
        return

    width = w - 2 * SIDE * s
    lines = font.wrap(title.text, width, big)
    subs = font.wrap(title.subtitle, width, s) if title.subtitle else []
    gap = 4 * s
    block = len(lines) * font.LINE_HEIGHT * big
    if subs:
        block += 2 * gap + s + len(subs) * font.LINE_HEIGHT * s
    top = (h - block) // 2 if title.position == "centro" else h - 12 * s - block

    layer = canvas.copy()
    shadow = OUTLINE if title.background is None else None
    y = top
    for line in lines:
        font.draw_text(layer, (w - font.text_width(line, big)) // 2, y + font.ASCENT * big, line,
                       title.color, big, shadow=shadow)
        y += font.LINE_HEIGHT * big
    if subs:
        rule = min(max(font.text_width(l, big) for l in lines), w // 2)
        y += gap
        layer[y:y + s, (w - rule) // 2:(w + rule) // 2] = NAME_TEXT
        y += s + gap
        for line in subs:
            font.draw_text(layer, (w - font.text_width(line, s)) // 2, y + font.ASCENT * s, line,
                           BORDER, s, shadow=shadow)
            y += font.LINE_HEIGHT * s

    changed = (layer != canvas).any(axis=2)
    if alpha < 1:
        changed &= _bayer(h, w) < alpha
    canvas[changed] = layer[changed]


def draw_captions(canvas: np.ndarray, captions: list[Caption], dialog_side: str | None = None) -> None:
    """Legendas centralizadas; `dialog_side` ("baixo"/"cima") é onde está a caixa de diálogo."""
    h, w = canvas.shape[:2]
    s = ui_scale((w, h))
    stacks = {"baixo": h - 6 * s, "cima": 6 * s}
    for caption in captions:
        side = caption.position
        if side == dialog_side:
            side = "cima" if side == "baixo" else "baixo"
        lines = font.wrap(caption.text, w - 2 * SIDE * s, s)
        height = len(lines) * font.LINE_HEIGHT * s
        y = stacks[side] - height if side == "baixo" else stacks[side]
        stacks[side] = y - 2 * s if side == "baixo" else y + height + 2 * s
        for line in lines:
            x = (w - font.text_width(line, s)) // 2
            top = y + font.ASCENT * s
            for dx, dy in OFFSETS:
                font.draw_text(canvas, x + dx * s, top + dy * s, line, OUTLINE, s)
            font.draw_text(canvas, x, top, line, caption.color, s)
            y += font.LINE_HEIGHT * s


def dim(canvas: np.ndarray, color=BOX, amount: float = 0.5) -> None:
    """Escurece a tela com dithering ordenado (fundo do close no retrato)."""
    h, w = canvas.shape[:2]
    canvas[_bayer(h, w) < amount] = color
