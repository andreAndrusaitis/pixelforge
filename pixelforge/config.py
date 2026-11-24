"""Carrega `pixelforge.toml` (procurando da pasta atual para cima) sobre os padrões."""

from __future__ import annotations

import copy
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_NAME = "pixelforge.toml"

DEFAULTS: dict = {
    "output": {
        "dir": "out",
        "formats": ["png"],
        "scales": [1, 16],
        "preview": True,
        "jpg_background": "#ffffff",
        "jpg_quality": 95,
    },
    "paths": {"art": "art", "palettes": "palettes"},
    "new": {"size": 32, "palette": "pico8"},
    "convert": {"preset": "default"},
    "presets": {"default": {}},
    "cena": {
        "resolucao": "hd",
        "escala": 6,
        "fps": 12,
        "formatos": ["gif", "mp4"],
        "presets": {
            "gba": [240, 160],
            "snes": [256, 224],
            "hd": [320, 180],
            "hd2": [480, 270],
            "hd3": [640, 360],
        },
    },
}


@dataclass
class Config:
    root: Path
    data: dict
    file: Path | None = None

    @property
    def output_dir(self) -> Path:
        return self.root / self.data["output"]["dir"]

    @property
    def art_dir(self) -> Path:
        return self.root / self.data["paths"]["art"]

    @property
    def palette_dirs(self) -> list[Path]:
        return [self.root / self.data["paths"]["palettes"]]

    def preset(self, name: str | None) -> dict:
        name = name or self.data["convert"]["preset"]
        presets = self.data["presets"]
        if name not in presets:
            raise KeyError(f"preset '{name}' não existe. Disponíveis: {', '.join(sorted(presets))}")
        return dict(presets[name])


def find_config(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for folder in (current, *current.parents):
        candidate = folder / CONFIG_NAME
        if candidate.is_file():
            return candidate
    return None


def merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: Path | None = None) -> Config:
    path = path or find_config()
    if path is None:
        return Config(Path.cwd(), copy.deepcopy(DEFAULTS))
    with open(path, "rb") as fh:
        try:
            user = tomllib.load(fh)
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"{path}: TOML inválido ({exc})") from None
    return Config(path.parent, merge(DEFAULTS, user), path)
