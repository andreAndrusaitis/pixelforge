"""Clipes por IA com cache e nota de estilo.

`make_clip` é o ponto de entrada: imagem em pixel art + descrição do movimento →
quadros já pixelizados (paleta travada da própria imagem), com

- **cache por hash** (imagem, descrição, duração, semente, modelo, passos): o clipe bruto
  da IA fica em `<cache>/<hash>.npz`; pixelizar de novo é rápido e não regera;
- **nota técnica** (`estilo comparar`): quadros de amostra do clipe pixelizado são
  avaliados contra as referências do tipo pedido; nota < 85 (ou abaixo da própria
  imagem de partida, se ela já estiver abaixo de 85) gera de novo com outra semente,
  até 3 tentativas; fica a de maior nota.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from .pixelize import PixelizeOptions, flicker, palette_of, pixelize_clip

MIN_SCORE = 85.0
ATTEMPTS = 3
SAMPLES = 3                # quadros avaliados por clipe
UPSCALE_TARGET = 832       # a imagem de pixel art é ampliada (vizinho) até ~este lado antes da IA


@dataclass
class ClipResult:
    frames: list[np.ndarray]                 # quadros nativos (RGB ou RGBA) no fps pedido
    fps: int
    seed: int
    score: float | None = None
    base_score: float | None = None
    attempts: list[dict] = field(default_factory=list)   # {semente, nota, tempo, cache}
    flicker: float = 0.0

    def describe(self) -> str:
        parts = [f"{len(self.frames)} quadros a {self.fps} fps", f"semente {self.seed}"]
        if self.score is not None:
            parts.append(f"nota técnica {self.score:g}" + (f" (imagem original {self.base_score:g})"
                                                           if self.base_score is not None else ""))
        parts.append(f"cintilação {self.flicker:.1%}")
        return ", ".join(parts)


def clip_key(image: np.ndarray, prompt: str, seconds: float, seed: int, steps: int, long_side: int) -> str:
    from .wan import GGUF_FILE, REPO
    h = hashlib.sha1()
    h.update(np.ascontiguousarray(image).tobytes())
    h.update(json.dumps([image.shape, prompt, round(seconds, 3), seed, steps, long_side, REPO, GGUF_FILE],
                        ensure_ascii=False).encode("utf-8"))
    return h.hexdigest()[:20]


def ai_input(image: np.ndarray, background: tuple[int, int, int] | None = None) -> Image.Image:
    """Pixel art (RGB/RGBA nativo) → imagem grande para a IA (vizinho mais próximo; alfa sobre `background`)."""
    rgba = image if image.shape[-1] == 4 else np.dstack([image, np.full(image.shape[:2], 255, np.uint8)])
    bg = np.array(background or (0, 0, 0), np.float32)
    a = rgba[..., 3:4].astype(np.float32) / 255
    rgb = (rgba[..., :3] * a + bg * (1 - a)).round().astype(np.uint8)
    k = max(1, UPSCALE_TARGET // max(rgb.shape[:2]))
    return Image.fromarray(np.kron(rgb, np.ones((k, k, 1), np.uint8)), "RGB")


def load_raw(path: Path) -> tuple[list[np.ndarray], dict] | None:
    if not path.is_file():
        return None
    with np.load(path, allow_pickle=False) as data:
        frames = list(data["frames"])
        meta = json.loads(str(data["meta"]))
    return frames, meta


def save_raw(path: Path, frames: list[np.ndarray], meta: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, frames=np.stack(frames), meta=json.dumps(meta, ensure_ascii=False))


def technical_score(frames: list[np.ndarray], tipo: str, config) -> float | None:
    """Média da nota técnica (`estilo comparar`) de quadros de amostra; None sem referências."""
    from ..style.analyze import analyze_array
    from ..style.cli import style_dir
    from ..style.compare import load_references, score

    refs = load_references(style_dir(config) / "referencias.json", style_dir(config) / "analises")
    if len(refs) < 5:
        return None
    picks = sorted({0, len(frames) // 2, len(frames) - 1})[:SAMPLES]
    notes = []
    for i in picks:
        rgba = frames[i] if frames[i].shape[-1] == 4 else np.dstack(
            [frames[i], np.full(frames[i].shape[:2], 255, np.uint8)])
        metrics, _ = analyze_array(rgba, native=True)
        notes.append(score(metrics, refs, tipo).nota)
    return round(float(np.mean(notes)), 1)


def make_clip(image: np.ndarray, prompt: str, seconds: float, *, fps: int = 12, seed: int = 0,
              cache_dir: Path, config=None, tipo: str | None = "cena", region: np.ndarray | None = None,
              key: tuple[int, int, int] | None = None, palette: np.ndarray | None = None,
              steps: int | None = None, long_side: int = 832, attempts: int = ATTEMPTS,
              min_score: float = MIN_SCORE, generator=None, log=print) -> ClipResult:
    """Gera (ou lê do cache) e pixeliza um clipe; refaz com outra semente se a nota for baixa.

    `image`: pixel art nativa (RGB, ou RGBA com `key` = cor de fundo do sprite).
    `region`: máscara nativa do que pode mudar (o resto fica como `image`).
    `generator`: objeto com `.generate(PIL, prompt, seconds, seed, long_side)` (padrão: Wan 2.2)."""
    from .wan import STEPS, FPS

    steps = steps or STEPS
    size = (image.shape[1], image.shape[0])
    pal = palette if palette is not None else palette_of(image)
    base_rgb = None if key is not None else image[..., :3]
    options = PixelizeOptions(size, FPS, fps, palette=pal, key=key)
    base_score = technical_score([image], tipo, config) if (tipo and config is not None) else None
    target = min_score if base_score is None else min(min_score, base_score - 2)
    big = ai_input(image, key)

    best: ClipResult | None = None
    history = []
    for attempt in range(max(1, attempts)):
        s = seed + attempt
        path = cache_dir / f"{clip_key(image, prompt, seconds, s, steps, long_side)}.npz"
        cached = load_raw(path)
        t0 = time.time()
        if cached is None:
            if generator is None:
                from .wan import WanI2V
                generator = WanI2V(steps=steps)
            raw, timing = generator.generate(big, prompt, seconds, s, long_side)
            save_raw(path, raw, {"descricao": prompt, "segundos": seconds, "semente": s,
                                 "tempos": timing.__dict__ if hasattr(timing, "__dict__") else {}})
            log(f"  IA: semente {s}, {timing.describe() if hasattr(timing, 'describe') else ''}")
            cached_flag = False
        else:
            raw, meta = cached
            log(f"  IA: semente {s} do cache ({path.name})")
            cached_flag = True
        frames = pixelize_clip(raw, options, base=base_rgb, region=region)
        note = technical_score(frames, tipo, config) if (tipo and config is not None) else None
        result = ClipResult(frames, fps, s, note, base_score, flicker=flicker(frames))
        history.append({"semente": s, "nota": note, "segundos": round(time.time() - t0, 1), "cache": cached_flag})
        if best is None or (note or 0) > (best.score or 0):
            best = result
        if note is None or note >= target:
            break
        log(f"  nota técnica {note:g} < {target:g}: gerando de novo com outra semente")
    best.attempts = history
    return best
