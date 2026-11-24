"""Folha da amostra v2: bustos em cima; no meio, os corpos inteiros numa calçada
molhada de fim de tarde (sombra de contato e reflexo), alinhados pelo chão; embaixo,
o cenário de teste do kit (rua de Goiânia, 320×180).

Render: python -m pixelforge render art/coletanea/veu/amostra-chibi/amostra-v2/folha.py --scales 1,3
"""

import importlib.util
from pathlib import Path

import numpy as np

from pixelforge.palettes import parse_color
from pixelforge.sprite import Sprite

NAME = "personagens_finais"
HERE = Path(__file__).parent
GAP = 8

SKY = ["#2a2438", "#352b42", "#46344a", "#5e404c", "#80524e", "#a8664e"]   # de cima para o horizonte
GLOW = parse_color("#e08a4a")
GROUND = ["#3a3344", "#2e2938", "#25212e"]                                   # calçada molhada
PUDDLE = parse_color("#5a4a5a")


def _frames(name: str) -> list[Sprite]:
    spec = importlib.util.spec_from_file_location(f"final_{name}", HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = mod.build()
    return out if isinstance(out, list) else [out]


def _blend(a, b, t):
    return np.clip(np.round(np.asarray(a[:3], float) * (1 - t) + np.asarray(b[:3], float) * t), 0, 255)


def backdrop(w: int, h: int, horizon: int) -> np.ndarray:
    """Céu em faixas (sem degradê liso) com brilho laranja à esquerda; chão molhado."""
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., 3] = 255
    band = max(1, horizon // len(SKY))
    for y in range(horizon):
        i = min(y // band, len(SKY) - 1)
        out[y, :, :3] = parse_color(SKY[i])[:3]
    ys, xs = np.mgrid[0:h, 0:w]
    glow = ((xs / w) ** 2 * 0.9 + ((horizon - ys) / horizon) ** 2 * 6.0)                # sol baixo à esquerda
    for level, t in ((0.45, 0.18), (0.16, 0.38), (0.04, 0.6)):
        m = (glow < level) & (ys < horizon)
        out[m, :3] = _blend(out[m].T, np.array(GLOW[:3])[:, None], t).T if m.any() else out[m, :3]
    for y in range(horizon, h):
        i = min((y - horizon) // 3, len(GROUND) - 1)
        out[y, :, :3] = parse_color(GROUND[i])[:3]
    rng = np.random.default_rng(1)
    for _ in range(w // 6):                                                               # poças refletindo o céu
        x, y = int(rng.integers(0, w - 8)), int(rng.integers(horizon + 2, h - 1))
        out[y, x:x + int(rng.integers(3, 9)), :3] = PUDDLE[:3]
    out[horizon, :, :3] = _blend(parse_color(GROUND[0]), GLOW, 0.35)                     # brilho na borda da calçada
    return out


def paste(canvas: np.ndarray, img: Sprite, x: int, y: int) -> None:
    m = img.pixels[..., 3] > 0
    canvas[y:y + img.height, x:x + img.width][m] = img.pixels[m]


def reflect(canvas: np.ndarray, img: Sprite, x: int, floor: int, depth: int) -> None:
    """Reflexo no chão molhado: invertido, escurecido, quebrado por ondulações."""
    flip = img.pixels[::-1]
    for k in range(min(depth, img.height)):
        row = flip[k]
        y = floor + 1 + k
        if y >= canvas.shape[0] or k % 3 == 2:
            continue
        shift = (1 if (k // 3) % 2 else -1) if k > 4 else 0
        m = row[:, 3] > 0
        xs = np.nonzero(m)[0] + x + shift
        ok = (xs >= 0) & (xs < canvas.shape[1])
        t = 0.3 + 0.5 * k / depth
        canvas[y, xs[ok], :3] = _blend(row[m][ok].T, canvas[y, xs[ok], :3].T, t).T


def build():
    busts = _frames("martim_retrato_repinta") + _frames("geraldo_retrato_repinta")
    bodies = _frames("martim_repinta") + _frames("geraldo_repinta")
    street = _frames("rua_goiania")[0]
    W = max(sum(b.width for b in busts), sum(b.width for b in bodies), street.width) + GAP * 4
    tallest = max(b.height for b in bodies)
    top = GAP + busts[0].height + GAP
    floor = top + tallest - 2
    H = floor + 26
    canvas = backdrop(W, H, floor - 18)
    canvas[:top] = parse_color("#1c1924")
    x = GAP * 2
    for b in busts:
        paste(canvas, b, x, GAP)
        x += b.width + GAP * 2
    x = GAP
    for b in bodies:
        ys, xs = np.nonzero(b.pixels[..., 3] > 0)
        feet = ys.max()
        ox, oy = x, floor - feet
        cx = ox + int(np.mean(xs[ys >= feet - 2]))
        sh = np.mgrid[0:H, 0:W]
        shadow = (((sh[1] - cx) / 18) ** 2 + ((sh[0] - floor - 1) / 2.2) ** 2) <= 1          # sombra de contato
        canvas[shadow, :3] = (canvas[shadow, :3] * 0.6).astype(np.uint8)
        reflect(canvas, b, ox, floor, 22)
        paste(canvas, b, ox, oy)
        x += b.width + GAP
    # cenário de teste do kit (320×180), embaixo, na escala dele
    full = np.zeros((H + street.height + GAP * 2, W, 4), dtype=np.uint8)
    full[:H] = canvas
    full[H:] = parse_color("#1c1924")
    paste(full, street, (W - street.width) // 2, H + GAP)
    return Sprite(full)
