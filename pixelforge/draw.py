"""Canvas com primitivas de desenho pixel-perfect (para scripts `.py` de arte).

Exemplo:
    def build():
        c = Canvas(32, palette={"pele": "#ffccaa", "olho": "#1d2b53"})
        c.ellipse(16, 14, 8, 9, "pele")
        c.px(13, 13, "olho")
        c.mirror_x()
        c.outline("#000000")
        return c

Cores podem ser nomes da paleta do canvas, hex (`#rrggbb`) ou tuplas RGB(A).
Coordenadas fora do canvas são ignoradas (recorte automático).
"""

from __future__ import annotations

from contextlib import contextmanager

import numpy as np

from . import process
from .palettes import RGBA, TRANSPARENT, parse_color
from .sprite import Art, Sprite

Color = str | tuple

CHECKER = np.array([[0, 0.5], [0.5, 0]])
BAYER2 = np.array([[0, 2], [3, 1]]) / 4
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16


class Canvas:
    def __init__(self, width: int, height: int | None = None, palette: dict[str, str] | None = None):
        self.sprite = Sprite.blank(width, height)
        self.palette = {name: parse_color(value) for name, value in (palette or {}).items()}
        self._lock: RGBA | None = None

    @property
    def width(self) -> int:
        return self.sprite.width

    @property
    def height(self) -> int:
        return self.sprite.height

    @property
    def pixels(self) -> np.ndarray:
        return self.sprite.pixels

    def color(self, c: Color) -> RGBA:
        if isinstance(c, str) and c in self.palette:
            return self.palette[c]
        return parse_color(c)

    # -- pixels -------------------------------------------------------------

    @contextmanager
    def only(self, c: Color):
        """Trava de cor: dentro do bloco, só pinta sobre pixels da cor `c`.

            with canvas.only("liquido"):
                canvas.gradient(0, 10, 32, 12, ["claro", "medio", "escuro"])
        """
        previous, self._lock = self._lock, self.color(c)
        try:
            yield self
        finally:
            self._lock = previous

    def _paint(self, mask: np.ndarray, c: Color) -> None:
        if self._lock is not None:
            mask = mask & np.all(self.pixels == np.array(self._lock, dtype=np.uint8), axis=-1)
        self.pixels[mask] = self.color(c)

    def px(self, x: int, y: int, c: Color) -> "Canvas":
        if 0 <= x < self.width and 0 <= y < self.height:
            if self._lock is None or self.get(x, y) == self._lock:
                self.pixels[y, x] = self.color(c)
        return self

    def get(self, x: int, y: int) -> RGBA:
        return tuple(int(v) for v in self.pixels[y, x])  # type: ignore[return-value]

    def clear(self, c: Color = "transparent") -> "Canvas":
        self._paint(np.ones((self.height, self.width), dtype=bool), c)
        return self

    # -- formas ---------------------------------------------------------------

    def line(self, x0: int, y0: int, x1: int, y1: int, c: Color) -> "Canvas":
        """Linha de Bresenham (sem anti-aliasing)."""
        color = self.color(c)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.px(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
        return self

    def rect(self, x: int, y: int, w: int, h: int, c: Color, fill: bool = True) -> "Canvas":
        color = self.color(c)
        if fill:
            mask = np.zeros((self.height, self.width), dtype=bool)
            mask[max(y, 0) : max(y + h, 0), max(x, 0) : max(x + w, 0)] = True
            self._paint(mask, color)
        else:
            self.line(x, y, x + w - 1, y, color)
            self.line(x, y + h - 1, x + w - 1, y + h - 1, color)
            self.line(x, y, x, y + h - 1, color)
            self.line(x + w - 1, y, x + w - 1, y + h - 1, color)
        return self

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, c: Color, fill: bool = True) -> "Canvas":
        """Elipse centrada em (cx, cy). Use .5 no centro para larguras pares."""
        inside = self._ellipse_mask(cx, cy, rx, ry)
        if not fill:
            border = np.zeros_like(inside)
            for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                border |= ~process._shifted(inside, dx, dy)
            inside &= border
        self._paint(inside, c)
        return self

    def circle(self, cx: float, cy: float, r: float, c: Color, fill: bool = True) -> "Canvas":
        return self.ellipse(cx, cy, r, r, c, fill)

    def _ellipse_mask(self, cx: float, cy: float, rx: float, ry: float) -> np.ndarray:
        ys, xs = np.mgrid[0 : self.height, 0 : self.width]
        rx, ry = max(rx, 0.5), max(ry, 0.5)
        return ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 <= 1.0 + 1e-9

    def polygon(self, points: list[tuple[int, int]], c: Color, fill: bool = True) -> "Canvas":
        color = self.color(c)
        if fill:
            ys, xs = np.mgrid[0 : self.height, 0 : self.width]
            px, py = xs + 0.5, ys + 0.5
            inside = np.zeros((self.height, self.width), dtype=bool)
            n = len(points)
            for i in range(n):
                (x0, y0), (x1, y1) = points[i], points[(i + 1) % n]
                x0, y0, x1, y1 = x0 + 0.5, y0 + 0.5, x1 + 0.5, y1 + 0.5
                crosses = (y0 > py) != (y1 > py)
                with np.errstate(divide="ignore", invalid="ignore"):
                    x_at = (x1 - x0) * (py - y0) / (y1 - y0) + x0
                inside ^= crosses & (px < x_at)
            self._paint(inside, color)
        for i in range(len(points)):
            (x0, y0), (x1, y1) = points[i], points[(i + 1) % len(points)]
            self.line(x0, y0, x1, y1, color)
        return self

    def fill(self, x: int, y: int, c: Color) -> "Canvas":
        """Balde de tinta (4 vizinhos)."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return self
        target, color = self.get(x, y), self.color(c)
        if target == color:
            return self
        stack = [(x, y)]
        while stack:
            px, py = stack.pop()
            if 0 <= px < self.width and 0 <= py < self.height and self.get(px, py) == target:
                self.pixels[py, px] = color
                stack.extend(((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)))
        return self

    def dither(self, x: int, y: int, w: int, h: int, c1: Color, c2: Color,
               level: float = 0.5, pattern: str = "bayer4") -> "Canvas":
        """Mistura c1/c2 num retângulo. level=0 → só c1; level=1 → só c2.

        pattern: checker | bayer2 | bayer4.
        """
        a, b = self.color(c1), self.color(c2)
        matrix = {"checker": CHECKER, "bayer2": BAYER2, "bayer4": BAYER4}[pattern]
        n = matrix.shape[0]
        for yy in range(max(y, 0), min(y + h, self.height)):
            for xx in range(max(x, 0), min(x + w, self.width)):
                self.px(xx, yy, b if matrix[yy % n, xx % n] < level else a)
        return self

    def gradient(self, x: int, y: int, w: int, h: int, colors: list[Color],
                 vertical: bool = True, pattern: str = "bayer4") -> "Canvas":
        """Rampa de cores em faixas, com dithering nas transições."""
        ramp = [self.color(c) for c in colors]
        if len(ramp) < 2:
            raise ValueError("gradient precisa de pelo menos 2 cores")
        matrix = {"bayer2": BAYER2, "bayer4": BAYER4}[pattern]
        n = matrix.shape[0]
        span = (h if vertical else w) - 1 or 1
        for yy in range(max(y, 0), min(y + h, self.height)):
            for xx in range(max(x, 0), min(x + w, self.width)):
                t = ((yy - y) if vertical else (xx - x)) / span * (len(ramp) - 1)
                i = min(int(t), len(ramp) - 2)
                frac = t - i
                self.px(xx, yy, ramp[i + 1] if matrix[yy % n, xx % n] < frac else ramp[i])
        return self

    # -- transformações -------------------------------------------------------

    def mirror_x(self, left_to_right: bool = True) -> "Canvas":
        """Simetria horizontal: copia a metade esquerda espelhada na direita."""
        half = self.width // 2
        if left_to_right:
            self.pixels[:, self.width - half :] = self.pixels[:, :half][:, ::-1]
        else:
            self.pixels[:, :half] = self.pixels[:, self.width - half :][:, ::-1]
        return self

    def mirror_y(self, top_to_bottom: bool = True) -> "Canvas":
        half = self.height // 2
        if top_to_bottom:
            self.pixels[self.height - half :] = self.pixels[:half][::-1]
        else:
            self.pixels[:half] = self.pixels[self.height - half :][::-1]
        return self

    def shift(self, dx: int = 0, dy: int = 0) -> "Canvas":
        """Desloca o conteúdo (útil para frames de animação). Bordas ficam transparentes."""
        out = np.zeros_like(self.pixels)
        h, w = self.height, self.width
        src = self.pixels[max(-dy, 0) : h - max(dy, 0), max(-dx, 0) : w - max(dx, 0)]
        out[max(dy, 0) : max(dy, 0) + src.shape[0], max(dx, 0) : max(dx, 0) + src.shape[1]] = src
        self.pixels[:] = out
        return self

    def replace(self, old: Color, new: Color) -> "Canvas":
        mask = np.all(self.pixels == np.array(self.color(old), dtype=np.uint8), axis=-1)
        self._paint(mask, new)
        return self

    def outline(self, c: Color, diagonal: bool = False) -> "Canvas":
        self.sprite = process.outline(self.sprite, self.color(c), diagonal)
        return self

    def paste(self, other: "Canvas | Sprite", x: int = 0, y: int = 0) -> "Canvas":
        """Cola outro canvas/sprite por cima (pixels transparentes são ignorados)."""
        src = other.pixels if isinstance(other, (Canvas, Sprite)) else other
        for sy in range(src.shape[0]):
            for sx in range(src.shape[1]):
                if src[sy, sx, 3] > 0:
                    self.px(x + sx, y + sy, tuple(int(v) for v in src[sy, sx]))
        return self

    def copy(self) -> "Canvas":
        clone = Canvas(self.width, self.height)
        clone.palette = dict(self.palette)
        clone.sprite = self.sprite.copy()
        return clone

    def to_art(self, name: str = "art") -> Art:
        return Art(name, [self.sprite.copy()])


__all__ = ["Canvas", "TRANSPARENT", "BAYER2", "BAYER4"]
