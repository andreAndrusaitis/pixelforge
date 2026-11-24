"""Atores: sprites com várias animações, âncora e espelho.

Formato (spec JSON; em scripts .py use as constantes ANCHOR e ANIMATIONS):

    "anchor": [16, 31],                      ponto do pé (padrão: base central)
    "animations": {
        "parado": {"frames": [0, 1], "fps": 3},
        "andar":  {"frames": [2, 3, 4, 5], "fps": 8},
        "falar":  {"frames": [6, 7], "fps": 6}
    }

Sprites são desenhados olhando para a direita; `olhar: "esquerda"` espelha.
Sem `animations`, todos os frames viram a animação `parado`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..sprite import Art
from .script import SceneError

DEFAULT_ANIM = "parado"


@dataclass
class Animation:
    frames: list[int]
    fps: int


@dataclass
class SpriteSheet:
    name: str
    frames: list[np.ndarray]                 # RGBA uint8
    anchor: tuple[int, int]
    animations: dict[str, Animation]

    @property
    def size(self) -> tuple[int, int]:
        return self.frames[0].shape[1], self.frames[0].shape[0]

    def default_anim(self) -> str:
        return DEFAULT_ANIM if DEFAULT_ANIM in self.animations else next(iter(self.animations))

    def check(self, anim: str, where: str) -> str:
        if anim not in self.animations:
            raise SceneError(f"{where}: animação '{anim}' não existe em '{self.name}' "
                             f"(tem: {', '.join(self.animations)})")
        return anim

    def frame(self, anim: str, elapsed: float) -> np.ndarray:
        animation = self.animations[anim]
        step = int(max(elapsed, 0) * animation.fps + 1e-9)
        return self.frames[animation.frames[step % len(animation.frames)]]


def sheet_from_art(art: Art) -> SpriteSheet:
    where = f"sprite '{art.name}'"
    w, h = art.size
    anchor = art.meta.get("anchor", [w // 2, h - 1])
    if (not isinstance(anchor, (list, tuple)) or len(anchor) != 2
            or not all(isinstance(v, int) and not isinstance(v, bool) for v in anchor)):
        raise SceneError(f"{where}: anchor deve ser [x, y] inteiros, não {anchor!r}")
    raw = art.meta.get("animations")
    if raw is None:
        animations = {DEFAULT_ANIM: Animation(list(range(len(art.frames))), art.fps)}
    else:
        if not isinstance(raw, dict) or not raw:
            raise SceneError(f"{where}: animations deve ser objeto {{nome: {{frames, fps}}}}")
        animations = {}
        for name, spec in raw.items():
            if isinstance(spec, list):
                spec = {"frames": spec}
            frames = spec.get("frames") if isinstance(spec, dict) else None
            if (not isinstance(frames, list) or not frames
                    or not all(isinstance(i, int) and 0 <= i < len(art.frames) for i in frames)):
                raise SceneError(f"{where}: animations.{name}.frames deve listar índices de 0 a "
                                 f"{len(art.frames) - 1}")
            fps = spec.get("fps", art.fps)
            if isinstance(fps, bool) or not isinstance(fps, int) or not 1 <= fps <= 60:
                raise SceneError(f"{where}: animations.{name}.fps deve ser inteiro entre 1 e 60")
            animations[name] = Animation(frames, fps)
    return SpriteSheet(art.name, [f.pixels for f in art.frames], (anchor[0], anchor[1]), animations)


@dataclass
class ActorView:
    """Um ator como aparece num quadro."""

    name: str
    sheet: SpriteSheet
    x: int
    y: int
    facing: str
    anim: str
    elapsed: float                            # s desde que a animação começou
    alpha: float = 1.0

    def image(self, override: np.ndarray | None = None) -> tuple[np.ndarray, int, int]:
        """(pixels RGBA já espelhados, x e y do canto superior esquerdo no cenário).
        `override`: quadro no lugar da animação (ex.: gerado por IA, mesmo tamanho do sprite)."""
        pixels = self.sheet.frame(self.anim, self.elapsed) if override is None else override
        ax, ay = self.sheet.anchor
        if self.facing == "esquerda":
            pixels = pixels[:, ::-1]
            ax = pixels.shape[1] - 1 - ax
        return pixels, self.x - ax, self.y - ay
