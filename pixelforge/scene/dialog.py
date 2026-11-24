"""Caixa de diálogo: layout, páginas, máquina de escrever e desenho.

A caixa fica embaixo (ou em cima, `posicao: "cima"`), com até 3 linhas de texto.
Texto maior vira páginas: cada página é digitada letra a letra, espera `pausa`
e dá lugar à seguinte; a última fica `fim` segundos na tela. O retrato (opcional)
fica à esquerda, alinhado à base da caixa, e pode passar da borda de cima.
Com `close: "retrato"` o retrato sai da caixa e vai grande para o meio da tela,
sobre a cena escurecida (corte para o close de quem fala).
Tudo em pixel inteiro; em resoluções altas a fonte e a caixa dobram (escala inteira).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import font
from .script import Line

MAX_LINES = 3
MARGIN = 4
PAD = 5
BOX = (24, 20, 37)        # #181425
BORDER = (192, 203, 220)  # #c0cbdc
INNER = (58, 68, 102)     # #3a4466
TEXT = (255, 255, 255)
NAME_BG = (58, 68, 102)
NAME_TEXT = (254, 174, 52)  # #feae34


def ui_scale(resolution: tuple[int, int]) -> int:
    return max(1, resolution[1] // 180)


@dataclass
class Page:
    lines: list[str]
    start: float          # s, relativo ao início da fala
    typed: float          # s, quando a última letra aparece

    @property
    def chars(self) -> int:
        return sum(len(l) for l in self.lines)


@dataclass
class LinePlan:
    line: Line
    pages: list[Page]
    portrait: np.ndarray | None
    total: float          # s: duração da fala inteira
    closeup: np.ndarray | None = None   # retrato do close (fora da caixa)


def box_extent(resolution: tuple[int, int]) -> int:
    """Altura de tela (px) que a caixa ocupa a partir da borda, contando a aba do nome."""
    s = ui_scale(resolution)
    box_h = 2 * PAD * s + MAX_LINES * font.LINE_HEIGHT * s - font.DESCENT * s
    return MARGIN * s + box_h + (font.CAP + 6) * s


def text_area_width(resolution: tuple[int, int], portrait: np.ndarray | None) -> int:
    s = ui_scale(resolution)
    width = resolution[0] - 2 * MARGIN * s - 2 * PAD * s
    if portrait is not None:
        width -= portrait.shape[1] * s + PAD * s
    return width


def plan_line(line: Line, resolution: tuple[int, int], portrait: np.ndarray | None) -> LinePlan:
    s = ui_scale(resolution)
    width = text_area_width(resolution, portrait)
    if width < 20 * s:
        raise ValueError(f"{line.where}: retrato largo demais para a resolução {resolution[0]}x{resolution[1]}")
    wrapped = font.wrap(line.text, width, s)
    pages, t = [], 0.0
    for i in range(0, len(wrapped), MAX_LINES):
        chunk = wrapped[i:i + MAX_LINES]
        typing = sum(len(l) for l in chunk) / line.speed
        pages.append(Page(chunk, t, t + typing))
        t += typing + line.pause
    total = pages[-1].typed + line.hold
    return LinePlan(line, pages, portrait, total)


@dataclass
class DialogView:
    plan: LinePlan
    page: int
    visible: int          # letras visíveis na página
    done: bool            # página toda digitada
    blink: bool           # indicador ▼ aceso

    @property
    def typing(self) -> bool:
        return not self.done


def view_at(plan: LinePlan, elapsed: float) -> DialogView | None:
    """Estado da fala `elapsed` segundos depois de começar (None = já acabou)."""
    if elapsed < 0 or elapsed >= plan.total:
        return None
    index = 0
    for i, page in enumerate(plan.pages):
        if elapsed >= page.start:
            index = i
    page = plan.pages[index]
    visible = min(page.chars, int((elapsed - page.start) * plan.line.speed + 1e-9))
    done = elapsed >= page.typed
    blink = done and int((elapsed - page.typed) * 2) % 2 == 0
    return DialogView(plan, index, visible, done, blink)


def draw(canvas: np.ndarray, view: DialogView) -> None:
    h, w = canvas.shape[:2]
    s = ui_scale((w, h))
    plan, line = view.plan, view.plan.line
    line_h = font.LINE_HEIGHT * s
    box_w = w - 2 * MARGIN * s
    box_h = 2 * PAD * s + MAX_LINES * line_h - font.DESCENT * s
    x0 = MARGIN * s
    y0 = h - MARGIN * s - box_h if line.position == "baixo" else MARGIN * s
    if plan.closeup is not None:
        _closeup(canvas, plan.closeup, y0, box_h, line.position, s)
    _panel(canvas, x0, y0, box_w, box_h, s)

    text_x = x0 + PAD * s
    if plan.portrait is not None:
        ph, pw = plan.portrait.shape[0] * s, plan.portrait.shape[1] * s
        py = y0 + box_h - PAD * s - ph if line.position == "baixo" else y0 + PAD * s
        _panel(canvas, text_x - s, py - s, pw + 2 * s, ph + 2 * s, s, fill=INNER, rounded=False)
        _paste(canvas, np.repeat(np.repeat(plan.portrait, s, axis=0), s, axis=1), text_x, py)
        text_x += pw + PAD * s

    if line.label:
        tab_w = font.text_width(line.label, s) + 2 * PAD * s
        tab_h = font.CAP * s + 2 * 3 * s
        tab_y = y0 - tab_h + s if line.position == "baixo" else y0 + box_h - s
        _panel(canvas, text_x - PAD * s, tab_y, tab_w, tab_h, s, fill=NAME_BG)
        font.draw_text(canvas, text_x, tab_y + 3 * s, line.label, NAME_TEXT, s)

    remaining = view.visible
    page = plan.pages[view.page]
    for i, text in enumerate(page.lines):
        shown = text[:max(remaining, 0)]
        remaining -= len(text)
        if shown:
            font.draw_text(canvas, text_x, y0 + PAD * s + font.ASCENT * s // 2 + i * line_h, shown, TEXT, s)

    if view.blink:   # ▼ no canto: página pronta
        bx, by = x0 + box_w - PAD * s - 5 * s, y0 + box_h - PAD * s - 3 * s
        for row, (a, b) in enumerate(((0, 5), (1, 4), (2, 3))):
            canvas[by + row * s:by + (row + 1) * s, bx + a * s:bx + b * s] = TEXT


def _closeup(canvas: np.ndarray, portrait: np.ndarray, box_y: int, box_h: int, position: str, s: int) -> None:
    """Retrato ampliado (escala inteira) no espaço livre acima/abaixo da caixa."""
    from .text import dim
    h, w = canvas.shape[:2]
    dim(canvas)
    tab = (font.CAP + 6) * s
    if position == "baixo":
        top, bottom = MARGIN * s, box_y - tab - MARGIN * s
    else:
        top, bottom = box_y + box_h + tab + MARGIN * s, h - MARGIN * s
    ph, pw = portrait.shape[:2]
    k = max(1, min((bottom - top - 4 * s) // ph, (w // 2) // pw))
    big = np.repeat(np.repeat(portrait, k, axis=0), k, axis=1)
    x, y = (w - pw * k) // 2, top + max(0, (bottom - top - ph * k) // 2)
    _panel(canvas, x - 2 * s, y - 2 * s, pw * k + 4 * s, ph * k + 4 * s, s, fill=INNER, rounded=False)
    _paste(canvas, big, x, y)


def _panel(canvas: np.ndarray, x: int, y: int, w: int, h: int, s: int, fill=BOX, rounded: bool = True) -> None:
    """Retângulo com borda clara e filete interno; `rounded` mantém o fundo nos 4 cantos."""
    ch, cw = canvas.shape[:2]
    corners = []
    if rounded:
        for cx, cy in ((x, y), (x + w - s, y), (x, y + h - s), (x + w - s, y + h - s)):
            ya, yb, xa, xb = max(cy, 0), min(cy + s, ch), max(cx, 0), min(cx + s, cw)
            if ya < yb and xa < xb:
                corners.append((ya, yb, xa, xb, canvas[ya:yb, xa:xb].copy()))

    def rect(rx, ry, rw, rh, color):
        xa, ya, xb, yb = max(rx, 0), max(ry, 0), min(rx + rw, cw), min(ry + rh, ch)
        if xa < xb and ya < yb:
            canvas[ya:yb, xa:xb] = color

    rect(x, y, w, h, BORDER)
    rect(x + s, y + s, w - 2 * s, h - 2 * s, INNER)
    rect(x + 2 * s, y + 2 * s, w - 4 * s, h - 4 * s, fill)
    for ya, yb, xa, xb, saved in corners:
        canvas[ya:yb, xa:xb] = saved


def _paste(canvas: np.ndarray, src: np.ndarray, x: int, y: int) -> None:
    from .compose import blit
    blit(canvas, src, x, y)
