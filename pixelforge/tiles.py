"""Tilesets com autotile (blob 47 ou 16 tiles) e mapas a partir de grade de caracteres.

Tileset (JSON):

    {
      "name": "campo",
      "tile": 16,
      "terrenos": {
        "terra": {"cor": "#a46422", "textura": "pontos"},
        "grama": {"cor": "#38b764", "borda": "#257179", "textura": "grama", "modo": "blob47"},
        "agua":  {"cor": "#3b5dc9", "textura": "ondas", "modo": "blob16"},
        "muro":  {"imagem": "tiles/muro.png", "modo": "blob47"}
      }
    }

- `modo`: `blob47` (8 vizinhos, cantos internos), `blob16` (4 vizinhos) ou `cheio` (1 tile).
- Tiles gerados por código: preenchimento + textura determinística + borda arredondada
  (distância euclidiana até os vizinhos vazios). `imagem` usa tiles desenhados à mão,
  na mesma ordem da folha gerada (8 colunas; veja `tileset_sheet`).

Mapa (JSON):

    {
      "name": "vila",
      "tileset": "campo.tileset.json",
      "base": "terra",
      "legenda": {".": "terra", "g": "grama", "~": "agua"},
      "grade": ["..gggg..", ".gg~~gg.", "..gggg.."]
    }

Terrenos são desenhados na ordem de `ordem` (padrão: ordem da legenda), cada um
com autotile em relação a ele mesmo, por cima da `base`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from .palettes import RGBA, parse_color
from .recolor import shade
from .sprite import Sprite

# bits dos vizinhos (sentido horário a partir do norte)
N, NE, E, SE, S, SW, W, NW = 1, 2, 4, 8, 16, 32, 64, 128
OFFSETS = {N: (0, -1), NE: (1, -1), E: (1, 0), SE: (1, 1), S: (0, 1), SW: (-1, 1), W: (-1, 0), NW: (-1, -1)}
CORNERS = {NE: (N, E), SE: (S, E), SW: (S, W), NW: (N, W)}
MODES = ("blob47", "blob16", "cheio")
TEXTURES = ("liso", "pontos", "grama", "ondas", "tijolo")
SHEET_COLUMNS = 8


def reduce_mask(mask: int) -> int:
    """Remove cantos que não importam (canto só conta se os dois lados existem)."""
    for corner, (a, b) in CORNERS.items():
        if mask & corner and not (mask & a and mask & b):
            mask &= ~corner
    return mask


BLOB47 = sorted({reduce_mask(m) for m in range(256)})
BLOB47_INDEX = {m: i for i, m in enumerate(BLOB47)}
assert len(BLOB47) == 47


def blob16_mask(mask: int) -> int:
    """8 bits → 4 bits (N=1, E=2, S=4, W=8)."""
    return (1 if mask & N else 0) | (2 if mask & E else 0) | (4 if mask & S else 0) | (8 if mask & W else 0)


def tile_index(mask: int, mode: str) -> int:
    if mode == "blob47":
        return BLOB47_INDEX[reduce_mask(mask)]
    if mode == "blob16":
        return blob16_mask(mask)
    return 0


def tile_count(mode: str) -> int:
    return {"blob47": 47, "blob16": 16, "cheio": 1}[mode]


def mask_for(index: int, mode: str) -> int:
    """Máscara de 8 bits representativa do tile `index`."""
    if mode == "blob47":
        return BLOB47[index]
    if mode == "blob16":
        mask = (N if index & 1 else 0) | (E if index & 2 else 0) | (S if index & 4 else 0) | (W if index & 8 else 0)
        # sem cantos internos neste modo: canto presente sempre que os dois lados existem
        for corner, (a, b) in CORNERS.items():
            if mask & a and mask & b:
                mask |= corner
        return mask
    return 255


# --------------------------------------------------------------------------
# Geração de tiles
# --------------------------------------------------------------------------


@dataclass
class Terrain:
    name: str
    color: RGBA | None = None
    edge: RGBA | None = None
    texture: str = "liso"
    mode: str = "blob47"
    margin: float = 0.0   # recuo da forma em relação à borda do tile (px)
    border: int = 1       # espessura da borda (px)
    tiles: list[Sprite] = field(default_factory=list)


def _hash(x: np.ndarray, y: np.ndarray, seed: int) -> np.ndarray:
    """Ruído determinístico por pixel (0–1), sem estado global."""
    h = (x.astype(np.int64) * 374761393 + y.astype(np.int64) * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h & 0xFFFF) / 65535.0


def texture(size: int, color: RGBA, kind: str, seed: int = 0) -> np.ndarray:
    """Preenchimento de um tile (size × size × 4) com a textura escolhida."""
    if kind not in TEXTURES:
        raise ValueError(f"textura '{kind}' inválida; use: {', '.join(TEXTURES)}")
    ys, xs = np.mgrid[0:size, 0:size]
    out = np.zeros((size, size, 4), dtype=np.uint8)
    out[:] = color
    dark, light = np.array(shade(color, -1), dtype=np.uint8), np.array(shade(color, 1), dtype=np.uint8)
    noise = _hash(xs, ys, seed)
    if kind == "pontos":
        out[noise > 0.93] = dark
        out[noise < 0.04] = light
    elif kind == "grama":
        tuft = (noise > 0.9) & (ys % 4 != 0)
        out[tuft] = dark
        above = np.roll(tuft, -1, axis=0) & ~tuft
        out[above & (noise < 0.97)] = light
    elif kind == "ondas":
        wave = ((xs + 2 * (ys // 4)) % 8 < 3) & (ys % 4 == 1)
        out[wave] = light
        out[(noise > 0.96) & ~wave] = dark
    elif kind == "tijolo":
        row = ys // 4
        mortar = (ys % 4 == 3) | ((xs + (row % 2) * (size // 4)) % (size // 2) == 0)
        out[mortar] = dark
        out[(ys % 4 == 0) & ~mortar] = light
    return out


def _rect_distance(px: np.ndarray, py: np.ndarray, x0: float, y0: float, x1: float, y1: float) -> np.ndarray:
    dx = np.maximum(np.maximum(x0 - px, 0), px - x1)
    dy = np.maximum(np.maximum(y0 - py, 0), py - y1)
    return np.sqrt(dx ** 2 + dy ** 2)


def autotile(base: np.ndarray, mask: int, edge: RGBA | None, margin: float = 0.0, border: int = 1) -> np.ndarray:
    """Recorta o preenchimento `base` para os vizinhos de `mask` (8 bits).

    Cada pixel mede a distância até os tiles vizinhos ausentes: perto deles fica
    transparente (recuo `margin`) ou vira borda; cantos saem arredondados.
    """
    size = base.shape[0]
    ys, xs = np.mgrid[0:size, 0:size]
    px, py = xs + 0.5, ys + 0.5
    dist = np.full((size, size), np.inf)
    for bit, (dx, dy) in OFFSETS.items():
        if mask & bit:
            continue
        x0, y0 = dx * size, dy * size
        dist = np.minimum(dist, _rect_distance(px, py, x0, y0, x0 + size, y0 + size))
    # canto externo (os dois lados ausentes): arredonda com raio r
    r = max(2.0, size / 4)
    for corner, (a, b) in CORNERS.items():
        if mask & a or mask & b:
            continue
        sx, sy = OFFSETS[corner]
        cx = (margin + r) if sx < 0 else size - (margin + r)
        cy = (margin + r) if sy < 0 else size - (margin + r)
        quadrant = ((px - cx) * sx > 0) & ((py - cy) * sy > 0)
        round_d = margin + r - np.sqrt((px - cx) ** 2 + (py - cy) ** 2)
        dist = np.where(quadrant, np.minimum(dist, round_d), dist)
    out = base.copy()
    out[dist < margin + 0.5] = 0
    if edge is not None and border > 0:
        band = (dist >= margin + 0.5) & (dist < margin + 0.5 + border)
        out[band] = edge
    return out


def generate_tiles(terrain: Terrain, size: int, seed: int = 0) -> list[Sprite]:
    base = texture(size, terrain.color, terrain.texture, seed)
    return [Sprite(autotile(base, mask_for(i, terrain.mode), terrain.edge, terrain.margin, terrain.border))
            for i in range(tile_count(terrain.mode))]


def slice_tiles(image: Image.Image, size: int, count: int) -> list[Sprite]:
    """Lê tiles de uma folha (8 colunas, mesma ordem da folha gerada)."""
    pixels = np.array(image.convert("RGBA"), dtype=np.uint8)
    cols = pixels.shape[1] // size
    tiles = []
    for i in range(count):
        r, c = divmod(i, cols)
        tile = pixels[r * size:(r + 1) * size, c * size:(c + 1) * size]
        if tile.shape[:2] != (size, size):
            raise ValueError(f"folha pequena demais: precisa de {count} tiles de {size}px")
        tiles.append(Sprite(tile.copy()))
    return tiles


# --------------------------------------------------------------------------
# Tileset e mapa
# --------------------------------------------------------------------------


@dataclass
class Tileset:
    name: str
    size: int
    terrains: dict[str, Terrain]


def parse_tileset(data: dict, base_dir: Path = Path("."), default_name: str = "tileset") -> Tileset:
    size = int(data.get("tile", 16))
    if size < 4:
        raise ValueError("'tile' deve ser >= 4")
    terrains = {}
    for i, (name, spec) in enumerate((data.get("terrenos") or {}).items()):
        mode = spec.get("modo", "blob47")
        if mode not in MODES:
            raise ValueError(f"terrenos.{name}.modo = {mode!r}; use: {', '.join(MODES)}")
        t = Terrain(name, mode=mode, texture=spec.get("textura", "liso"),
                    margin=float(spec.get("recuo", 0)), border=int(spec.get("espessura", 1)))
        if "imagem" in spec:
            path = (base_dir / spec["imagem"])
            if not path.is_file():
                raise FileNotFoundError(f"terrenos.{name}.imagem: arquivo não encontrado: {path}")
            with Image.open(path) as im:
                t.tiles = slice_tiles(im, size, tile_count(mode))
        else:
            if "cor" not in spec:
                raise ValueError(f"terrenos.{name}: precisa de 'cor' ou 'imagem'")
            t.color = parse_color(spec["cor"])
            t.edge = parse_color(spec["borda"]) if spec.get("borda") else (shade(t.color, -2) if mode != "cheio" else None)
            t.tiles = generate_tiles(t, size, seed=i + 1)
        terrains[name] = t
    if not terrains:
        raise ValueError("tileset precisa de 'terrenos'")
    return Tileset(data.get("name") or default_name, size, terrains)


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: JSON inválido ({exc})") from None


def _stem(path: Path) -> str:
    name = path.name
    for suffix in (".json", ".tileset", ".mapa"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


def load_tileset(path: str | Path) -> Tileset:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"arquivo não encontrado: {path}")
    try:
        return parse_tileset(_read_json(path), path.parent, _stem(path))
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from None


def tileset_sheet(tileset: Tileset) -> tuple[Sprite, dict]:
    """Folha com todos os tiles (uma faixa por terreno, 8 colunas) + índice JSON.

    O índice diz, para cada terreno, a máscara de vizinhos de cada tile
    (bits: N=1 NE=2 E=4 SE=8 S=16 SW=32 W=64 NW=128) e sua posição na folha.
    """
    size = tileset.size
    rows_total = sum(-(-len(t.tiles) // SHEET_COLUMNS) for t in tileset.terrains.values())
    sheet = np.zeros((rows_total * size, SHEET_COLUMNS * size, 4), dtype=np.uint8)
    index: dict = {"tile": size, "colunas": SHEET_COLUMNS, "bits": {"N": N, "NE": NE, "E": E, "SE": SE, "S": S,
                                                                      "SW": SW, "W": W, "NW": NW},
                   "terrenos": {}}
    row = 0
    for name, t in tileset.terrains.items():
        entries = []
        for i, tile in enumerate(t.tiles):
            r, c = divmod(i, SHEET_COLUMNS)
            y, x = (row + r) * size, c * size
            sheet[y:y + size, x:x + size] = tile.pixels
            entries.append({"indice": i, "mascara": mask_for(i, t.mode), "x": x, "y": y})
        index["terrenos"][name] = {"modo": t.mode, "tiles": entries}
        row += -(-len(t.tiles) // SHEET_COLUMNS)
    return Sprite(sheet), index


@dataclass
class TileMap:
    name: str
    tileset: Tileset
    grid: list[str]
    legend: dict[str, str]
    base: str | None
    order: list[str]


def parse_map(data: dict, base_dir: Path = Path("."), default_name: str = "mapa") -> TileMap:
    ts = data.get("tileset")
    if isinstance(ts, dict):
        tileset = parse_tileset(ts, base_dir)
    elif isinstance(ts, str):
        tileset = load_tileset(base_dir / ts)
    else:
        raise ValueError("mapa precisa de 'tileset' (caminho ou objeto)")
    grid = data.get("grade") or []
    if not grid or any(len(r) != len(grid[0]) for r in grid):
        raise ValueError("'grade' deve ser uma lista de linhas, todas com a mesma largura")
    legend = dict(data.get("legenda") or {})
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch not in legend:
                raise ValueError(f"grade linha {y}, coluna {x}: caractere {ch!r} não está na legenda")
    for ch, name in legend.items():
        if name is not None and name not in tileset.terrains:
            raise ValueError(f"legenda {ch!r} → terreno {name!r} não existe no tileset")
    base = data.get("base")
    if base is not None and base not in tileset.terrains:
        raise ValueError(f"base {base!r} não existe no tileset")
    order = list(data.get("ordem") or dict.fromkeys(v for v in legend.values() if v))
    return TileMap(data.get("name") or default_name, tileset, grid, legend, base, order)


def load_map(path: str | Path) -> TileMap:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"arquivo não encontrado: {path}")
    try:
        return parse_map(_read_json(path), path.parent, _stem(path))
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from None


def neighbor_mask(cells: np.ndarray, x: int, y: int) -> int:
    """Máscara de 8 vizinhos; fora do mapa conta como presente (o terreno continua)."""
    h, w = cells.shape
    mask = 0
    for bit, (dx, dy) in OFFSETS.items():
        nx, ny = x + dx, y + dy
        if not (0 <= nx < w and 0 <= ny < h) or cells[ny, nx]:
            mask |= bit
    return mask


def render_map(tilemap: TileMap) -> Sprite:
    ts = tilemap.tileset
    size = ts.size
    h, w = len(tilemap.grid), len(tilemap.grid[0])
    names = np.array([[tilemap.legend[ch] or "" for ch in row] for row in tilemap.grid], dtype=object)
    out = np.zeros((h * size, w * size, 4), dtype=np.uint8)

    def stamp(tile: Sprite, x: int, y: int) -> None:
        dst = out[y * size:(y + 1) * size, x * size:(x + 1) * size]
        m = tile.pixels[..., 3] > 0
        dst[m] = tile.pixels[m]

    if tilemap.base:
        full = ts.terrains[tilemap.base]
        tile = full.tiles[tile_index(255, full.mode)]
        for y in range(h):
            for x in range(w):
                stamp(tile, x, y)
    for name in tilemap.order:
        if name == tilemap.base:
            continue
        t = ts.terrains[name]
        cells = names == name
        for y, x in zip(*np.nonzero(cells)):
            stamp(t.tiles[tile_index(neighbor_mask(cells, x, y), t.mode)], x, y)
    return Sprite(out)
