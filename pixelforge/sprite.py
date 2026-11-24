"""Modelo de dados (Sprite, Art) e o formato de spec JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from .palettes import RGBA, TRANSPARENT, parse_color, to_hex

TRANSPARENT_KEY = "."
# Ordem em que chaves são atribuídas ao gerar specs automaticamente.
SPEC_KEYS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ#@$%&*+=?"


class SpecError(ValueError):
    pass


@dataclass
class Sprite:
    """Um frame: array numpy uint8 (altura, largura, 4) em RGBA."""

    pixels: np.ndarray

    @classmethod
    def blank(cls, width: int, height: int | None = None) -> "Sprite":
        return cls(np.zeros((height or width, width, 4), dtype=np.uint8))

    @classmethod
    def from_image(cls, image: Image.Image) -> "Sprite":
        return cls(np.array(image.convert("RGBA"), dtype=np.uint8))

    @property
    def width(self) -> int:
        return self.pixels.shape[1]

    @property
    def height(self) -> int:
        return self.pixels.shape[0]

    def copy(self) -> "Sprite":
        return Sprite(self.pixels.copy())

    def to_image(self) -> Image.Image:
        return Image.fromarray(self.pixels, "RGBA")

    def colors(self) -> list[RGBA]:
        """Cores opacas, da mais frequente para a menos frequente."""
        flat = self.pixels.reshape(-1, 4)
        opaque = flat[flat[:, 3] > 0]
        if not len(opaque):
            return []
        unique, counts = np.unique(opaque, axis=0, return_counts=True)
        order = np.argsort(-counts, kind="stable")
        return [tuple(int(v) for v in unique[i]) for i in order]


@dataclass
class Art:
    """Uma arte: um ou mais frames do mesmo tamanho."""

    name: str
    frames: list[Sprite]
    fps: int = 8
    meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.frames:
            raise ValueError("Art precisa de pelo menos um frame")
        w, h = self.frames[0].width, self.frames[0].height
        for i, frame in enumerate(self.frames):
            if (frame.width, frame.height) != (w, h):
                raise ValueError(f"frame {i} tem tamanho diferente do frame 0")

    @property
    def size(self) -> tuple[int, int]:
        return self.frames[0].width, self.frames[0].height

    def colors(self) -> list[RGBA]:
        """Cores opacas de todos os frames, da mais frequente para a menos."""
        return Sprite(np.concatenate([f.pixels for f in self.frames], axis=0)).colors()


# --------------------------------------------------------------------------
# Spec JSON
# --------------------------------------------------------------------------


def parse_spec(data: dict, default_name: str = "art") -> Art:
    if "palette" not in data or not isinstance(data["palette"], dict):
        raise SpecError("spec precisa de 'palette' (objeto chave → cor)")

    palette: dict[str, RGBA] = {TRANSPARENT_KEY: TRANSPARENT}
    for key, value in data["palette"].items():
        if len(key) != 1:
            raise SpecError(f"chave de paleta deve ter 1 caractere: {key!r}")
        try:
            palette[key] = parse_color(value)
        except ValueError as exc:
            raise SpecError(f"paleta['{key}']: {exc}") from None

    if "frames" in data:
        frames_rows = data["frames"]
    elif "pixels" in data:
        frames_rows = [data["pixels"]]
    else:
        raise SpecError("spec precisa de 'pixels' ou 'frames'")

    size = data.get("size")
    if isinstance(size, int):
        size = [size, size]

    frames = []
    for f, rows in enumerate(frames_rows):
        where = f"frame {f}, " if len(frames_rows) > 1 else ""
        if not rows:
            raise SpecError(f"{where}grade vazia")
        width = len(rows[0])
        if size and (width, len(rows)) != tuple(size):
            raise SpecError(
                f"{where}grade é {width}x{len(rows)}, mas size é {size[0]}x{size[1]}"
            )
        pixels = np.zeros((len(rows), width, 4), dtype=np.uint8)
        for y, row in enumerate(rows):
            if len(row) != width:
                raise SpecError(f"{where}linha {y}: largura {len(row)}, esperado {width}")
            for x, key in enumerate(row):
                if key not in palette:
                    raise SpecError(f"{where}linha {y}, coluna {x}: chave {key!r} não está na paleta")
                pixels[y, x] = palette[key]
        frames.append(Sprite(pixels))

    meta = {k: v for k, v in data.items() if k not in ("name", "size", "fps", "palette", "pixels", "frames")}
    return Art(data.get("name") or default_name, frames, int(data.get("fps", 8)), meta)


def load_spec(path: str | Path) -> Art:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SpecError(f"{path}: JSON inválido ({exc})") from None
    try:
        return parse_spec(data, default_name=path.stem)
    except SpecError as exc:
        raise SpecError(f"{path}: {exc}") from None


def spec_from_art(art: Art, palette_keys: dict[RGBA, str] | None = None) -> dict:
    """Converte uma Art em spec. Atribui chaves às cores que não tiverem uma."""
    keys: dict[RGBA, str] = dict(palette_keys or {})
    used = set(keys.values()) | {TRANSPARENT_KEY}
    free = (k for k in SPEC_KEYS if k not in used)
    for color in art.colors():
        if color not in keys:
            try:
                keys[color] = next(free)
            except StopIteration:
                raise SpecError(f"cores demais para uma spec (máx. {len(SPEC_KEYS)})") from None

    def rows(sprite: Sprite) -> list[str]:
        out = []
        for line in sprite.pixels:
            out.append(
                "".join(TRANSPARENT_KEY if px[3] == 0 else keys[tuple(int(v) for v in px)] for px in line)
            )
        return out

    spec: dict = {"name": art.name, "size": list(art.size)}
    if len(art.frames) > 1:
        spec["fps"] = art.fps
    # metadados (ex.: "source" e "convert", usados pelo compare) preservados no retoque
    spec.update({k: v for k, v in art.meta.items() if v is not None})
    spec["palette"] = {TRANSPARENT_KEY: "transparent", **{k: to_hex(c) for c, k in keys.items()}}
    if len(art.frames) == 1:
        spec["pixels"] = rows(art.frames[0])
    else:
        spec["frames"] = [rows(f) for f in art.frames]
    return spec


def save_spec(art: Art, path: str | Path, palette_keys: dict[RGBA, str] | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    spec = spec_from_art(art, palette_keys)
    path.write_text(dump_spec(spec), encoding="utf-8")
    return path


def dump_spec(spec: dict) -> str:
    """JSON legível: cada linha da grade em sua própria linha."""
    lines = ["{"]
    items = list(spec.items())
    for i, (key, value) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        if key == "pixels":
            lines.append(f'  "pixels": [\n{_rows_json(value, 4)}\n  ]{comma}')
        elif key == "frames":
            frames = ",\n".join(f"    [\n{_rows_json(rows, 6)}\n    ]" for rows in value)
            lines.append(f'  "frames": [\n{frames}\n  ]{comma}')
        elif key == "palette":
            entries = ",\n".join(f"    {json.dumps(k)}: {json.dumps(v)}" for k, v in value.items())
            lines.append(f'  "palette": {{\n{entries}\n  }}{comma}')
        else:
            lines.append(f"  {json.dumps(key)}: {json.dumps(value, ensure_ascii=False)}{comma}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def _rows_json(rows: list[str], indent: int) -> str:
    pad = " " * indent
    return ",\n".join(f"{pad}{json.dumps(r)}" for r in rows)
