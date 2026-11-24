"""Geradores de animação a partir de uma pose parada (qualquer sprite).

Grava na spec as chaves `animations` e `anchor` (formato do motor de cena,
docs/specs/2026-10-21-pixelforge-cena-design.md):

    "anchor": [16, 31],
    "animations": {"parado": {"frames": [0, 1], "fps": 3}, ...}

Geradores (todos devolvem lista de Sprite):
  breathe   respirar: parte de cima desce 1 px (achata o tronco)
  blink     piscar: pixels dos olhos viram a cor da pálpebra (pixel de cima)
  talk      falar: retângulo da boca alterna fechado/aberto (escuro)
  walk      andar 4 ou 6 quadros: pernas abaixo do quadril balançam (cisalhamento)

Sprites são desenhados olhando para a direita; a esquerda é espelho automático
(o motor de cena espelha; `mirror` está aqui para quem precisar do quadro).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .export import save_gif
from .palettes import RGBA, parse_color
from .recolor import shade
from .sprite import Art, Sprite

WALK_OFFSETS = {
    4: [2, 0, -2, 0],
    6: [2, 1, -1, -2, -1, 1],
}
# quadros de "passagem" (pernas juntas) sobem o corpo 1 px — aqui, em vez de subir,
# os quadros de contato abaixam (não precisa de margem em cima)
WALK_DOWN = {4: [True, False, True, False], 6: [True, False, False, True, False, False]}


def default_anchor(sprite: Sprite) -> list[int]:
    """Base central da silhueta: [x do centro, y da linha mais baixa opaca]."""
    opaque = sprite.pixels[..., 3] > 0
    if not opaque.any():
        return [sprite.width // 2, sprite.height - 1]
    ys, xs = np.nonzero(opaque)
    bottom = ys.max()
    row = xs[ys >= bottom - 1]
    return [int(round((row.min() + row.max()) / 2)), int(bottom)]


def mirror(sprite: Sprite) -> Sprite:
    return Sprite(sprite.pixels[:, ::-1].copy())


def shift_rows(sprite: Sprite, top: int, bottom: int, dy: int) -> Sprite:
    """Desloca verticalmente as linhas [top, bottom) por dy (transparente onde abre)."""
    out = sprite.copy()
    band = sprite.pixels[top:bottom].copy()
    out.pixels[top:bottom] = 0
    for i, row in enumerate(band):
        y = top + i + dy
        if 0 <= y < sprite.height:
            mask = row[:, 3] > 0
            out.pixels[y][mask] = row[mask]
    return out


def breathe(sprite: Sprite, chest: int) -> list[Sprite]:
    """Quadro 0 = original; quadro 1 = tudo acima de `chest` desce 1 px."""
    down = sprite.copy()
    down.pixels[1:chest + 1] = sprite.pixels[0:chest]
    down.pixels[0] = 0
    # a linha `chest` original fica por baixo de onde não foi coberta
    below = sprite.pixels[chest]
    hole = down.pixels[chest, :, 3] == 0
    down.pixels[chest][hole] = below[hole]
    return [sprite.copy(), down]


def blink(sprite: Sprite, eyes: list[tuple[int, int]], lid: RGBA | None = None) -> Sprite:
    """Fecha os olhos: cada pixel vira `lid` ou a cor do pixel logo acima."""
    out = sprite.copy()
    for x, y in eyes:
        color = lid or tuple(int(v) for v in sprite.pixels[max(y - 1, 0), x])
        out.pixels[y, x] = color
    return out


def talk(sprite: Sprite, mouth: tuple[int, int, int, int], color: RGBA | None = None) -> list[Sprite]:
    """Quadros [boca fechada, boca aberta]; `mouth` = x, y, largura, altura."""
    x, y, w, h = mouth
    opened = sprite.copy()
    region = [tuple(int(v) for v in px) for px in sprite.pixels[y:y + h, x:x + w].reshape(-1, 4) if px[3] > 0]
    # padrão: bem mais escuro que a cor dominante da região (pele → boca)
    fill = color or (shade(max(set(region), key=region.count), -3) if region else (0, 0, 0, 255))
    opened.pixels[y:y + h, x:x + w] = fill
    return [sprite.copy(), opened]


def walk(sprite: Sprite, hip: int, frames: int = 4, split: int | None = None) -> list[Sprite]:
    """Ciclo de andar (vista lateral) a partir da pose parada.

    Abaixo de `hip`, a metade de trás (x < split) e a da frente (x >= split)
    balançam em sentidos opostos, com deslocamento crescente até o pé.
    """
    if frames not in WALK_OFFSETS:
        raise ValueError("andar tem 4 ou 6 quadros")
    h, w = sprite.height, sprite.width
    split = default_anchor(sprite)[0] if split is None else split
    legs = sprite.pixels[hip:].copy()
    span = max(h - 1 - hip, 1)
    out = []
    for offset, down in zip(WALK_OFFSETS[frames], WALK_DOWN[frames]):
        frame = sprite.copy()
        frame.pixels[hip:] = 0
        for half, sign in (("back", -1), ("front", 1)):
            for i, row in enumerate(legs):
                dx = int(round(sign * offset * (i + 1) / (span + 1)))
                for x in range(w):
                    if row[x, 3] == 0 or (x < split) != (half == "back"):
                        continue
                    nx = x + dx
                    if 0 <= nx < w and (half == "front" or frame.pixels[hip + i, nx, 3] == 0):
                        frame.pixels[hip + i, nx] = row[x]
        _close_gaps(frame, hip, sprite)
        if down:
            frame = shift_rows(frame, 0, hip, 1)
        out.append(frame)
    return out


def _close_gaps(frame: Sprite, hip: int, original: Sprite, max_gap: int = 2) -> None:
    """Fecha frestas de até `max_gap` px que o cisalhamento abre entre as metades das pernas
    (só onde a pose parada era opaca: o vão real entre as pernas continua vazio)."""
    px = frame.pixels
    for y in range(hip, frame.height):
        row = px[y]
        opaque = np.nonzero(row[:, 3] > 0)[0]
        for a, b in zip(opaque, opaque[1:]):
            gap = b - a - 1
            if 0 < gap <= max_gap and original.pixels[y, a + 1:b, 3].all():
                row[a + 1:b] = row[a]


# --------------------------------------------------------------------------
# Montagem: quadros únicos + animations
# --------------------------------------------------------------------------


class Builder:
    """Junta animações, reaproveitando quadros idênticos."""

    def __init__(self) -> None:
        self.frames: list[Sprite] = []
        self.animations: dict[str, dict] = {}
        self._index: dict[bytes, int] = {}

    def add_frame(self, sprite: Sprite) -> int:
        key = sprite.pixels.tobytes()
        if key not in self._index:
            self._index[key] = len(self.frames)
            self.frames.append(sprite)
        return self._index[key]

    def add(self, name: str, sprites: list[Sprite], fps: int) -> None:
        self.animations[name] = {"frames": [self.add_frame(s) for s in sprites], "fps": int(fps)}

    def art(self, name: str, anchor: list[int] | None = None, meta: dict | None = None, fps: int = 8) -> Art:
        meta = dict(meta or {})
        meta["anchor"] = anchor or default_anchor(self.frames[0])
        meta["animations"] = self.animations
        return Art(name, self.frames, fps, meta)


def validate_animations(art: Art) -> None:
    anchor = art.meta.get("anchor")
    if anchor is not None and (len(anchor) != 2 or not all(isinstance(v, int) for v in anchor)):
        raise ValueError("'anchor' deve ser [x, y] inteiros")
    anims = art.meta.get("animations")
    if anims is None:
        return
    if not isinstance(anims, dict):
        raise ValueError("'animations' deve ser um objeto nome → {frames, fps}")
    for name, anim in anims.items():
        frames = anim.get("frames") if isinstance(anim, dict) else None
        if not frames or not all(isinstance(i, int) and 0 <= i < len(art.frames) for i in frames):
            raise ValueError(f"animação '{name}': 'frames' deve listar índices de 0 a {len(art.frames) - 1}")
        if int(anim.get("fps", art.fps)) <= 0:
            raise ValueError(f"animação '{name}': fps deve ser > 0")


def animations_of(art: Art) -> dict[str, dict]:
    """Animações da arte; sem `animations`, o sprite inteiro vira `parado`."""
    return art.meta.get("animations") or {"parado": {"frames": list(range(len(art.frames))), "fps": art.fps}}


def animation_art(art: Art, name: str) -> Art:
    anim = animations_of(art)[name]
    return Art(f"{art.name}_{name}", [art.frames[i] for i in anim["frames"]], int(anim.get("fps", art.fps)))


def export_animations(art: Art, out_dir: str | Path, scale: int = 4) -> list[Path]:
    """Um GIF por animação: <nome>_<animacao>.gif."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in animations_of(art):
        sub = animation_art(art, name)
        path = out_dir / f"{sub.name}.gif"
        save_gif(sub, path, scale)
        paths.append(path)
    return paths


def parse_points(value: str) -> list[tuple[int, int]]:
    """'12,10 15,10' → [(12, 10), (15, 10)]."""
    points = []
    for part in value.split():
        x, y = (int(v) for v in part.split(","))
        points.append((x, y))
    return points


def generate(sprite: Sprite, idle: bool = True, chest: int | None = None, eyes=None, mouth=None,
             mouth_color: str | None = None, hip: int | None = None, walk_frames: int = 0,
             split: int | None = None) -> Builder:
    """Animações padrão a partir de um sprite parado."""
    b = Builder()
    anchor_y = default_anchor(sprite)[1]
    opaque_rows = np.nonzero((sprite.pixels[..., 3] > 0).any(axis=1))[0]
    top = int(opaque_rows.min()) if len(opaque_rows) else 0
    hip = hip if hip is not None else top + int((anchor_y - top) * 0.68)
    chest = chest if chest is not None else hip - 1
    still = sprite.copy()
    idle_frames = breathe(still, chest) if idle else [still]
    closed = blink(still, eyes) if eyes else None
    up, down = idle_frames[0], idle_frames[-1]
    # 2 s a 4 fps: respira duas vezes e pisca no fim (se houver olhos)
    b.add("parado", [up, up, down, down, up, up, down, closed if closed is not None else down], 4)
    b.add("respirar", idle_frames, 2)
    if closed is not None:
        b.add("piscar", [still, closed, still], 8)
    if mouth:
        b.add("falar", talk(still, mouth, parse_color(mouth_color) if mouth_color else None), 6)
    if walk_frames:
        b.add("andar", walk(still, hip, walk_frames, split), 8)
    return b
