"""Gera as specs finais do Martim e do Seu Geraldo para as cenas (640×360).

Fonte: as bases da via de IA repintadas por código (martim_repinta.py,
martim_retrato_repinta.py, geraldo_repinta.py, geraldo_retrato_repinta.py).

Rodar da raiz do repositório:
    python art/coletanea/veu/final/sprites.py

Grava em art/coletanea/veu/:
    martim_final.json             parado, respirar, piscar, falar, andar           (~101 px)
    martim_final_retrato.json     parado, piscar, falar                            (busto 96×128)
    geraldo_final.json            parado, respirar, piscar, falar, andar, tirar_chapeu (~137 px)
    geraldo_final_sem_chapeu.json parado, respirar, piscar, falar, andar           (chapéu na mão)
    geraldo_final_retrato.json    parado, piscar, falar                            (busto 96×128)
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from pixelforge import animate  # noqa: E402
from pixelforge.recolor import merge_close  # noqa: E402
from pixelforge.sprite import SPEC_KEYS, Sprite, save_spec  # noqa: E402

OUT = HERE.parent


def load(name: str):
    spec = importlib.util.spec_from_file_location(f"final_{name}", HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fit_palette(frames: list[Sprite], limit: int = len(SPEC_KEYS) - 1) -> list[Sprite]:
    """Funde tons quase iguais até caber nas chaves de uma spec (sem mudar o desenho)."""
    delta = 0.012
    while True:
        colors = Sprite(np.concatenate([f.pixels for f in frames], axis=1)).colors()
        if len(colors) <= limit:
            return frames
        frames = merge_close(frames, delta)
        delta += 0.006


def build(name: str, anims: dict[str, tuple[list[Sprite], int]], anchor: list[int], origem: str) -> Path:
    order = [(a, frames, fps) for a, (frames, fps) in anims.items()]
    flat = fit_palette([f for _, frames, _ in order for f in frames])
    b = animate.Builder()
    i = 0
    for a, frames, fps in order:
        b.add(a, flat[i:i + len(frames)], fps)
        i += len(frames)
    meta = {"personagem": name.split("_")[0], "estilo": "pintado", "origem": origem}
    art = b.art(name, anchor=anchor, meta=meta, fps=4)
    animate.validate_animations(art)
    path = save_spec(art, OUT / f"{name}.json")
    ys = np.nonzero(art.frames[0].pixels[..., 3].any(axis=1))[0]
    print(f"{path.name}: {len(art.frames)} quadros, {len(art.colors())} cores, altura {ys.max() - ys.min() + 1} px, "
          f"animações: {', '.join(art.meta['animations'])}")
    return path


def feet_anchor(s: Sprite) -> list[int]:
    """Âncora no chão, no meio dos dois pés (6 linhas de baixo), não só da última linha."""
    ys, xs = np.nonzero(s.pixels[..., 3] > 0)
    bottom = ys.max()
    feet = xs[ys >= bottom - 5]
    return [int(round((feet.min() + feet.max()) / 2)), int(bottom)]


def idle(base: Sprite, breath: Sprite, blink: Sprite) -> list[Sprite]:
    return [base, base, breath, breath, base, base, breath, blink]


def hip_row(s: Sprite, frac: float) -> int:
    ys = np.nonzero(s.pixels[..., 3].any(axis=1))[0]
    return int(ys.min() + (ys.max() - ys.min()) * frac)


def portrait(mod, name: str, origem: str) -> None:
    r, closed, talk = mod.render(), mod.render(eyes=False), mod.render(mouth=True)
    build(name, {"parado": ([r] * 7 + [closed], 4), "piscar": ([r, closed, r], 8), "falar": ([r, talk], 6)},
          [r.width // 2, r.height - 1], origem)


def martim() -> None:
    m = load("martim_repinta")
    base, blink, talk = m.render(), m.render(eyes=False), m.render(mouth=True)
    breath = animate.breathe(base, hip_row(base, 0.5))[1]
    walk = animate.walk(base, hip_row(base, 0.56), 4)
    build("martim_final", {"parado": (idle(base, breath, blink), 4), "respirar": ([base, breath], 2),
                           "piscar": ([base, blink, base], 8), "falar": ([base, talk], 6), "andar": (walk, 8)},
          feet_anchor(base), "martim_ia_final_corpo + martim_repinta.py")
    portrait(load("martim_retrato_repinta"), "martim_final_retrato",
             "martim_ia_final_retrato + martim_retrato_repinta.py")


def geraldo() -> None:
    g = load("geraldo_repinta")
    hat, lift, held = g.render("cabeca"), g.render("erguido"), g.render("mao")
    for name, state, base, extra in (("geraldo_final", "cabeca", hat, {"tirar_chapeu": ([hat, lift, held], 4)}),
                                     ("geraldo_final_sem_chapeu", "mao", held, {})):
        blink, talk = g.render(state, eyes=False), g.render(state, mouth=True)
        breath = animate.breathe(base, hip_row(base, 0.42))[1]
        walk = animate.walk(base, hip_row(base, 0.5), 4)
        anims = {"parado": (idle(base, breath, blink), 4), "respirar": ([base, breath], 2),
                 "piscar": ([base, blink, base], 8), "falar": ([base, talk], 6), "andar": (walk, 8), **extra}
        build(name, anims, feet_anchor(base), "geraldo_ia_final_corpo + geraldo_repinta.py")
    portrait(load("geraldo_retrato_repinta"), "geraldo_final_retrato",
             "geraldo_ia_final_retrato + geraldo_retrato_repinta.py")


if __name__ == "__main__":
    martim()
    geraldo()
