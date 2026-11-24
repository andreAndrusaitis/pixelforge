"""Imagem de referência → pixel art.

Pipeline:
  1. preparar: EXIF → máscara → recorte → remover fundo → aparar → ajustar cores
     → encaixar numa "resolução de trabalho" = tamanho final × K (K até 8)
  2. suavizar preservando bordas (Kuwahara), na resolução de trabalho
  3. paleta: nomeada ou k-means em OKLab (região de foco pesa mais)
  4. reduzir para a grade final:
       detail → cor dominante de cada bloco, com peso extra para tons escuros
                (olhos, boca e contornos não somem)
       box/nearest/bilinear/lanczos → reamostragem + quantização com dithering
  5. traço: bordas fortes da foto escurecem o pixel do lado escuro
  6. limpeza (franja do fundo, pixels órfãos, fusão de tons quase iguais), contorno, fundo
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageEnhance, ImageOps

from . import palettes as pal
from . import process
from .color import kmeans_palette, nearest_lab, srgb_to_oklab
from .draw import BAYER2, BAYER4
from .filters import blocks, center_weights, kuwahara, sobel
from .sprite import Art, Sprite

MAX_SOURCE = 1024
WORK_TARGET = 512  # lado aproximado da resolução de trabalho
RESAMPLE = {
    "box": Image.Resampling.BOX,
    "nearest": Image.Resampling.NEAREST,
    "bilinear": Image.Resampling.BILINEAR,
    "lanczos": Image.Resampling.LANCZOS,
    "detail": None,
}


@dataclass
class ConvertOptions:
    size: tuple[int, int] = (32, 32)
    palette: int | str = 16
    dither: str = "none"  # none | floyd | bayer2 | bayer4 (ignorado com resample=detail)
    dither_strength: float = 0.4
    fit: str = "contain"  # contain | cover | stretch
    crop: tuple[float, float, float, float] | None = None  # x, y, w, h (frações ≤1 ou pixels)
    mask: str = ""  # imagem em tons de cinza: branco = manter
    contrast: float = 1.0
    saturation: float = 1.0
    sharpness: float = 1.0
    resample: str = "box"  # box | nearest | bilinear | lanczos | detail
    detail: float = 0.5  # peso extra de tons escuros nos blocos com borda (modo detail)
    edge_spread: float = 0.25  # variação de luminosidade que faz um bloco "ter borda" (modo detail)
    smooth: str = "none"  # none | kuwahara
    smooth_radius: int = 0  # 0 = automático (≈ K/2)
    lines: float = 0.0  # 0–1: força do traço vindo das bordas da foto
    line_threshold: float = 0.35  # 0–1: quão forte uma borda precisa ser
    focus: tuple[float, float, float, float] | None = None  # x, y, w, h em frações do quadro final
    focus_weight: float = 4.0
    alpha_threshold: int = 128
    remove_bg: str = ""  # "" | "auto" | "#rrggbb"
    bg_tolerance: int = 40
    trim: bool = True
    cleanup: int = 1
    merge: float = 0.0  # funde tons quase iguais com ΔE OKLab abaixo disso (0 desliga; ~0.05)
    defringe: int = 0  # passadas removendo franja de fundo na borda da silhueta
    outline: str = ""  # "" | "auto" | "#rrggbb"
    background: str = ""  # "" = transparente | "#rrggbb" preenche o fundo

    @classmethod
    def from_dict(cls, values: dict) -> "ConvertOptions":
        known = {f.name for f in fields(cls)}
        unknown = set(values) - known
        if unknown:
            raise ValueError(f"opções de conversão desconhecidas: {', '.join(sorted(unknown))}")
        values = dict(values)
        if "size" in values:
            values["size"] = parse_size(values["size"])
        for key in ("crop", "focus"):
            if values.get(key) is not None:
                values[key] = parse_box(values[key])
        return cls(**values)

    def to_dict(self) -> dict:
        data = asdict(self)
        for key in ("size", "crop", "focus"):
            if data[key] is not None:
                data[key] = list(data[key])
        return data

    def validate(self) -> None:
        checks = {
            "dither": ("none", "floyd", "bayer2", "bayer4"),
            "fit": ("contain", "cover", "stretch"),
            "resample": tuple(RESAMPLE),
            "smooth": ("none", "kuwahara"),
        }
        for name, allowed in checks.items():
            if getattr(self, name) not in allowed:
                raise ValueError(f"{name} deve ser um de {allowed}, recebido {getattr(self, name)!r}")
        if min(self.size) < 1:
            raise ValueError("size deve ser positivo")
        if isinstance(self.palette, int) and not 2 <= self.palette <= 256:
            raise ValueError("palette adaptativa deve ter entre 2 e 256 cores")


def parse_size(value) -> tuple[int, int]:
    """32 | "32" | "32x48" | [32, 48] → (largura, altura)."""
    if isinstance(value, int):
        return value, value
    if isinstance(value, str):
        parts = value.lower().split("x")
        if len(parts) == 1:
            return int(parts[0]), int(parts[0])
        return int(parts[0]), int(parts[1])
    w, h = value
    return int(w), int(h)


def parse_box(value) -> tuple[float, float, float, float]:
    """"x,y,w,h" | [x, y, w, h] → tupla de 4 floats."""
    parts = value.split(",") if isinstance(value, str) else value
    box = tuple(float(v) for v in parts)
    if len(box) != 4 or box[2] <= 0 or box[3] <= 0:
        raise ValueError(f"caixa inválida (esperado x,y,w,h): {value!r}")
    return box  # type: ignore[return-value]


def portable_path(path: str | Path) -> str:
    """Caminho relativo à pasta atual (com /) quando possível — specs ficam portáveis."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(resolved)


def work_factor(size: tuple[int, int]) -> int:
    return int(np.clip(WORK_TARGET // max(size), 1, 8))


# --------------------------------------------------------------------------
# Conversão
# --------------------------------------------------------------------------


def convert(source: str | Path | Image.Image, options: ConvertOptions,
            name: str | None = None, palette_dirs: Iterable[Path] = ()) -> Art:
    options.validate()
    if name is None:
        name = "art" if isinstance(source, Image.Image) else Path(source).stem
    work, k = prepare(source, options)
    tw, th = options.size

    opaque_hi = work[..., 3] >= options.alpha_threshold
    rgb_hi = work[..., :3].astype(np.float64)
    if options.smooth == "kuwahara":
        radius = options.smooth_radius or max(1, k // 2)
        rgb_hi = kuwahara(rgb_hi, radius, opaque_hi)
    rgb_hi_u8 = np.clip(np.round(rgb_hi), 0, 255).astype(np.uint8)
    lab_hi = srgb_to_oklab(rgb_hi_u8)

    weights = focus_weights(opaque_hi.shape, options.focus, options.focus_weight)
    colors = resolve_palette(options.palette, rgb_hi_u8[opaque_hi], palette_dirs, weights[opaque_hi])
    colors_lab = srgb_to_oklab(colors)

    if options.resample == "detail":
        labels_hi = nearest_lab(lab_hi, colors_lab)
        index, opaque = detail_downscale(labels_hi, opaque_hi, lab_hi, colors_lab, k, options.detail,
                                         options.edge_spread)
    else:
        small = np.dstack([rgb_hi_u8, work[..., 3]])
        small = np.array(Image.fromarray(small, "RGBA").resize((tw, th), RESAMPLE[options.resample]))
        opaque = small[..., 3] >= options.alpha_threshold
        index = quantize_index(small[..., :3], opaque, colors, colors_lab, options.dither, options.dither_strength)

    if options.lines > 0:
        index = apply_lines(index, opaque, lab_hi, opaque_hi, colors_lab, k, options.lines, options.line_threshold)

    out = np.zeros((th, tw, 4), dtype=np.uint8)
    out[..., :3] = colors[index]
    out[..., 3] = np.where(opaque, 255, 0)
    out[~opaque] = 0
    sprite = Sprite(out)

    if options.defringe:
        sprite = process.defringe(sprite, options.defringe)
    if options.cleanup:
        sprite = process.cleanup(sprite, options.cleanup)
    if options.merge > 0:
        sprite = process.merge_shades(sprite, options.merge)
    if options.outline:
        color = (
            pal.darkest([(*map(int, c), 255) for c in colors])
            if options.outline == "auto"
            else pal.parse_color(options.outline)
        )
        sprite = process.outline(sprite, color)
    if options.background:
        bg = pal.parse_color(options.background)
        sprite.pixels[sprite.pixels[..., 3] == 0] = bg

    meta = {"convert": options.to_dict()}
    if not isinstance(source, Image.Image):
        meta = {"source": portable_path(source), **meta}
    return Art(name, [sprite], meta=meta)


def prepare(source: str | Path | Image.Image, options: ConvertOptions) -> tuple[np.ndarray, int]:
    """Carrega e encaixa a imagem na resolução de trabalho. Retorna (RGBA uint8, K)."""
    if isinstance(source, Image.Image):
        image = ImageOps.exif_transpose(source).convert("RGBA")
    else:
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGBA")

    if options.mask:
        with Image.open(options.mask) as m:
            mask = m.convert("L").resize(image.size, Image.Resampling.BILINEAR)
        alpha = np.minimum(np.array(image.getchannel("A")), np.array(mask))
        image.putalpha(Image.fromarray(alpha.astype(np.uint8), "L"))
    if options.crop:
        image = image.crop(crop_box(options.crop, image.size))
    image.thumbnail((MAX_SOURCE, MAX_SOURCE), Image.Resampling.LANCZOS)

    if options.remove_bg:
        image = remove_background(image, options.remove_bg, options.bg_tolerance)
    if options.trim:
        bbox = image.getchannel("A").point(lambda a: 255 if a >= options.alpha_threshold else 0).getbbox()
        if bbox:
            image = image.crop(bbox)

    image = enhance(image, options.contrast, options.saturation, options.sharpness)

    k = work_factor(options.size)
    tw, th = options.size
    margin = k if options.outline else 0
    resample = Image.Resampling.NEAREST if options.resample == "nearest" else Image.Resampling.LANCZOS
    work = fit(image, (tw * k, th * k), options.fit, resample, margin)
    return np.array(work, dtype=np.uint8), k


def crop_box(box: tuple[float, float, float, float], size: tuple[int, int]) -> tuple[int, int, int, int]:
    """Frações (todos ≤ 1) ou pixels → caixa (esquerda, topo, direita, base) em pixels."""
    x, y, w, h = box
    if max(box) <= 1:
        x, y, w, h = x * size[0], y * size[1], w * size[0], h * size[1]
    left, top = max(0, round(x)), max(0, round(y))
    right, bottom = min(size[0], round(x + w)), min(size[1], round(y + h))
    if right <= left or bottom <= top:
        raise ValueError(f"crop fora da imagem: {box}")
    return left, top, right, bottom


# --------------------------------------------------------------------------
# Etapas
# --------------------------------------------------------------------------


def remove_background(image: Image.Image, mode: str, tolerance: int) -> Image.Image:
    """Torna transparente a região conectada à borda com a cor de fundo.

    O flood-fill roda numa cópia ≤ 384 px e a máscara é ampliada de volta.
    """
    small = image.copy()
    small.thumbnail((384, 384), Image.Resampling.BILINEAR)
    px = np.array(small, dtype=np.int32)
    h, w = px.shape[:2]
    if mode == "auto":
        corners = np.array([px[0, 0], px[0, w - 1], px[h - 1, 0], px[h - 1, w - 1]])
        bg = np.median(corners[:, :3], axis=0)
    else:
        bg = np.array(pal.parse_color(mode)[:3])
    close = (np.abs(px[..., :3] - bg).max(axis=-1) <= tolerance) | (px[..., 3] == 0)

    reached = np.zeros((h, w), dtype=bool)
    stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if 0 <= x < w and 0 <= y < h and close[y, x] and not reached[y, x]:
            reached[y, x] = True
            stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    keep = Image.fromarray(np.where(reached, 0, 255).astype(np.uint8), "L").resize(image.size, Image.Resampling.NEAREST)
    out = image.copy()
    out.putalpha(Image.fromarray(np.minimum(np.array(image.getchannel("A")), np.array(keep)), "L"))
    return out


def enhance(image: Image.Image, contrast: float, saturation: float, sharpness: float) -> Image.Image:
    alpha = image.getchannel("A")
    rgb = image.convert("RGB")
    if contrast != 1.0:
        rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    if saturation != 1.0:
        rgb = ImageEnhance.Color(rgb).enhance(saturation)
    if sharpness != 1.0:
        rgb = ImageEnhance.Sharpness(rgb).enhance(sharpness)
    rgb.putalpha(alpha)
    return rgb


def fit(image: Image.Image, size: tuple[int, int], mode: str, resample, margin: int = 0) -> Image.Image:
    tw, th = size
    inner_w, inner_h = max(tw - 2 * margin, 1), max(th - 2 * margin, 1)
    if mode == "stretch":
        scaled = image.resize((inner_w, inner_h), resample)
    elif mode == "cover":
        scaled = ImageOps.fit(image, (inner_w, inner_h), resample)
    else:
        ratio = min(inner_w / image.width, inner_h / image.height)
        new = (max(1, round(image.width * ratio)), max(1, round(image.height * ratio)))
        scaled = image.resize(new, resample)
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    canvas.paste(scaled, ((tw - scaled.width) // 2, (th - scaled.height) // 2))
    return canvas


def focus_weights(shape: tuple[int, int], focus, weight: float) -> np.ndarray:
    w = np.ones(shape)
    if focus:
        h, wd = shape
        left, top, right, bottom = crop_box(focus, (wd, h))
        w[top:bottom, left:right] = weight
    return w


def resolve_palette(spec: int | str, opaque_rgb: np.ndarray, palette_dirs: Iterable[Path] = (),
                    weights: np.ndarray | None = None) -> np.ndarray:
    """Paleta nomeada ou adaptativa (k-means OKLab só sobre pixels opacos). Retorna (N, 3)."""
    if isinstance(spec, str) and not spec.isdigit():
        return np.array([c[:3] for c in pal.get(spec, palette_dirs) if c[3] > 0], dtype=np.int32)
    if len(opaque_rgb) == 0:
        return np.array([[0, 0, 0]], dtype=np.int32)
    return kmeans_palette(opaque_rgb, int(spec), weights)


def detail_downscale(labels: np.ndarray, opaque: np.ndarray, lab: np.ndarray, colors_lab: np.ndarray,
                     k: int, detail: float, edge_spread: float = 0.25) -> tuple[np.ndarray, np.ndarray]:
    """Redução híbrida por blocos k×k.

    Blocos lisos (pele, camiseta): cor média do bloco → áreas uniformes, sem manchas.
    Blocos com borda (olhos, boca, contorno do cabelo): cor dominante por voto,
    com peso extra para a minoria bem mais escura e para o centro do bloco →
    traços finos não somem nem borram.
    """
    lab_idx = blocks(labels, k)
    op_b = blocks(opaque, k)
    lab_b = blocks(lab, k)
    out_opaque = op_b.mean(axis=2) >= 0.5

    n_op = np.maximum(op_b.sum(axis=2, keepdims=True), 1)
    mean_lab = (lab_b * op_b[..., None]).sum(axis=2) / n_op
    mean_idx = nearest_lab(mean_lab, colors_lab)

    l_b = np.where(op_b, lab_b[..., 0], mean_lab[..., :1])
    spread = np.percentile(l_b, 90, axis=2) - np.percentile(l_b, 10, axis=2)
    edgy = spread > edge_spread

    darker = np.clip((mean_lab[..., :1] - l_b - 0.04) / 0.08, 0, 2)
    votes = (1 + detail * darker) * center_weights(k)[None, None, :] * op_b
    n_colors = len(colors_lab)
    scores = np.zeros(lab_idx.shape[:2] + (n_colors,))
    for c in range(n_colors):
        scores[..., c] = (votes * (lab_idx == c)).sum(axis=2)
    return np.where(edgy, scores.argmax(axis=2), mean_idx), out_opaque


def quantize_index(rgb: np.ndarray, opaque: np.ndarray, colors: np.ndarray, colors_lab: np.ndarray,
                   dither: str, strength: float) -> np.ndarray:
    h, w = rgb.shape[:2]
    if dither in ("bayer2", "bayer4"):
        matrix = BAYER2 if dither == "bayer2" else BAYER4
        n = matrix.shape[0]
        tiled = np.tile(matrix, (h // n + 1, w // n + 1))[:h, :w] - 0.5
        shifted = np.clip(rgb.astype(np.float64) + tiled[..., None] * 96 * strength, 0, 255)
        return nearest_lab(srgb_to_oklab(shifted), colors_lab)
    if dither == "floyd":
        return _floyd_steinberg(rgb, opaque, colors, colors_lab)
    return nearest_lab(srgb_to_oklab(rgb), colors_lab)


def _floyd_steinberg(rgb: np.ndarray, opaque: np.ndarray, colors: np.ndarray, colors_lab: np.ndarray) -> np.ndarray:
    """Difusão de erro restrita aos pixels opacos (não vaza para o fundo)."""
    work = rgb.astype(np.float64)
    out = np.zeros(rgb.shape[:2], dtype=np.int64)
    h, w = rgb.shape[:2]
    for y in range(h):
        for x in range(w):
            old = np.clip(work[y, x], 0, 255)
            i = int(nearest_lab(srgb_to_oklab(old[None, :]), colors_lab)[0])
            out[y, x] = i
            if not opaque[y, x]:
                continue
            err = old - colors[i]
            for dx, dy, kk in ((1, 0, 7), (-1, 1, 3), (0, 1, 5), (1, 1, 1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and ny < h and opaque[ny, nx]:
                    work[ny, nx] += err * kk / 16
    return out


def apply_lines(index: np.ndarray, opaque: np.ndarray, lab_hi: np.ndarray, opaque_hi: np.ndarray,
                colors_lab: np.ndarray, k: int, strength: float, threshold: float) -> np.ndarray:
    """Escurece pixels atravessados por bordas fortes da foto, só do lado escuro da borda.

    O pixel troca para a cor da paleta mais próxima de (L - 0.12·força, a, b):
    um tom mais escuro do mesmo material, como o traço de um artista.
    """
    edges = sobel(np.where(opaque_hi, lab_hi[..., 0], 0))
    edges[~opaque_hi] = 0
    ref = np.percentile(edges[opaque_hi], 98) if opaque_hi.any() else 1.0
    strong = edges >= max(ref, 1e-6) * (0.25 + 0.6 * threshold)
    frac = blocks(strong, k).mean(axis=2)
    flagged = (frac >= 1.5 / k) & opaque

    grid_l = colors_lab[index][..., 0]
    padded = np.pad(np.where(opaque, grid_l, np.nan), 1, constant_values=np.nan)
    neighbors = np.stack([padded[:-2, 1:-1], padded[2:, 1:-1], padded[1:-1, :-2], padded[1:-1, 2:]])
    count = (~np.isnan(neighbors)).sum(axis=0)
    local = np.where(count > 0, np.nansum(neighbors, axis=0) / np.maximum(count, 1), np.nan)
    dark_side = grid_l <= np.nan_to_num(local, nan=1.0)

    target = colors_lab[index].copy()
    target[..., 0] -= 0.12 * strength
    darker = nearest_lab(target, colors_lab)
    darker_ok = colors_lab[darker][..., 0] < grid_l - 0.02
    result = index.copy()
    pick = flagged & dark_side & darker_ok
    result[pick] = darker[pick]
    return result
