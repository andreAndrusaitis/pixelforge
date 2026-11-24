"""Sombreamento e contorno automáticos a partir de arte chapada.

Cada região (pixels conectados da mesma cor) é tratada como um volume
arredondado: a posição do pixel dentro da região, medida na direção da luz,
decide se ele recebe luz, fica na base ou cai na sombra. As cores vêm de
rampas automáticas (`recolor.ramp`) ou fornecidas pelo chamador.

    sombreado = auto_shade(sprite, light="cima-esquerda")
    pronto = outline(sombreado, "selout")
"""

from __future__ import annotations

from collections import deque

import numpy as np

from .palettes import RGBA, darkest, parse_color
from .process import _N4, _shifted
from .recolor import ramp, shade
from .sprite import Sprite

LIGHTS = {
    "cima-esquerda": (-1, -1), "cima": (0, -1), "cima-direita": (1, -1),
    "esquerda": (-1, 0), "direita": (1, 0),
    "baixo-esquerda": (-1, 1), "baixo": (0, 1), "baixo-direita": (1, 1),
}


def parse_light(value: str | tuple | list) -> tuple[int, int]:
    """Nome (cima-esquerda, ...) ou vetor [dx, dy] apontando para a luz."""
    if isinstance(value, str):
        key = value.strip().lower().replace("_", "-").replace(" ", "-")
        if key not in LIGHTS:
            raise ValueError(f"luz '{value}' inválida. Use: {', '.join(LIGHTS)}")
        return LIGHTS[key]
    dx, dy = (int(np.sign(v)) for v in value)
    if (dx, dy) == (0, 0):
        raise ValueError("vetor de luz não pode ser [0, 0]")
    return dx, dy


def label_regions(pixels: np.ndarray) -> np.ndarray:
    """Componentes conectados (4 vizinhos) de mesma cor; -1 = transparente."""
    h, w = pixels.shape[:2]
    labels = np.full((h, w), -1, dtype=np.int32)
    key = pixels.astype(np.uint32)
    key = (key[..., 0] << 24) | (key[..., 1] << 16) | (key[..., 2] << 8) | key[..., 3]
    opaque = pixels[..., 3] > 0
    current = 0
    for y in range(h):
        for x in range(w):
            if not opaque[y, x] or labels[y, x] >= 0:
                continue
            target = key[y, x]
            labels[y, x] = current
            queue = deque([(x, y)])
            while queue:
                cx, cy = queue.popleft()
                for dx, dy in _N4:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and labels[ny, nx] < 0 and opaque[ny, nx] and key[ny, nx] == target:
                        labels[ny, nx] = current
                        queue.append((nx, ny))
            current += 1
    return labels


def _runs(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Para cada pixel da máscara: posição relativa (0–1) e comprimento do trecho na linha."""
    h, w = mask.shape
    pos = np.full((h, w), 0.5)
    length = np.zeros((h, w), dtype=np.int32)
    for y in range(h):
        x = 0
        row = mask[y]
        while x < w:
            if not row[x]:
                x += 1
                continue
            start = x
            while x < w and row[x]:
                x += 1
            n = x - start
            length[y, start:x] = n
            if n > 1:
                pos[y, start:x] = (np.arange(n) + 0.5) / n
    return pos, length


def shade_scores(mask: np.ndarray, light: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    """Nota 0 (de frente para a luz) a 1 (lado oposto) para cada pixel da máscara."""
    lx, ly = light
    tx, rx = _runs(mask)
    ty, ry = _runs(mask.T)
    ty, ry = ty.T, ry.T
    px = tx if lx < 0 else (1 - tx if lx > 0 else np.full_like(tx, 0.5))
    py = ty if ly < 0 else (1 - ty if ly > 0 else np.full_like(ty, 0.5))
    wx, wy = abs(lx), abs(ly)
    # trecho de 1 pixel não tem volume naquele eixo
    px = np.where(rx > 1, px, 0.5)
    py = np.where(ry > 1, py, 0.5)
    score = (wx * px + wy * py) / (wx + wy)
    return score, np.minimum(rx, ry)


def shade_regions(regions: np.ndarray, ramps: dict[int, tuple[list[RGBA], int]],
                  light=(-1, -1), shadow: float = 0.6, highlight: float = 0.2,
                  casts: dict[int, set[int]] | None = None,
                  volumes: dict[int, np.ndarray] | None = None) -> np.ndarray:
    """Pinta cada região com a rampa dela; devolve RGBA (h, w, 4).

    ramps[r] = (cores da mais clara à mais escura, índice da base).
    casts[r] = regiões que projetam sombra sobre r (ex.: cabelo sobre o rosto):
    o pixel de r logo abaixo/ao lado de uma delas, do lado da luz, fica na sombra.
    volumes[r] = máscara usada para medir o volume (ex.: a região mais os detalhes
    preservados dentro dela), para buracos não quebrarem a sombra.
    """
    light = parse_light(light)
    h, w = regions.shape
    out = np.zeros((h, w, 4), dtype=np.uint8)
    index = np.zeros((h, w), dtype=np.int32)
    for r, (colors, base) in ramps.items():
        mask = regions == r
        if not mask.any():
            continue
        score, thickness = shade_scores(volumes[r] if volumes and r in volumes else mask, light)
        level = np.zeros((h, w), dtype=np.int32)
        level[mask & (score > shadow)] = 1
        level[mask & (score > 0.5 + shadow / 2) & (thickness >= 8)] = 2
        level[mask & (score < highlight) & (thickness >= 4)] = -1
        if casts and r in casts:
            caster = np.isin(regions, list(casts[r]))
            # vizinho do lado da luz (acima/ao lado) pertence a quem projeta
            near = np.zeros_like(caster)
            if light[1]:  # luz de cima/baixo: sombra só na vertical (franja sobre a testa)
                near |= _shifted(caster, 0, light[1])
            else:
                near |= _shifted(caster, light[0], 0)
            level[mask & near] = np.maximum(level[mask & near], 1)
        level = _despeckle(level, mask)
        index[mask] = np.clip(base + level[mask], 0, len(colors) - 1)
        palette = np.array(colors, dtype=np.uint8)
        out[mask] = palette[index[mask]]
    return out


def _despeckle(level: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Tom isolado (nenhum vizinho ortogonal com o mesmo tom) adota o da maioria."""
    h, w = level.shape
    out = level.copy()
    for y, x in zip(*np.nonzero(mask)):
        here = level[y, x]
        neigh = [level[y + dy, x + dx] for dx, dy in _N4
                 if 0 <= x + dx < w and 0 <= y + dy < h and mask[y + dy, x + dx]]
        if len(neigh) >= 2 and here not in neigh:
            out[y, x] = max(set(neigh), key=neigh.count)
    return out


def auto_shade(sprite: Sprite, light="cima-esquerda", shadow: float = 0.6, highlight: float = 0.2,
               ramps: dict[RGBA, list[RGBA]] | None = None, keep: list[RGBA] | None = None,
               min_size: int = 3) -> Sprite:
    """Sombreia arte chapada. `keep`: cores que não recebem sombra (ex.: contorno, olhos).

    Regiões com menos de `min_size` pixels em algum eixo (traços, olhos) ficam como estão.
    """
    keep_set = {tuple(parse_color(c)) for c in (keep or [])}
    regions = label_regions(sprite.pixels)
    table: dict[int, tuple[list[RGBA], int]] = {}
    custom = {tuple(parse_color(k) if isinstance(k, str) else k): v for k, v in (ramps or {}).items()}
    for r in range(int(regions.max()) + 1):
        ys, xs = np.nonzero(regions == r)
        color = tuple(int(v) for v in sprite.pixels[ys[0], xs[0]])
        if color in keep_set or (ys.max() - ys.min() + 1) < min_size or (xs.max() - xs.min() + 1) < min_size:
            continue
        if color in custom:
            colors = [parse_color(c) if isinstance(c, str) else tuple(c) for c in custom[color]]
            base = colors.index(color) if color in colors else len(colors) // 2
        else:
            colors, base = ramp(color), 1
        table[r] = (colors, base)
    kept = np.zeros(regions.shape, dtype=bool)
    for color in keep_set:
        kept |= np.all(sprite.pixels == np.array(color, dtype=np.uint8), axis=-1)
    volumes = {r: (regions == r) | kept for r in table} if kept.any() else None
    shaded = shade_regions(regions, table, light, shadow, highlight, volumes=volumes)
    out = sprite.copy()
    touched = np.isin(regions, list(table))
    out.pixels[touched] = shaded[touched]
    return out


def selout(sprite: Sprite, dark_of: dict[RGBA, RGBA] | None = None, levels: float = -3) -> Sprite:
    """Contorno seletivo: cada pixel do contorno usa um tom escuro da cor vizinha
    (em vez de preto chapado). `dark_of` força o tom de cada cor."""
    pixels = sprite.pixels
    h, w = pixels.shape[:2]
    opaque = pixels[..., 3] > 0
    near = np.zeros_like(opaque)
    for dx, dy in _N4:
        near |= _shifted(opaque, dx, dy)
    out = sprite.copy()
    cache: dict[RGBA, RGBA] = {}
    for y, x in zip(*np.nonzero(near & ~opaque)):
        neigh = [tuple(int(v) for v in pixels[y + dy, x + dx]) for dx, dy in _N4
                 if 0 <= x + dx < w and 0 <= y + dy < h and opaque[y + dy, x + dx]]
        source = darkest(neigh)
        if source not in cache:
            cache[source] = (dark_of or {}).get(source) or shade(source, levels)
        out.pixels[y, x] = cache[source]
    return out


def outline(sprite: Sprite, mode: str = "selout", dark_of: dict[RGBA, RGBA] | None = None) -> Sprite:
    """mode: "selout", "auto" (cor mais escura da arte), "#rrggbb" ou "nenhum"."""
    from .process import outline as solid

    mode = (mode or "nenhum").strip().lower()
    if mode in ("nenhum", "none", ""):
        return sprite.copy()
    if mode == "selout":
        return selout(sprite, dark_of)
    if mode == "auto":
        return solid(sprite, shade(darkest(sprite.colors()), -2))
    return solid(sprite, parse_color(mode))
