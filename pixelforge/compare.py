"""Compara uma pixel art com a foto de referência.

A foto passa pelo mesmo preparo da conversão (máscara, recorte, encaixe) e é
reduzida por média para a grade da arte. Notas (0–100):
  cor    diferença média em OKLab nos pixels em comum
  traços correlação entre as bordas das duas imagens
  forma  sobreposição das silhuetas (IoU)
  total  0.5·cor + 0.3·traços + 0.2·forma

E, à parte, qualidade de pixel art:
  limpeza  % de pixels que têm ao menos um vizinho ortogonal da mesma cor
           (manchas e ruído derrubam; borrado não é premiado aqui)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .color import srgb_to_oklab
from .convert import ConvertOptions, prepare
from .filters import sobel
from .sprite import Sprite


@dataclass
class Similarity:
    color: float
    edges: float
    shape: float
    clean: float = 100.0

    @property
    def total(self) -> float:
        return 0.5 * self.color + 0.3 * self.edges + 0.2 * self.shape

    def __str__(self) -> str:
        return (f"semelhança {self.total:.1f}/100  (cor {self.color:.1f}, "
                f"traços {self.edges:.1f}, forma {self.shape:.1f})  |  limpeza {self.clean:.1f}/100")


def reference_grid(source: str | Path | Image.Image, options: ConvertOptions) -> np.ndarray:
    """A foto reduzida por média para o tamanho da arte (RGBA uint8)."""
    work, _ = prepare(source, options)
    small = Image.fromarray(work, "RGBA").resize(tuple(options.size), Image.Resampling.BOX)
    return np.array(small, dtype=np.uint8)


def similarity(reference: np.ndarray, art: Sprite, alpha_threshold: int = 128) -> Similarity:
    ref_op = reference[..., 3] >= alpha_threshold
    art_op = art.pixels[..., 3] > 0
    both = ref_op & art_op
    union = ref_op | art_op
    shape = 100.0 * both.sum() / max(union.sum(), 1)
    clean = cleanliness(art)
    if not both.any():
        return Similarity(0.0, 0.0, shape, clean)

    ref_lab = srgb_to_oklab(reference[..., :3])
    art_lab = srgb_to_oklab(art.pixels[..., :3])
    delta = np.sqrt(((ref_lab - art_lab) ** 2).sum(axis=-1))[both].mean()
    color = 100.0 * max(0.0, 1.0 - delta / 0.25)

    e_ref = sobel(np.where(ref_op, ref_lab[..., 0], 0))[both]
    e_art = sobel(np.where(art_op, art_lab[..., 0], 0))[both]
    if e_ref.std() < 1e-9 or e_art.std() < 1e-9:
        edges = 100.0 if np.allclose(e_ref, e_art) else 0.0
    else:
        edges = 100.0 * max(0.0, float(np.corrcoef(e_ref, e_art)[0, 1]))
    return Similarity(color, edges, shape, clean)


def cleanliness(art: Sprite) -> float:
    """% de pixels opacos com pelo menos um vizinho ortogonal de cor idêntica."""
    px = art.pixels.astype(np.int64)
    key = ((px[..., 0] * 256 + px[..., 1]) * 256 + px[..., 2]) * 256 + px[..., 3]
    opaque = px[..., 3] > 0
    if not opaque.any():
        return 100.0
    padded = np.pad(key, 1, constant_values=-1)
    same = np.zeros(key.shape, dtype=bool)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        same |= padded[1 + dy : 1 + dy + key.shape[0], 1 + dx : 1 + dx + key.shape[1]] == key
    return 100.0 * same[opaque].mean()


def compare_image(reference: np.ndarray, art: Sprite, panel: int = 320) -> Image.Image:
    """Três painéis: foto reduzida | pixel art | sobreposição 50%."""
    h, w = art.height, art.width
    scale = max(1, panel // max(w, h))
    size = (w * scale, h * scale)

    def checker(img: np.ndarray) -> Image.Image:
        ys, xs = np.mgrid[0 : size[1], 0 : size[0]]
        cell = max(scale // 2, 2)
        bg = np.where((((xs // cell) + (ys // cell)) % 2)[..., None] == 1, 205, 245).repeat(3, -1)
        base = Image.fromarray(np.dstack([bg, np.full(bg.shape[:2], 255)]).astype(np.uint8), "RGBA")
        layer = Image.fromarray(img, "RGBA").resize(size, Image.Resampling.NEAREST)
        return Image.alpha_composite(base, layer)

    ref_img = checker(reference)
    art_img = checker(art.pixels)
    overlay = Image.blend(ref_img, art_img, 0.5)

    gap, label_h = 12, 22
    sheet = Image.new("RGBA", (size[0] * 3 + gap * 4, size[1] + label_h + gap * 2), (30, 30, 36, 255))
    draw = ImageDraw.Draw(sheet)
    for i, (img, label) in enumerate(((ref_img, "foto"), (art_img, "pixel art"), (overlay, "sobreposicao"))):
        x = gap + i * (size[0] + gap)
        sheet.paste(img, (x, gap + label_h))
        draw.text((x, gap), label, fill=(230, 230, 230, 255))
    return sheet
