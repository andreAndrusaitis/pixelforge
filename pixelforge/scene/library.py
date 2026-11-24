"""Biblioteca de artes da cena: resolve caminhos e monta cenários em camadas.

Caminhos no roteiro são relativos à pasta do arquivo que os cita (roteiro ou
cenário) e, depois, à pasta `art/`. A extensão é opcional (.json, .py, .png).

Um cenário é um JSON com `camadas` (de trás para a frente):

    {"name": "patio", "size": [640, 180], "camadas": [
        {"arte": "ceu", "parallax": 0.1, "repetir": "x"},
        {"arte": "chao"},
        {"arte": "folhas", "parallax": 1.3, "frente": true}]}

Qualquer arte simples (spec, script ou imagem) vira um cenário de 1 camada.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..artfile import ART_SUFFIXES, load_art
from ..sprite import Art
from .actors import SpriteSheet, sheet_from_art
from .script import AISpec, SceneError, _point, check_keys, parse_ai

BACKDROP_KEYS = ("name", "size", "camadas")
LAYER_KEYS = ("arte", "parallax", "pos", "repetir", "frente", "fps", "ia")
REPEAT = {False: "", True: "x", "": "", "x": "x", "y": "y", "xy": "xy"}


@dataclass
class Layer:
    frames: list[np.ndarray]          # RGBA uint8 (altura, largura, 4)
    fps: int = 8
    parallax: float = 1.0
    pos: tuple[int, int] = (0, 0)
    repeat: str = ""                  # "", "x", "y" ou "xy"
    front: bool = False
    name: str = ""
    ai: AISpec | None = None          # animação por IA (preparada antes do render)
    loop: str = "repetir"             # repetir | vaivem | segurar

    @property
    def size(self) -> tuple[int, int]:
        return self.frames[0].shape[1], self.frames[0].shape[0]

    def frame_at(self, t: float) -> np.ndarray:
        if len(self.frames) == 1:
            return self.frames[0]
        return self.frames[loop_index(int(t * self.fps + 1e-9), len(self.frames), self.loop)]


def loop_index(step: int, n: int, mode: str) -> int:
    """Quadro `step` de um clipe de `n` quadros: repetir, vaivem (ida e volta) ou segurar o último."""
    if n <= 1:
        return 0
    if mode == "segurar":
        return min(max(step, 0), n - 1)
    if mode == "vaivem":
        period = 2 * (n - 1)
        k = step % period
        return k if k < n else period - k
    return step % n


@dataclass
class Backdrop:
    name: str
    layers: list[Layer]
    size: tuple[int | None, int | None]   # None = sem limite (camadas repetidas)


class Library:
    def __init__(self, art_dir: Path | None = None):
        self.art_dir = Path(art_dir) if art_dir else None
        self._arts: dict[Path, Art] = {}
        self._backdrops: dict[str, Backdrop] = {}
        self._sheets: dict[Path, SpriteSheet] = {}

    # -- caminhos -----------------------------------------------------------

    def resolve(self, ref: str, base: Path | None) -> Path:
        ref_path = Path(ref)
        folders = [] if ref_path.is_absolute() else [f for f in (base, self.art_dir) if f is not None]
        candidates = [ref_path] if ref_path.is_absolute() else [f / ref_path for f in folders]
        tried = []
        for candidate in candidates:
            options = [candidate] if candidate.suffix.lower() in ART_SUFFIXES else []
            options += [candidate.with_name(candidate.name + s) for s in ART_SUFFIXES[:3]]
            for option in options:
                tried.append(option)
                if option.is_file():
                    return option
        where = ", ".join(str(f) for f in folders) or "caminho absoluto"
        raise FileNotFoundError(f"arte '{ref}' não encontrada (procurado em: {where}; extensões .json/.py/.png)")

    def art(self, path: Path) -> Art:
        path = path.resolve()
        if path not in self._arts:
            self._arts[path] = load_art(path)
        return self._arts[path]

    def sprite(self, ref: str, base: Path | None) -> SpriteSheet:
        """Sprite de ator (animações + âncora), com cache."""
        path = self.resolve(ref, base).resolve()
        if path not in self._sheets:
            self._sheets[path] = sheet_from_art(self.art(path))
        return self._sheets[path]

    def image(self, ref: str, base: Path | None) -> np.ndarray:
        """Primeiro frame de uma arte (retratos)."""
        return self.art(self.resolve(ref, base)).frames[0].pixels

    # -- cenários -----------------------------------------------------------

    def backdrop(self, ref: str | dict, base: Path | None) -> Backdrop:
        """`ref`: caminho (arte ou cenário .json com camadas) ou objeto inline."""
        if isinstance(ref, dict):
            return self._parse_backdrop(ref, base, "cenário inline")
        path = self.resolve(ref, base)
        key = str(path.resolve())
        if key not in self._backdrops:
            data = _read_json(path) if path.suffix.lower() == ".json" else None
            if isinstance(data, dict) and "camadas" in data:
                try:
                    backdrop = self._parse_backdrop(data, path.parent, path.stem)
                except SceneError as exc:
                    raise SceneError(f"{path.name}: {exc}") from None
            else:
                art = self.art(path)
                backdrop = Backdrop(art.name, [_layer_from_art(art)], art.size)
            self._backdrops[key] = backdrop
        return self._backdrops[key]

    def _parse_backdrop(self, data: dict, base: Path | None, default_name: str) -> Backdrop:
        check_keys(data, BACKDROP_KEYS, "cenário")
        raw_layers = data.get("camadas")
        if not isinstance(raw_layers, list) or not raw_layers:
            raise SceneError("cenário: 'camadas' deve ser lista com ao menos uma camada")
        layers = [self._parse_layer(raw, i + 1, base) for i, raw in enumerate(raw_layers)]
        size = data.get("size")
        if size is not None:
            if isinstance(size, int):
                size = [size, size]
            size = _point(size, "cenário.size")
        return Backdrop(data.get("name") or default_name, layers, size or world_size(layers))

    def _parse_layer(self, raw, index: int, base: Path | None) -> Layer:
        where = f"camada {index}"
        if isinstance(raw, str):
            raw = {"arte": raw}
        if not isinstance(raw, dict):
            raise SceneError(f"{where}: esperado objeto com 'arte'")
        try:
            check_keys(raw, LAYER_KEYS, where)
            if "arte" not in raw:
                raise SceneError("'arte' é obrigatório")
            art = self.art(self.resolve(raw["arte"], base))
            layer = _layer_from_art(art)
            parallax = raw.get("parallax", 1.0)
            if isinstance(parallax, bool) or not isinstance(parallax, (int, float)) or not 0 <= parallax <= 4:
                raise SceneError(f"parallax: esperado número entre 0 e 4, não {parallax!r}")
            layer.parallax = float(parallax)
            if "pos" in raw:
                layer.pos = _point(raw["pos"], "pos")
            repeat = raw.get("repetir", False)
            if not isinstance(repeat, (bool, str)) or repeat not in REPEAT:
                raise SceneError(f"repetir: use false, true (= \"x\"), \"x\", \"y\" ou \"xy\", não {repeat!r}")
            layer.repeat = REPEAT[repeat]
            front = raw.get("frente", False)
            if not isinstance(front, bool):
                raise SceneError(f"frente: esperado true ou false, não {front!r}")
            layer.front = front
            if "ia" in raw:
                layer.ai = parse_ai(raw["ia"], "ia", layer=True)
                layer.name = str(raw["arte"])
            if "fps" in raw:
                fps = raw["fps"]
                if isinstance(fps, bool) or not isinstance(fps, int) or not 1 <= fps <= 60:
                    raise SceneError(f"fps: esperado inteiro entre 1 e 60, não {fps!r}")
                layer.fps = fps
        except SceneError as exc:
            raise SceneError(f"{where} ('{raw.get('arte', '?')}'): {exc}") from None
        return layer


def world_size(layers: list[Layer]) -> tuple[int | None, int | None]:
    """Tamanho do cenário: extensão das camadas de parallax 1 (ou de todas, se
    nenhuma tiver parallax 1). Eixo em que todas repetem não tem limite."""
    main = [l for l in layers if l.parallax == 1.0] or layers
    size: list[int | None] = []
    for axis, letter in ((0, "x"), (1, "y")):
        fixed = [l for l in main if letter not in l.repeat]
        size.append(max(l.pos[axis] + l.size[axis] for l in fixed) if fixed else None)
    return size[0], size[1]


def _layer_from_art(art: Art) -> Layer:
    return Layer([f.pixels for f in art.frames], art.fps, name=art.name)


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SceneError(f"{path}: JSON inválido ({exc})") from None
