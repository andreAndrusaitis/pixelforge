"""Exportação: PNG, JPG, WebP, GIF, SVG, escalas e preview com grade.

Formatos estáticos com vários frames viram sprite sheet horizontal;
GIF e WebP ficam animados quando há mais de um frame.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from .palettes import parse_color
from .sprite import Art, Sprite

FORMATS = ("png", "jpg", "webp", "gif", "svg")
PREVIEW_TARGET = 512  # lado aproximado do preview, em px


@dataclass
class ExportOptions:
    formats: list[str] = field(default_factory=lambda: ["png"])
    scales: list[int] = field(default_factory=lambda: [1])
    preview: bool = True
    jpg_background: str = "#ffffff"
    jpg_quality: int = 95

    def validate(self) -> None:
        bad = [f for f in self.formats if f not in FORMATS]
        if bad:
            raise ValueError(f"formato(s) não suportado(s): {', '.join(bad)}. Use: {', '.join(FORMATS)}")
        if any(s < 1 for s in self.scales):
            raise ValueError("escalas devem ser >= 1")


def export(art: Art, out_dir: str | Path, options: ExportOptions) -> list[Path]:
    options.validate()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet = sprite_sheet(art)
    animated = len(art.frames) > 1
    written: list[Path] = []

    for fmt in options.formats:
        if fmt == "svg":
            path = out_dir / f"{art.name}.svg"
            path.write_text(to_svg(sheet, max(options.scales)), encoding="utf-8")
            written.append(path)
            continue
        for scale in options.scales:
            suffix = "" if scale == 1 else f"@{scale}x"
            path = out_dir / f"{art.name}{suffix}.{fmt}"
            if fmt == "gif":
                save_gif(art, path, scale)
            elif fmt == "webp" and animated:
                frames = [upscale(f.to_image(), scale) for f in art.frames]
                frames[0].save(path, save_all=True, append_images=frames[1:],
                               duration=_duration(art), loop=0, lossless=True)
            elif fmt == "webp":
                upscale(sheet.to_image(), scale).save(path, lossless=True)
            elif fmt == "jpg":
                flatten(upscale(sheet.to_image(), scale), options.jpg_background).save(
                    path, quality=options.jpg_quality, subsampling=0)
            else:
                upscale(sheet.to_image(), scale).save(path)
            written.append(path)

    if options.preview:
        path = out_dir / f"{art.name}_preview.png"
        preview(sheet).save(path)
        written.append(path)
    return written


def sprite_sheet(art: Art) -> Sprite:
    if len(art.frames) == 1:
        return art.frames[0]
    return Sprite(np.concatenate([f.pixels for f in art.frames], axis=1))


def upscale(image: Image.Image, scale: int) -> Image.Image:
    if scale == 1:
        return image
    return image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)


def flatten(image: Image.Image, background: str) -> Image.Image:
    base = Image.new("RGBA", image.size, parse_color(background))
    return Image.alpha_composite(base, image.convert("RGBA")).convert("RGB")


def _duration(art: Art) -> int:
    return max(1, round(1000 / max(art.fps, 1)))


def save_gif(art: Art, path: Path, scale: int) -> None:
    """GIF com paleta explícita: índice 0 = transparente."""
    colors = [c[:3] for c in art.colors()]
    if len(colors) > 255:
        raise ValueError("GIF suporta no máximo 255 cores opacas")
    lookup = {c: i + 1 for i, c in enumerate(colors)}
    flat_palette = [0, 0, 0] + [v for c in colors for v in c]
    flat_palette += [0] * (768 - len(flat_palette))

    frames = []
    for sprite in art.frames:
        idx = np.zeros((sprite.height, sprite.width), dtype=np.uint8)
        for y in range(sprite.height):
            for x in range(sprite.width):
                px = sprite.pixels[y, x]
                if px[3] > 0:
                    idx[y, x] = lookup[(int(px[0]), int(px[1]), int(px[2]))]
        image = Image.fromarray(idx, "P")
        image.putpalette(flat_palette)
        frames.append(upscale(image, scale))

    extra = {"save_all": True, "append_images": frames[1:], "duration": _duration(art),
             "loop": 0, "disposal": 2} if len(frames) > 1 else {}
    frames[0].save(path, transparency=0, optimize=False, **extra)


def to_svg(sprite: Sprite, scale: int = 1) -> str:
    """Um <rect> por sequência horizontal de pixels iguais."""
    w, h = sprite.width, sprite.height
    rects = []
    for y in range(h):
        x = 0
        while x < w:
            px = sprite.pixels[y, x]
            run = 1
            while x + run < w and np.array_equal(sprite.pixels[y, x + run], px):
                run += 1
            if px[3] > 0:
                fill = f"#{px[0]:02x}{px[1]:02x}{px[2]:02x}"
                opacity = "" if px[3] == 255 else f' fill-opacity="{px[3] / 255:.3f}"'
                rects.append(f'<rect x="{x}" y="{y}" width="{run}" height="1" fill="{fill}"{opacity}/>')
            x += run
    body = "\n  ".join(rects)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * scale}" height="{h * scale}" '
        f'viewBox="0 0 {w} {h}" shape-rendering="crispEdges">\n  {body}\n</svg>\n'
    )


def preview(sprite: Sprite) -> Image.Image:
    """Ampliação com fundo xadrez (transparência) e grade a cada pixel; linha
    mais forte a cada 8 pixels para facilitar contar coordenadas."""
    scale = max(4, PREVIEW_TARGET // max(sprite.width, sprite.height))
    w, h = sprite.width * scale, sprite.height * scale

    ys, xs = np.mgrid[0:h, 0:w]
    checker = (((xs // (scale // 2 or 1)) + (ys // (scale // 2 or 1))) % 2).astype(bool)
    bg = np.where(checker[..., None], 205, 245).repeat(3, axis=-1).astype(np.uint8)
    base = Image.fromarray(np.dstack([bg, np.full((h, w), 255, np.uint8)]), "RGBA")
    image = Image.alpha_composite(base, upscale(sprite.to_image(), scale))

    px = np.array(image)
    for i in range(sprite.width + 1):
        col = min(i * scale, w - 1)
        px[:, col, :3] = px[:, col, :3] * (0.55 if i % 8 == 0 else 0.82)
    for j in range(sprite.height + 1):
        row = min(j * scale, h - 1)
        px[row, :, :3] = px[row, :, :3] * (0.55 if j % 8 == 0 else 0.82)
    return Image.fromarray(px, "RGBA")
