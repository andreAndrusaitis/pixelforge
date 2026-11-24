"""Pós-processamento de sprites: contorno, limpeza e recorte."""

from __future__ import annotations

from collections import Counter

import numpy as np

from .palettes import RGBA
from .sprite import Sprite

_N4 = ((0, -1), (-1, 0), (1, 0), (0, 1))
_N8 = _N4 + ((-1, -1), (1, -1), (-1, 1), (1, 1))


def _shifted(mask: np.ndarray, dx: int, dy: int) -> np.ndarray:
    """mask deslocada: resultado[y, x] = mask[y + dy, x + dx] (fora = False)."""
    h, w = mask.shape
    out = np.zeros_like(mask)
    ys, yd = (slice(dy, h), slice(0, h - dy)) if dy >= 0 else (slice(0, h + dy), slice(-dy, h))
    xs, xd = (slice(dx, w), slice(0, w - dx)) if dx >= 0 else (slice(0, w + dx), slice(-dx, w))
    out[yd, xd] = mask[ys, xs]
    return out


def outline(sprite: Sprite, color: RGBA, diagonal: bool = False) -> Sprite:
    """Pinta de `color` os pixels transparentes vizinhos a pixels opacos."""
    opaque = sprite.pixels[..., 3] > 0
    near = np.zeros_like(opaque)
    for dx, dy in _N8 if diagonal else _N4:
        near |= _shifted(opaque, dx, dy)
    result = sprite.copy()
    result.pixels[near & ~opaque] = color
    return result


def cleanup(sprite: Sprite, passes: int = 1, threshold: int = 6) -> Sprite:
    """Remove pixels órfãos (sem vizinho ortogonal da mesma cor).

    Um órfão só é substituído quando pelo menos `threshold` dos 8 vizinhos
    compartilham a mesma cor, o que preserva detalhes intencionais como olhos.
    """
    result = sprite.copy()
    h, w = result.height, result.width
    for _ in range(passes):
        src = result.pixels.copy()
        changed = False
        for y in range(h):
            for x in range(w):
                here = tuple(src[y, x])
                neighbors = [
                    tuple(src[y + dy, x + dx]) if 0 <= x + dx < w and 0 <= y + dy < h else (0, 0, 0, 0)
                    for dx, dy in _N8
                ]
                if any(n == here for n in neighbors[:4]):
                    continue
                color, count = Counter(neighbors).most_common(1)[0]
                if count >= threshold:
                    result.pixels[y, x] = color
                    changed = True
        if not changed:
            break
    return result


def merge_shades(sprite: Sprite, max_delta: float = 0.05, passes: int = 2) -> Sprite:
    """Funde o salpicado de tons quase iguais (típico de foto convertida).

    Um pixel sem vizinho ortogonal da mesma cor adota a cor mais frequente entre
    os 8 vizinhos cuja diferença em OKLab seja < `max_delta`. Traços de verdade
    (olho, boca, contorno) têm contraste maior e ficam intactos.
    """
    from .color import srgb_to_oklab

    result = sprite.copy()
    h, w = result.height, result.width
    for _ in range(passes):
        src = result.pixels.copy()
        lab = srgb_to_oklab(src[..., :3])
        changed = False
        for y in range(h):
            for x in range(w):
                if src[y, x, 3] == 0:
                    continue
                here = tuple(src[y, x])
                if any(0 <= x + dx < w and 0 <= y + dy < h and tuple(src[y + dy, x + dx]) == here
                       for dx, dy in _N4):
                    continue
                candidates: Counter = Counter()
                for dx, dy in _N8:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and src[ny, nx, 3] > 0:
                        if np.sqrt(((lab[ny, nx] - lab[y, x]) ** 2).sum()) < max_delta:
                            candidates[tuple(src[ny, nx])] += 1
                if candidates:
                    result.pixels[y, x] = candidates.most_common(1)[0][0]
                    changed = True
        if not changed:
            break
    return result


def defringe(sprite: Sprite, passes: int = 1, max_delta: float = 0.10) -> Sprite:
    """Remove a franja do fundo que sobra na borda da silhueta (máscara/recorte).

    Pixel da borda (vizinho ortogonal transparente) cuja cor difere mais que
    `max_delta` (OKLab) da cor mais comum entre os vizinhos internos adota essa cor.
    """
    from .color import srgb_to_oklab

    result = sprite.copy()
    h, w = result.height, result.width
    for _ in range(passes):
        src = result.pixels.copy()
        opaque = src[..., 3] > 0
        edge = opaque & ~(
            _shifted(opaque, 0, -1) & _shifted(opaque, 0, 1) & _shifted(opaque, -1, 0) & _shifted(opaque, 1, 0)
        )
        lab = srgb_to_oklab(src[..., :3])
        for y, x in zip(*np.nonzero(edge)):
            inner: Counter = Counter()
            for dx, dy in _N8:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and opaque[ny, nx] and not edge[ny, nx]:
                    inner[(nx, ny)] = 1
            if not inner:
                continue
            colors = Counter(tuple(src[ny, nx]) for nx, ny in inner)
            color, _ = colors.most_common(1)[0]
            cx, cy = next((nx, ny) for nx, ny in inner if tuple(src[ny, nx]) == color)
            if np.sqrt(((lab[y, x] - lab[cy, cx]) ** 2).sum()) > max_delta:
                result.pixels[y, x] = color
    return result


def trim(sprite: Sprite) -> Sprite:
    """Recorta as margens totalmente transparentes."""
    opaque = sprite.pixels[..., 3] > 0
    if not opaque.any():
        return sprite.copy()
    ys, xs = np.nonzero(opaque)
    return Sprite(sprite.pixels[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1].copy())
