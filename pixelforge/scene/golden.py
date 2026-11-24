"""Testes de imagem de referência ("golden"): quadros da cena comparados pixel a pixel.

Um manifesto JSON lista cenas e instantes:

    {"cenas": [{"roteiro": "cena/golden.json", "quadros": [0.5, 2.25, 6.0]}]}

Cada quadro é salvo na resolução lógica (sem ampliar) em
`<pasta do manifesto>/<nome da cena>/t<instante>.png`. `check` compara e, se
algo mudou, grava `<...>_atual.png` e `<...>_diff.png` (pixels diferentes em
magenta) em `saida`; `record` (re)grava as referências.

    python -m pixelforge golden tests/golden/golden.json            # compara
    python -m pixelforge golden tests/golden/golden.json --regravar # aceita o visual novo
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from ..config import Config
from . import open_scene, render_frame

DIFF = (255, 0, 255)


@dataclass
class GoldenResult:
    scene: str
    time: float
    reference: Path
    status: str                  # ok | diferente | faltando | gravado
    changed: int = 0             # pixels diferentes
    box: tuple[int, int, int, int] | None = None   # x0, y0, x1, y1 das diferenças

    def describe(self) -> str:
        where = f"{self.scene} t={self.time:g}s"
        if self.status == "diferente":
            return f"{where}: {self.changed} pixel(s) diferentes em x {self.box[0]}–{self.box[2]}, " \
                   f"y {self.box[1]}–{self.box[3]} ({self.reference.name})"
        if self.status == "faltando":
            return f"{where}: sem referência {self.reference} (rode com --regravar)"
        return f"{where}: {self.status}"


def load_manifest(path: Path) -> list[tuple[Path, list[float]]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    scenes = data.get("cenas") if isinstance(data, dict) else None
    if not isinstance(scenes, list) or not scenes:
        raise ValueError(f"{path}: esperado {{\"cenas\": [{{\"roteiro\": ..., \"quadros\": [s, ...]}}]}}")
    items = []
    for i, entry in enumerate(scenes, 1):
        times = entry.get("quadros")
        if not isinstance(entry.get("roteiro"), str) or not isinstance(times, list) or not times:
            raise ValueError(f"{path}: cenas[{i}] precisa de 'roteiro' e 'quadros' (lista de instantes em s)")
        items.append((Path(path).parent / entry["roteiro"], [float(t) for t in times]))
    return items


def frames(script: Path, times: list[float], config: Config) -> tuple[str, list[np.ndarray]]:
    timeline = open_scene(script, config)
    return timeline.scene.name, [render_frame(timeline, timeline.at(t)) for t in times]


def reference_path(folder: Path, scene: str, t: float) -> Path:
    return folder / scene / f"t{t:g}.png"


def compare(expected: np.ndarray, actual: np.ndarray) -> tuple[int, tuple[int, int, int, int] | None]:
    if expected.shape != actual.shape:
        h, w = actual.shape[:2]
        return h * w, (0, 0, w - 1, h - 1)
    mask = (expected != actual).any(axis=2)
    if not mask.any():
        return 0, None
    ys, xs = np.nonzero(mask)
    return int(mask.sum()), (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def run(manifest: Path, config: Config, record: bool = False, out_dir: Path | None = None) -> list[GoldenResult]:
    folder = Path(manifest).parent
    results = []
    for script, times in load_manifest(manifest):
        name, images = frames(script, times, config)
        for t, image in zip(times, images):
            ref = reference_path(folder, name, t)
            if record:
                ref.parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(image, "RGB").save(ref, optimize=True)
                results.append(GoldenResult(name, t, ref, "gravado"))
                continue
            if not ref.is_file():
                results.append(GoldenResult(name, t, ref, "faltando"))
                continue
            expected = np.array(Image.open(ref).convert("RGB"))
            changed, box = compare(expected, image)
            results.append(GoldenResult(name, t, ref, "ok" if not changed else "diferente", changed, box))
            if changed and out_dir is not None:
                out_dir.mkdir(parents=True, exist_ok=True)
                Image.fromarray(image, "RGB").save(out_dir / f"{name}_t{t:g}_atual.png")
                if expected.shape == image.shape:
                    diff = (image // 3).astype(np.uint8)
                    diff[(expected != image).any(axis=2)] = DIFF
                    Image.fromarray(diff, "RGB").save(out_dir / f"{name}_t{t:g}_diff.png")
    return results
