"""Rascunho de IA (ou qualquer imagem "pseudo-pixel") → pixel art de verdade.

Imagens de IA com estilo pixel têm blocos de tamanho irregular, bordas borradas
e centenas de tons. Pipeline:

  1. preparar: remover fundo (opcional) e ajustar contraste/saturação
  2. grade: detectar a escala e o deslocamento do pseudo-pixel (perfil de bordas)
     e alinhar as células a ela; sem grade confiável, células uniformes
  3. paleta: nomeada, arquivo (.hex/.png/.json), ou k-means OKLab com N cores
  4. reduzir: moda (voto da cor da paleta, centro do bloco pesa mais)
     ou mediana (OKLab) por célula
  5. limpeza: órfãos, fusão de tons quase iguais, contorno (seletivo ou cor fixa)

Só numpy + Pillow. Reaproveita `convert` (fundo, ajustes, paleta) e `process`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageOps

from . import palettes as pal
from . import process
from .color import kmeans_palette, nearest_lab, srgb_to_oklab
from .convert import enhance, parse_size, portable_path, remove_background
from .sprite import Art, Sprite, load_spec

MAX_SOURCE = 2048


@dataclass
class PixelizeOptions:
    size: tuple[int, int] | None = None  # None = tamanho natural da grade detectada
    colors: int = 24  # nº de cores do k-means (ignorado com palette)
    palette: str = ""  # "" = k-means | nome de paleta | arquivo .hex/.png/.json
    method: str = "mode"  # mode | median
    grid: str = "auto"  # auto | none | escala do pseudo-pixel em px (ex.: "8")
    grid_tolerance: float = 0.1  # com size: usa a grade se o tamanho natural ficar a ±10 %
    remove_bg: str = ""  # "" | "auto" | "#rrggbb"
    bg_tolerance: int = 40
    trim: bool = False  # recorta a margem transparente antes de reduzir
    contrast: float = 1.0
    saturation: float = 1.0
    cleanup: int = 1  # passadas de remoção de órfãos
    merge: float = 0.0  # funde tons quase iguais (ΔE OKLab; ~0.04). 0 desliga
    outline: str = ""  # "" | "selective" | "auto" | "#rrggbb"
    background: str = ""  # "" = transparente | "#rrggbb"
    alpha_threshold: int = 128

    @classmethod
    def from_dict(cls, values: dict) -> "PixelizeOptions":
        known = {f.name for f in fields(cls)}
        unknown = set(values) - known
        if unknown:
            raise ValueError(f"opções de pixelização desconhecidas: {', '.join(sorted(unknown))}")
        values = dict(values)
        if values.get("size") not in (None, "", "auto"):
            values["size"] = parse_size(values["size"])
        else:
            values["size"] = None
        return cls(**values)

    def to_dict(self) -> dict:
        data = asdict(self)
        if data["size"] is not None:
            data["size"] = list(data["size"])
        return data

    def validate(self) -> None:
        if self.method not in ("mode", "median"):
            raise ValueError(f"método deve ser mode ou median, recebido {self.method!r}")
        if self.grid not in ("auto", "none"):
            try:
                if float(self.grid) < 1:
                    raise ValueError
            except ValueError:
                raise ValueError(f"grade deve ser auto, none ou a escala em px, recebido {self.grid!r}") from None
        if not self.palette and not 2 <= self.colors <= 256:
            raise ValueError("cores deve ficar entre 2 e 256")
        if self.size is not None and min(self.size) < 1:
            raise ValueError("tamanho deve ser positivo")


@dataclass
class Grid:
    """Grade do pseudo-pixel: escala (px por pixel) e deslocamento em x e y."""

    scale: float
    offset_x: float
    offset_y: float
    confidence: float  # contraste médio das bordas na grade ÷ fora dela (0 = sem grade)

    def to_dict(self) -> dict:
        return {k: round(v, 3) for k, v in asdict(self).items()}


# --------------------------------------------------------------------------
# Grade
# --------------------------------------------------------------------------


def edge_profiles(rgb: np.ndarray, valid: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Força das bordas entre colunas (x) e entre linhas (y), somada na imagem.

    Usa a diferença em OKLab; pixels transparentes não contam.
    """
    lab = srgb_to_oklab(rgb)
    dx = np.sqrt(((lab[:, 1:] - lab[:, :-1]) ** 2).sum(axis=2))
    dy = np.sqrt(((lab[1:] - lab[:-1]) ** 2).sum(axis=2))
    if valid is not None:
        dx = dx * (valid[:, 1:] & valid[:, :-1])
        dy = dy * (valid[1:] & valid[:-1])
    # bordas fracas (ruído dentro do bloco) pesam menos que as fortes
    return (dx ** 1.5).sum(axis=0), (dy ** 1.5).sum(axis=1)


def _grid_mask(n: int, scale: float, offset: float) -> np.ndarray:
    """Posições do perfil que caem em fronteiras da grade (escala, deslocamento)."""
    # profile[i] = borda entre as colunas i e i+1 → fronteira em x = i + 1
    positions = np.round(offset + np.arange(0, n / scale + 1) * scale).astype(int) - 1
    mask = np.zeros(n, dtype=bool)
    mask[positions[(positions >= 0) & (positions < n)]] = True
    return mask


def _grid_score(profile: np.ndarray, scale: float, offset: float) -> float:
    """Média do perfil nas fronteiras previstas menos a média fora delas."""
    mask = _grid_mask(len(profile), scale, offset)
    if mask.sum() < 3:
        return -np.inf
    return float(profile[mask].mean() - profile[~mask].mean())


def _finer_grid_is_real(profile: np.ndarray, scale: float, offset: float, divisor: int) -> bool:
    """A grade `scale / divisor` (com o mesmo deslocamento) tem bordas próprias?

    Compara as fronteiras que só a grade fina tem (no meio dos blocos grandes)
    com as posições fora de qualquer fronteira: borda de verdade fica bem acima.
    """
    n = len(profile)
    coarse = _grid_mask(n, scale, offset)
    fine = _grid_mask(n, scale / divisor, offset)
    only_fine, off = fine & ~coarse, ~fine
    if only_fine.sum() < 3 or off.sum() < 3:
        return False
    return profile[only_fine].mean() > 2.5 * max(profile[off].mean(), 1e-9)


def _best_offset(profile: np.ndarray, scale: float) -> tuple[float, float]:
    best = (-np.inf, 0.0)
    for offset in np.arange(0, scale, 0.5 if scale < 16 else 1.0):
        best = max(best, (_grid_score(profile, scale, offset), float(offset)))
    return best


def detect_grid(rgb: np.ndarray, valid: np.ndarray | None = None, min_scale: float = 2.0,
                max_scale: float = 32.0) -> Grid:
    """Escala e deslocamento do pseudo-pixel.

    Para cada escala candidata (passo 0,25 px) e deslocamento, compara a força
    das bordas nas fronteiras previstas com a força fora delas. A escala certa
    vence as frações dela (que caem no meio dos blocos) e os múltiplos (que
    pulam fronteiras e misturam bordas reais na média de fora).
    """
    px, py = edge_profiles(rgb, valid)
    if px.sum() <= 0 or py.sum() <= 0:
        return Grid(1.0, 0.0, 0.0, 0.0)
    px, py = px / px.mean(), py / py.mean()
    max_scale = min(max_scale, min(rgb.shape[:2]) / 4)
    found: dict[float, tuple[float, float, float]] = {}
    for scale in np.arange(min_scale, max_scale + 1e-9, 0.25):
        sx, ox = _best_offset(px, scale)
        sy, oy = _best_offset(py, scale)
        found[float(scale)] = (sx + sy, ox, oy)
    scale = max(found, key=lambda s: found[s][0])
    # o vencedor pode ser múltiplo da escala real (16 em vez de 8, 15 em vez de 7,5) quando
    # parte dos blocos vem em pares; desce enquanto a grade mais fina tiver bordas próprias
    descended = True
    while descended:
        descended = False
        _, ox, oy = found[scale]
        for divisor in (2, 3):
            smaller = round(scale / divisor * 4) / 4
            if smaller < min_scale or smaller not in found:
                continue
            if _finer_grid_is_real(px, scale, ox, divisor) and _finer_grid_is_real(py, scale, oy, divisor):
                scale, descended = smaller, True
                break
    score, ox, oy = found[scale]
    # confiança: borda média na grade ÷ borda média geral (1 = nada se destaca)
    confidence = max(0.0, score / 2)
    return Grid(scale, ox, oy, confidence)


def cell_edges(length: int, scale: float, offset: float) -> np.ndarray:
    """Fronteiras inteiras das células alinhadas à grade.

    Células parciais nas bordas entram só se tiverem ao menos metade do tamanho;
    as menores ficam de fora (recorte), em vez de misturar duas cores numa célula.
    """
    starts = offset + np.arange(-1, length / scale + 2) * scale
    edges = np.round(starts).astype(int)
    edges = edges[(edges > 0) & (edges < length)]
    edges = np.unique(np.concatenate([[0], edges, [length]]))
    if len(edges) > 2 and edges[1] - edges[0] < scale / 2:
        edges = edges[1:]
    if len(edges) > 2 and edges[-1] - edges[-2] < scale / 2:
        edges = edges[:-1]
    return edges


def uniform_edges(length: int, cells: int) -> np.ndarray:
    return np.round(np.linspace(0, length, cells + 1)).astype(int)


# --------------------------------------------------------------------------
# Paleta
# --------------------------------------------------------------------------


def load_palette_spec(spec: str, palette_dirs: Iterable[Path] = (), colors: int = 32) -> np.ndarray:
    """Nome de paleta, .hex, ou as cores de uma arte (.png / spec .json). Retorna (N, 3)."""
    path = Path(spec)
    if path.suffix.lower() == ".hex" and path.is_file():
        found = pal.load_hex_file(path)
    elif path.suffix.lower() == ".json" and path.is_file():
        found = load_spec(path).colors()
    elif path.suffix.lower() in (".png", ".gif", ".webp") and path.is_file():
        with Image.open(path) as opened:
            px = np.array(opened.convert("RGBA")).reshape(-1, 4)
        px = px[px[:, 3] >= 128, :3]
        uniq = np.unique(px, axis=0)
        if len(uniq) > 256:  # imagem comum: resume em `colors` cores
            return kmeans_palette(px, colors)
        return uniq.astype(np.int32)
    else:
        found = pal.get(spec, palette_dirs)
    rgb = [c[:3] for c in found if c[3] > 0]
    if not rgb:
        raise ValueError(f"paleta {spec!r} não tem cores opacas")
    return np.array(rgb, dtype=np.int32)


# --------------------------------------------------------------------------
# Redução
# --------------------------------------------------------------------------


def reduce_cells(lab: np.ndarray, valid: np.ndarray, xs: np.ndarray, ys: np.ndarray,
                 colors_lab: np.ndarray, method: str) -> tuple[np.ndarray, np.ndarray]:
    """Uma cor da paleta por célula. Retorna (índices (H, W), opaco (H, W))."""
    h, w = len(ys) - 1, len(xs) - 1
    index = np.zeros((h, w), dtype=np.int64)
    opaque = np.zeros((h, w), dtype=bool)
    labels = nearest_lab(lab, colors_lab) if method == "mode" else None
    n = len(colors_lab)
    for j in range(h):
        y0, y1 = ys[j], ys[j + 1]
        for i in range(w):
            x0, x1 = xs[i], xs[i + 1]
            ok = valid[y0:y1, x0:x1]
            if ok.mean() < 0.5:
                continue
            opaque[j, i] = True
            if method == "median":
                med = np.median(lab[y0:y1, x0:x1][ok], axis=0)
                index[j, i] = nearest_lab(med[None], colors_lab)[0]
                continue
            # moda com peso no centro: a borda borrada entre blocos vota menos
            cy = np.abs(np.arange(y0, y1) - (y0 + y1 - 1) / 2) / max(y1 - y0, 1)
            cx = np.abs(np.arange(x0, x1) - (x0 + x1 - 1) / 2) / max(x1 - x0, 1)
            weight = (1.0 - cy[:, None]) * (1.0 - cx[None, :])
            votes = np.bincount(labels[y0:y1, x0:x1][ok], weights=weight[ok], minlength=n)
            index[j, i] = int(votes.argmax())
    return index, opaque


# --------------------------------------------------------------------------
# Contorno seletivo
# --------------------------------------------------------------------------


def selective_outline(sprite: Sprite, colors: np.ndarray, darken: float = 0.22) -> Sprite:
    """Contorno de "selout": cada pixel de contorno é uma versão escura da cor vizinha.

    Pinta os pixels transparentes vizinhos (4-conexos) a pixels opacos com a cor
    da paleta mais próxima de (L − darken) da cor interna vizinha.
    """
    px = sprite.pixels
    opaque = px[..., 3] > 0
    colors_lab = srgb_to_oklab(colors)
    result = sprite.copy()
    h, w = opaque.shape
    for y, x in zip(*np.nonzero(~opaque)):
        neighbors = [(y + dy, x + dx) for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1))
                     if 0 <= y + dy < h and 0 <= x + dx < w and opaque[y + dy, x + dx]]
        if not neighbors:
            continue
        lab = srgb_to_oklab(np.array([px[ny, nx, :3] for ny, nx in neighbors])).mean(axis=0)
        lab[0] -= darken
        lab[1:] *= 0.8
        idx = int(nearest_lab(lab[None], colors_lab)[0])
        result.pixels[y, x] = (*colors[idx], 255)
    return result


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------


def load_source(source: str | Path | Image.Image) -> Image.Image:
    if isinstance(source, Image.Image):
        image = ImageOps.exif_transpose(source).convert("RGBA")
    else:
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGBA")
    image.thumbnail((MAX_SOURCE, MAX_SOURCE), Image.Resampling.LANCZOS)
    return image


def pixelize(source: str | Path | Image.Image, options: PixelizeOptions, name: str | None = None,
             palette_dirs: Iterable[Path] = ()) -> Art:
    options.validate()
    if name is None:
        name = "arte" if isinstance(source, Image.Image) else Path(source).stem
    image = load_source(source)
    if options.remove_bg:
        image = remove_background(image, options.remove_bg, options.bg_tolerance)
    image = enhance(image, options.contrast, options.saturation, 1.0)

    px = np.array(image, dtype=np.uint8)
    valid = px[..., 3] >= options.alpha_threshold
    rgb = px[..., :3]
    height, width = valid.shape

    grid = _choose_grid(rgb, valid, options)
    if grid is not None:
        xs = cell_edges(width, grid.scale, grid.offset_x)
        ys = cell_edges(height, grid.scale, grid.offset_y)
    else:
        tw, th = options.size or (max(1, round(width / 8)), max(1, round(height / 8)))
        xs, ys = uniform_edges(width, tw), uniform_edges(height, th)

    if options.palette:
        colors = load_palette_spec(options.palette, palette_dirs, options.colors)
    elif valid.any():
        colors = kmeans_palette(_cell_centers(rgb, valid, xs, ys), options.colors)
    else:
        colors = np.zeros((1, 3), dtype=np.int32)
    colors_lab = srgb_to_oklab(colors)

    lab = srgb_to_oklab(rgb)
    index, opaque = reduce_cells(lab, valid, xs, ys, colors_lab, options.method)

    out = np.zeros(index.shape + (4,), dtype=np.uint8)
    out[..., :3] = colors[index]
    out[..., 3] = np.where(opaque, 255, 0)
    out[~opaque] = 0
    sprite = Sprite(out)

    # grade natural ≠ tamanho pedido (dentro da tolerância): ajuste final por vizinho
    if options.size and (sprite.width, sprite.height) != tuple(options.size):
        sprite = Sprite(np.array(sprite.to_image().resize(options.size, Image.Resampling.NEAREST)))

    if options.trim:
        sprite = process.trim(sprite)
    if options.cleanup:
        sprite = process.cleanup(sprite, options.cleanup)
    if options.merge > 0:
        sprite = process.merge_shades(sprite, options.merge)
    if options.outline == "selective":
        sprite = selective_outline(_pad(sprite), colors)
    elif options.outline:
        color = (pal.darkest([(*map(int, c), 255) for c in colors]) if options.outline == "auto"
                 else pal.parse_color(options.outline))
        sprite = process.outline(_pad(sprite), color)
    if options.background:
        sprite.pixels[sprite.pixels[..., 3] == 0] = pal.parse_color(options.background)

    meta = {"pixelize": options.to_dict(),
            "grid": grid.to_dict() if grid else None}
    if not isinstance(source, Image.Image):
        meta = {"source": portable_path(source), **meta}
    return Art(name, [sprite], meta=meta)


def _choose_grid(rgb: np.ndarray, valid: np.ndarray, options: PixelizeOptions) -> Grid | None:
    """Grade a usar, ou None para células uniformes no tamanho pedido."""
    if options.grid == "none":
        return None
    height, width = valid.shape
    if options.grid != "auto":
        scale = float(options.grid)
        px, py = edge_profiles(rgb, valid)
        return Grid(scale, _best_offset(px, scale)[1], _best_offset(py, scale)[1], 1.0)
    grid = detect_grid(rgb, valid)
    if grid.confidence < 0.6:  # nada se destaca: não é pseudo-pixel
        return None
    if options.size:
        natural = (width / grid.scale, height / grid.scale)
        ok = all(abs(n - t) <= options.grid_tolerance * t for n, t in zip(natural, options.size))
        if not ok:
            return None
    return grid


def _cell_centers(rgb: np.ndarray, valid: np.ndarray, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Amostra do meio de cada célula (sem a borda borrada) para o k-means."""
    picks = []
    for j in range(len(ys) - 1):
        y0, y1 = ys[j], ys[j + 1]
        my0, my1 = y0 + (y1 - y0) // 4, max(y0 + (y1 - y0) // 4 + 1, y1 - (y1 - y0) // 4)
        for i in range(len(xs) - 1):
            x0, x1 = xs[i], xs[i + 1]
            mx0, mx1 = x0 + (x1 - x0) // 4, max(x0 + (x1 - x0) // 4 + 1, x1 - (x1 - x0) // 4)
            ok = valid[my0:my1, mx0:mx1]
            if ok.any():
                picks.append(rgb[my0:my1, mx0:mx1][ok])
    return np.concatenate(picks) if picks else rgb[valid]


def _pad(sprite: Sprite) -> Sprite:
    """Garante 1 px transparente em volta (espaço para o contorno) se a arte encosta na borda."""
    a = sprite.pixels[..., 3] > 0
    if not (a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any()):
        return sprite
    return Sprite(np.pad(sprite.pixels, ((1, 1), (1, 1), (0, 0))))


def comparison(raw: Image.Image, art: Art, height: int = 768) -> Image.Image:
    """Rascunho e pixel art lado a lado, mesma altura (para revisão)."""
    pixel = art.frames[0].to_image()
    scale = max(1, height // pixel.height)
    pixel = pixel.resize((pixel.width * scale, pixel.height * scale), Image.Resampling.NEAREST)
    raw = raw.convert("RGBA")
    raw = raw.resize((round(raw.width * pixel.height / raw.height), pixel.height), Image.Resampling.LANCZOS)
    sheet = Image.new("RGBA", (raw.width + pixel.width + 16, pixel.height), (40, 40, 44, 255))
    sheet.alpha_composite(raw, (0, 0))
    checker = _checker(pixel.size)
    checker.alpha_composite(pixel)
    sheet.alpha_composite(checker, (raw.width + 16, 0))
    return sheet


def _checker(size: tuple[int, int], cell: int = 16) -> Image.Image:
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    tone = np.where(((xx // cell) + (yy // cell)) % 2 == 0, 200, 170).astype(np.uint8)
    return Image.fromarray(np.dstack([tone, tone, tone, np.full_like(tone, 255)]), "RGBA")
