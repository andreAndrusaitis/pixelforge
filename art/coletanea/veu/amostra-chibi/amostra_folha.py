"""Folha da amostra chibi: retratos em cima, sprites embaixo alinhados pelo chão
(para comparar alturas: Martim ~54 px, Geraldo ~79 px com chapéu).

Render: python -m pixelforge render art/coletanea/veu/amostra-chibi/amostra_folha.py --scales 1,4
"""

import importlib.util
from pathlib import Path

import numpy as np

from pixelforge.sprite import Sprite

NAME = "amostra_chibi"
HERE = Path(__file__).parent
GAP = 6
FLOOR = (238, 232, 220, 255)


def _frames(name: str):
    spec = importlib.util.spec_from_file_location(f"amostra_{name}", HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = mod.build()
    return out if isinstance(out, list) else [out]


def build():
    portraits = _frames("martim_retrato") + _frames("geraldo_retrato")
    sprites = _frames("martim_sprite") + _frames("geraldo_sprite")
    pw = sum(s.width for s in portraits) + GAP * (len(portraits) + 1)
    sw = sum(s.width for s in sprites) + GAP * (len(sprites) + 1)
    sh = max(s.height for s in sprites)
    W = max(pw, sw)
    H = GAP + portraits[0].height + GAP * 2 + sh + 3
    canvas = np.zeros((H, W, 4), dtype=np.uint8)

    def paste(img: Sprite, x: int, y: int) -> None:
        m = img.pixels[..., 3] > 0
        canvas[y:y + img.height, x:x + img.width][m] = img.pixels[m]

    x = GAP
    for s in portraits:
        paste(s, x, GAP)
        x += s.width + GAP
    floor = H - 3
    canvas[floor:floor + 2, :] = FLOOR
    x = GAP
    for s in sprites:
        paste(s, x, floor - s.height)
        x += s.width + GAP
    return Sprite(canvas)
