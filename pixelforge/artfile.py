"""Carrega uma arte de arquivo: spec `.json`, script `.py` (com build()) ou imagem."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from PIL import Image

from .draw import Canvas
from .sprite import Art, Sprite, load_spec

ART_SUFFIXES = (".json", ".py", ".png", ".gif", ".webp")


def load_art(path: Path) -> Art:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"arquivo não encontrado: {path}")
    if path.suffix.lower() == ".json":
        return load_spec(path)
    if path.suffix.lower() == ".py":
        return load_script(path)
    if path.suffix.lower() in (".png", ".gif", ".webp"):
        with Image.open(path) as opened:
            return Art(path.stem, [Sprite.from_image(opened)])
    raise ValueError(f"{path}: use .json (spec), .py (script com build()) ou .png")


def load_script(path: Path) -> Art:
    spec = importlib.util.spec_from_file_location(f"pixelforge_art_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    build = getattr(module, "build", None)
    if not callable(build):
        raise ValueError(f"{path}: o script precisa definir build()")
    art = to_art(build(), getattr(module, "NAME", path.stem), getattr(module, "FPS", 8))
    # sprites de cena: ANCHOR = [x, y] do "pé"; ANIMATIONS = {"andar": {"frames": [...], "fps": 8}}
    for constant, key in (("ANCHOR", "anchor"), ("ANIMATIONS", "animations")):
        if hasattr(module, constant):
            art.meta[key] = getattr(module, constant)
    return art


def to_art(result, name: str, fps: int) -> Art:
    if isinstance(result, Art):
        return result
    items = result if isinstance(result, (list, tuple)) else [result]
    frames = []
    for item in items:
        if isinstance(item, Canvas):
            frames.append(item.sprite.copy())
        elif isinstance(item, Sprite):
            frames.append(item)
        else:
            raise ValueError(f"build() deve retornar Canvas, Sprite, Art ou lista deles, não {type(item).__name__}")
    return Art(name, frames, fps)
