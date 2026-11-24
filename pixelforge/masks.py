"""Máscaras a partir de formas (polígonos e elipses) para isolar a figura da foto.

Coordenadas em frações da imagem (todos os valores ≤ 1) ou em pixels.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def _points(spec: str, size: tuple[int, int]) -> list[tuple[float, float]]:
    pairs = [tuple(float(v) for v in p.split(",")) for p in spec.split()]
    if len(pairs) < 3 or any(len(p) != 2 for p in pairs):
        raise ValueError(f'polígono inválido (use "x,y x,y x,y ..."): {spec!r}')
    fractional = all(v <= 1 for p in pairs for v in p)
    return [(x * size[0], y * size[1]) if fractional else (x, y) for x, y in pairs]


def _ellipse(spec: str, size: tuple[int, int]) -> tuple[float, float, float, float]:
    cx, cy, rx, ry = (float(v) for v in spec.split(","))
    if max(cx, cy, rx, ry) <= 1:
        cx, rx = cx * size[0], rx * size[0]
        cy, ry = cy * size[1], ry * size[1]
    return cx - rx, cy - ry, cx + rx, cy + ry


def build_mask(size: tuple[int, int], polygons: list[str], ellipses: list[str],
               subtract: list[str] = (), feather: float = 0.6) -> Image.Image:
    """Máscara L (255 = manter). `feather` em % do lado maior suaviza a borda."""
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    for spec in polygons:
        draw.polygon(_points(spec, size), fill=255)
    for spec in ellipses:
        draw.ellipse(_ellipse(spec, size), fill=255)
    for spec in subtract:
        draw.polygon(_points(spec, size), fill=0)
    radius = max(size) * feather / 100
    return mask.filter(ImageFilter.GaussianBlur(radius)) if radius > 0 else mask


def mask_preview(image: Image.Image, mask: Image.Image, max_side: int = 640) -> Image.Image:
    """Foto com a área removida escurecida e tingida de vermelho, para conferir a máscara."""
    rgb = np.array(image.convert("RGB"), dtype=np.float64)
    m = np.array(mask, dtype=np.float64)[..., None] / 255
    tint = rgb * 0.25 + np.array([160, 30, 30]) * 0.35
    out = Image.fromarray((rgb * m + tint * (1 - m)).astype(np.uint8), "RGB")
    out.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return out
