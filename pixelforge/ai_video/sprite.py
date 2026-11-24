"""Animação de sprite por IA: ciclos `parado`, `andar`, `falar` (ou qualquer outro) a partir
de um sprite pronto, pixelizados com a paleta do próprio sprite.

O sprite (pose de partida) vai ampliado sobre um fundo liso de uma cor longe da paleta;
a IA anima; a pixelização temporal volta para o tamanho do sprite com a paleta dele e
recorta o fundo (alfa). O resultado é gravado numa spec nova com os quadros antigos +
os novos, `animations` e o mesmo `anchor` — pronta para `atores` de uma cena.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..color import srgb_to_oklab
from ..sprite import Art, Sprite, save_spec
from .clips import make_clip
from .pixelize import palette_of

# Descrições padrão (inglês rende melhor no Wan). {who} vira a descrição do personagem.
PROMPTS = {
    "parado": "{who}, idle animation, standing still, breathing gently, subtle sway, static camera, "
              "flat solid background, pixel art game sprite",
    "andar": "{who}, walking in place facing right, looping walk cycle, legs and arms swinging, "
             "static camera, flat solid background, pixel art game sprite",
    "falar": "{who}, talking, mouth opening and closing, small head and hand gestures, static camera, "
             "flat solid background, pixel art game sprite",
}
DEFAULT_WHO = "a pixel art character"
KEY_CANDIDATES = [(0, 177, 64), (255, 0, 255), (0, 120, 255), (255, 255, 255), (32, 32, 32)]


def key_color(palette: np.ndarray) -> tuple[int, int, int]:
    """Cor de fundo mais distante (Oklab) de todas as cores do sprite."""
    pal = srgb_to_oklab(np.asarray(palette, np.float64))
    best, far = KEY_CANDIDATES[0], -1.0
    for c in KEY_CANDIDATES:
        d = float(np.sqrt(((pal - srgb_to_oklab(np.array([c], np.float64))) ** 2).sum(axis=1)).min())
        if d > far:
            best, far = c, d
    return best


@dataclass
class SpriteAnimation:
    name: str
    frames: list[np.ndarray]     # RGBA no tamanho do sprite
    fps: int
    seed: int
    score: float | None


def animate_sprite(art: Art, anims: dict[str, str | None], *, seconds: float = 2.0, fps: int = 8,
                   frames: int | None = None, who: str = DEFAULT_WHO, seed: int = 0, cache_dir: Path,
                   config=None, start_frame: int = 0, generator=None, log=print) -> list[SpriteAnimation]:
    """Gera as animações pedidas (`{nome: descrição ou None = padrão}`)."""
    source = art.frames[start_frame].pixels
    palette = palette_of(source)
    key = key_color(palette)
    out = []
    for name, prompt in anims.items():
        text = (prompt or PROMPTS.get(name) or f"{{who}}, {name}, static camera, flat solid background").format(who=who)
        log(f"{art.name}: {name} — {text}")
        clip = make_clip(source, text, seconds, fps=fps, seed=seed, cache_dir=cache_dir, config=config,
                         tipo="personagem", key=key, palette=palette, generator=generator, log=log)
        picked = clip.frames
        if frames:
            idx = np.linspace(0, len(picked) - 1, frames).round().astype(int)
            picked = [picked[i] for i in idx]
        out.append(SpriteAnimation(name, picked, fps, clip.seed, clip.score))
    return out


def save_animated(art: Art, animations: list[SpriteAnimation], path: Path) -> Path:
    """Spec com os quadros do sprite + os gerados; `animations` e `anchor` preservados/acrescentados."""
    frames = [Sprite(f.pixels.copy()) for f in art.frames]
    w, h = art.size
    meta = dict(art.meta)
    meta.setdefault("anchor", [w // 2, h - 1])
    table = dict(meta.get("animations") or {"parado": {"frames": list(range(len(frames))), "fps": art.fps}})
    for anim in animations:
        start = len(frames)
        frames += [Sprite(np.ascontiguousarray(f)) for f in anim.frames]
        table[anim.name] = {"frames": list(range(start, len(frames))), "fps": anim.fps}
    meta["animations"] = table
    meta["ia"] = {a.name: {"semente": a.seed, "nota": a.score} for a in animations}
    return save_spec(Art(path.stem, frames, art.fps, meta), path)
