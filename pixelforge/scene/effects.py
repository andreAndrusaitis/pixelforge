"""Efeitos de cena, desenhados na resolução da tela, em pixel.

Todos são funções puras do instante: a posição de cada gota/partícula vem de
um hash (semente fixa por efeito), não de estado acumulado — `quadro --t 7.5`
dá exatamente o mesmo pixel que o vídeo. Transições graduais (neblina, luz,
vinheta, flash) usam degraus e dithering ordenado, não gradiente liso.
"""

from __future__ import annotations

import math
import zlib
from dataclasses import dataclass

import numpy as np

from .script import Effect

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16

TINTS = {
    "noite": (0.42, 0.48, 0.85),
    "dia": (1.06, 1.02, 0.94),
    "por-do-sol": (1.05, 0.78, 0.62),
}
SEPIA = (1.0, 0.82, 0.6)
PARTICLE_COLORS = {
    "poeira": [(234, 212, 170), (228, 166, 114)],
    "folhas": [(62, 137, 72), (184, 111, 80), (254, 174, 52)],
    "brasas": [(247, 118, 34), (254, 174, 52), (254, 231, 97)],
    "neve": [(255, 255, 255), (192, 203, 220)],
    "vagalumes": [(254, 231, 97), (99, 199, 77)],
}


@dataclass
class EffectContext:
    t: float                    # s desde o início do efeito (plano ou cena)
    camera: tuple[int, int]     # canto da vista no cenário
    zoom: int


def active(effect: Effect, elapsed: float) -> bool:
    if elapsed < effect.start:
        return False
    return effect.dur is None or elapsed < effect.start + effect.dur


def apply(canvas: np.ndarray, effect: Effect, ctx: EffectContext) -> np.ndarray:
    seed = zlib.crc32(effect.where.encode("utf-8"))
    fn = {"tinta": _tint, "luz": _light, "neblina": _fog, "chuva": _rain, "particulas": _particles,
          "flash": _flash, "vinheta": _vignette}[effect.kind]
    return fn(canvas, effect, ctx, seed)


# --------------------------------------------------------------------------


def _rand(seed: int, ids: np.ndarray, k: int) -> np.ndarray:
    """Números em [0, 1) determinísticos por (semente, id, k)."""
    x = (ids.astype(np.uint64) * np.uint64(0x9E3779B97F4A7C15)
         + np.uint64((seed * 31 + k * 0x632BE5AB) & 0xFFFFFFFF))
    x ^= x >> np.uint64(30)
    x *= np.uint64(0xBF58476D1CE4E5B9)
    x ^= x >> np.uint64(27)
    x *= np.uint64(0x94D049BB133111EB)
    x ^= x >> np.uint64(31)
    return (x >> np.uint64(11)).astype(np.float64) / float(1 << 53)


def _bayer(h: int, w: int) -> np.ndarray:
    return np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]


def _mix(canvas: np.ndarray, color, amount: np.ndarray | float) -> np.ndarray:
    amount = np.asarray(amount, np.float32)
    if amount.ndim == 2:
        amount = amount[..., None]
    out = canvas.astype(np.float32) * (1 - amount) + np.array(color, np.float32) * amount
    return np.floor(out + 0.5).clip(0, 255).astype(np.uint8)


def _steps(values: np.ndarray, steps: int = 4) -> np.ndarray:
    return np.floor(values * steps + 0.5) / steps


def _put(canvas: np.ndarray, xs: np.ndarray, ys: np.ndarray, color) -> None:
    h, w = canvas.shape[:2]
    xs, ys = np.asarray(xs).astype(int), np.asarray(ys).astype(int)
    ok = (xs >= 0) & (xs < w) & (ys >= 0) & (ys < h)
    canvas[ys[ok], xs[ok]] = color


# --------------------------------------------------------------------------


def _tint(canvas, effect, ctx, seed):
    p = effect.params
    k = p["intensidade"]
    if p["cor"] is not None:
        factors = np.array(p["cor"], np.float32) / 255
        tinted = canvas.astype(np.float32) * factors
    elif p["modo"] == "sepia":
        lum = canvas.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)
        tinted = lum[..., None] * np.array(SEPIA, np.float32)
    else:
        tinted = canvas.astype(np.float32) * np.array(TINTS[p["modo"]], np.float32)
    out = canvas.astype(np.float32) * (1 - k) + tinted * k
    return np.floor(out + 0.5).clip(0, 255).astype(np.uint8)


def _light(canvas, effect, ctx, seed):
    """Luz de tocha/janela: 3 anéis em degraus, borda com dithering, raio piscando."""
    p = effect.params
    h, w = canvas.shape[:2]
    z = ctx.zoom
    cx, cy = (p["pos"][0] - ctx.camera[0]) * z, (p["pos"][1] - ctx.camera[1]) * z
    t = ctx.t
    wobble = 0.5 * math.sin(t * 7.3 + seed % 7) + 0.3 * math.sin(t * 13.1) + 0.2 * math.sin(t * 2.9)
    radius = p["raio"] * z * (1 + 0.12 * p["piscar"] * wobble)
    strength = p["intensidade"] * (1 + 0.25 * p["piscar"] * wobble)
    r = int(radius) + 2
    x0, x1, y0, y1 = max(int(cx) - r, 0), min(int(cx) + r + 1, w), max(int(cy) - r, 0), min(int(cy) + r + 1, h)
    if x0 >= x1 or y0 >= y1:
        return canvas
    ys, xs = np.mgrid[y0:y1, x0:x1]
    d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / radius
    rings = np.floor((1 - d) * 3 + _bayer(h, w)[y0:y1, x0:x1] * 0.9).clip(0, 3) / 3
    out = canvas.copy()
    region = out[y0:y1, x0:x1].astype(np.float32)
    region += np.array(p["cor"], np.float32) * (rings * strength)[..., None]
    out[y0:y1, x0:x1] = np.floor(region + 0.5).clip(0, 255).astype(np.uint8)
    return out


def _fog(canvas, effect, ctx, seed):
    p = effect.params
    h, w = canvas.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    shift = ctx.t * p["velocidade"] + ctx.camera[0] * ctx.zoom * 0.5
    wave = (np.sin((xs + shift) / (23 * ctx.zoom) + np.sin(ys / (11 * ctx.zoom)) * 1.5 + seed % 5)
            + 0.6 * np.sin((xs - shift * 0.6) / (9 * ctx.zoom) + ys / (17 * ctx.zoom)))
    density = p["intensidade"] * (0.35 + 0.65 * ys / h) * (0.75 + 0.25 * wave / 1.6)
    amount = _steps(np.clip(density + (_bayer(h, w) - 0.5) * 0.25, 0, 1)) * 0.8
    return _mix(canvas, p["cor"], amount)


def _rain(canvas, effect, ctx, seed):
    p = effect.params
    h, w = canvas.shape[:2]
    s = max(1, h // 180)
    n = max(1, int(p["intensidade"] * w * h / (350 * s * s)))
    ids = np.arange(n)
    length = (4 + (_rand(seed, ids, 3) * 3).astype(int)) * s
    speed = (190 + 70 * _rand(seed, ids, 2)) * s
    span = h + 8 * s
    y = (_rand(seed, ids, 1) * span + speed * ctx.t) % span - 6 * s
    slant = p["vento"] * 0.25
    x = (_rand(seed, ids, 0) * (w + 40 * s) + slant * y) % (w + 40 * s) - 20 * s
    out = canvas.copy()
    color = p["cor"]
    for step in range(int(length.max())):
        on = step < length
        _put(out, (x + slant * step)[on], (y + step)[on], color)
    return out


def _particles(canvas, effect, ctx, seed):
    p = effect.params
    style = p["estilo"]
    h, w = canvas.shape[:2]
    s = max(1, h // 180)
    n = p["quantidade"]
    ids = np.arange(n)
    r0, r1, r2, r3 = (_rand(seed, ids, k) for k in range(4))
    t = ctx.t
    colors = [p["cor"]] if p["cor"] is not None else PARTICLE_COLORS[style]
    size = np.ones(n, int) * s
    visible = np.ones(n, bool)
    if style == "brasas":       # sobem tremendo, somem no alto
        y = h - ((r1 * h + (14 + 16 * r2) * s * t) % (h * 0.8))
        x = r0 * w + 3 * s * np.sin(t * (2 + 2 * r3) + r2 * 6)
        visible = np.sin(t * (6 + 5 * r3) + r1 * 9) > -0.6
    elif style == "vagalumes":  # vagam devagar na metade de baixo, piscando
        x = (r0 * w + 18 * s * np.sin(t * (0.4 + 0.5 * r2) + r3 * 6)) % w
        y = h * (0.45 + 0.45 * r1) + 8 * s * np.sin(t * (0.5 + 0.4 * r3) + r0 * 6)
        visible = np.sin(t * (1.6 + 1.4 * r2) + r3 * 12) > 0.1
    else:                       # caem: poeira, folhas, neve
        fall = {"poeira": 5, "folhas": 22, "neve": 14}[style]
        sway = {"poeira": 6, "folhas": 10, "neve": 5}[style]
        span = h + 4 * s
        y = (r1 * span + (fall * (0.6 + 0.8 * r2)) * s * t) % span - 2 * s
        drift = {"poeira": 4, "folhas": 10, "neve": 3}[style] * s * t
        x = (r0 * w + drift + sway * s * np.sin(t * (0.8 + r3) + r2 * 6)) % w
        if style in ("folhas", "neve"):
            size = np.where(r3 > 0.6, 2 * s, s)
    out = canvas.copy()
    for i in range(n):
        if not visible[i]:
            continue
        color = colors[int(r2[i] * len(colors)) % len(colors)]
        xi, yi, sz = int(x[i]), int(y[i]), int(size[i])
        if style == "folhas" and sz > s:   # folha de 2 px que "gira": horizontal/vertical
            flip = math.sin(t * 3 + r0[i] * 9) > 0
            out[max(yi, 0):max(yi + (s if flip else 2 * s), 0), max(xi, 0):max(xi + (2 * s if flip else s), 0)] = color
        else:
            out[max(yi, 0):max(yi + sz, 0), max(xi, 0):max(xi + sz, 0)] = color
    return out


def _flash(canvas, effect, ctx, seed):
    dur = effect.dur or 0.3
    u = (ctx.t - effect.start) / dur
    amount = float(_steps(np.array(max(0.0, 1 - u)), 4))
    return _mix(canvas, effect.params["cor"], amount) if amount > 0 else canvas


def _vignette(canvas, effect, ctx, seed):
    p = effect.params
    h, w = canvas.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt(((xs - w / 2) / (w / 2)) ** 2 + ((ys - h / 2) / (h / 2)) ** 2)
    raw = np.clip((d - 0.65) / 0.6, 0, 1) * p["intensidade"]
    amount = _steps(np.clip(raw + (_bayer(h, w) - 0.5) * 0.25, 0, 1))
    return _mix(canvas, p["cor"], amount)
