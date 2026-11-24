"""Troca de paleta (palette swap) e rampas de sombra automáticas.

- `shade(cor, nivel)`: tom mais claro (nivel > 0) ou mais escuro (< 0) com
  deslocamento de matiz (sombra puxa para frio/roxo, luz para quente/amarelo;
  12° por nível).
- `ramp(cor)`: rampa [luz, base, sombra, escuro] para um material.
- Mapas nomeados: tintas embutidas (`noite`, `por-do-sol`, `fantasma`, `sepia`,
  `dia`) e mapas do usuário em JSON (`{"mapas": {"casa_azul": {"#b13e53": "#3b5dc9"}}}`).
- `swap_family`: troca uma cor-base e também os tons da rampa dela, mantendo o
  mesmo desvio de luminosidade/matiz (a sombra do vermelho vira a sombra do azul).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .color import nearest, oklab_to_srgb, srgb_to_oklab
from .palettes import RGBA, parse_color
from .sprite import Art, Sprite

# Matizes-alvo em OKLCh (graus): sombras puxam para azul-violeta, luzes para amarelo.
COOL_HUE = 285.0
WARM_HUE = 85.0
STEP_L = 0.085


def to_lch(color: RGBA) -> tuple[float, float, float]:
    lab = srgb_to_oklab(np.array(color[:3]))
    L, a, b = (float(v) for v in lab)
    return L, float(np.hypot(a, b)), float(np.degrees(np.arctan2(b, a)) % 360)


def from_lch(L: float, C: float, h: float, alpha: int = 255) -> RGBA:
    rad = np.radians(h)
    rgb = oklab_to_srgb(np.array([L, C * np.cos(rad), C * np.sin(rad)]))
    return (int(rgb[0]), int(rgb[1]), int(rgb[2]), alpha)


def _toward(h: float, target: float, degrees: float) -> float:
    """Gira o matiz `degrees` graus em direção a `target` (sem passar dele)."""
    diff = (target - h + 180) % 360 - 180
    step = min(abs(diff), degrees)
    return (h + step * (1 if diff >= 0 else -1)) % 360


def shade(color: RGBA, level: float, hue_shift: float = 12.0) -> RGBA:
    """Clareia (level > 0) ou escurece (level < 0) com hue shifting em OKLCh."""
    if level == 0:
        return tuple(color)  # type: ignore[return-value]
    L, C, h = to_lch(color)
    if level < 0:
        L = max(0.06, L + STEP_L * level)
        h = _toward(h, COOL_HUE, hue_shift * -level) if C > 0.015 else h
        C = C * (1 + 0.08 * -level) if L > 0.25 else C * 0.85
    else:
        L = min(0.97, L + STEP_L * level)
        h = _toward(h, WARM_HUE, hue_shift * level) if C > 0.015 else h
        C = C * (1 - 0.12 * level)
    return from_lch(L, max(C, 0.0), h, color[3])


def ramp(color: RGBA | str, lights: int = 1, shadows: int = 2) -> list[RGBA]:
    """Rampa da mais clara para a mais escura: luz(es), base, sombra(s)."""
    base = parse_color(color) if isinstance(color, str) else tuple(color)
    return [shade(base, lv) for lv in range(lights, -shadows - 1, -1)]  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Tintas (transformações nomeadas)
# --------------------------------------------------------------------------


def _tint(rgb: np.ndarray, *, light: float = 1.0, sat: float = 1.0, toward=None,
          amount: float = 0.0, lift: float = 0.0) -> np.ndarray:
    lab = srgb_to_oklab(rgb)
    lab[..., 0] = np.clip(lab[..., 0] * light + lift, 0, 1)
    lab[..., 1:] *= sat
    if toward is not None:
        target = srgb_to_oklab(np.array(parse_color(toward)[:3]))
        # mistura o croma em direção à cor da luz; luminosidade preservada
        lab[..., 1:] = lab[..., 1:] * (1 - amount) + target[1:] * amount
    return oklab_to_srgb(lab)


TINTS = {
    "dia": dict(),
    "noite": dict(light=0.62, sat=0.55, toward="#3b4c9a", amount=0.45, lift=0.04),
    "por-do-sol": dict(light=0.92, sat=1.05, toward="#ff8a3c", amount=0.32),
    "fantasma": dict(light=0.85, sat=0.15, toward="#9fe6ff", amount=0.35, lift=0.18),
    "sepia": dict(light=1.0, sat=0.0, toward="#a0703c", amount=0.35),
}
GHOST_ALPHA = 170


def apply_tint(sprite: Sprite, name: str) -> Sprite:
    if name not in TINTS:
        raise KeyError(f"tinta '{name}' não existe. Disponíveis: {', '.join(TINTS)}")
    out = sprite.copy()
    opaque = out.pixels[..., 3] > 0
    if TINTS[name]:
        out.pixels[opaque, :3] = _tint(out.pixels[opaque, :3], **TINTS[name])
    if name == "fantasma":
        out.pixels[opaque, 3] = np.minimum(out.pixels[opaque, 3], GHOST_ALPHA)
    return out


# --------------------------------------------------------------------------
# Mapas de cor
# --------------------------------------------------------------------------


def swap_exact(sprite: Sprite, mapping: dict[RGBA, RGBA]) -> Sprite:
    out = sprite.copy()
    src = sprite.pixels
    for old, new in mapping.items():
        mask = np.all(src == np.array(old, dtype=np.uint8), axis=-1)
        out.pixels[mask] = new
    return out


def family(colors: list[RGBA], base: RGBA, max_hue: float = 40.0, max_chroma: float = 0.6) -> list[RGBA]:
    """Cores de `colors` que parecem tons da rampa de `base` (matiz e croma próximos)."""
    L0, C0, h0 = to_lch(base)
    members = []
    for c in colors:
        if c[3] == 0:
            continue
        L, C, h = to_lch(c)
        if C0 < 0.03:  # base neutra (cinza): família = outros neutros
            if C < 0.035:
                members.append(c)
            continue
        dh = abs((h - h0 + 180) % 360 - 180)
        if dh <= max_hue + 30 * abs(L - L0) / 0.3 and C > 0.02 and abs(C - C0) / C0 <= max_chroma + 0.6:
            members.append(c)
    return members


def swap_family(sprite: Sprite, old: RGBA, new: RGBA, others: list[RGBA] | None = None) -> dict[RGBA, RGBA]:
    """Mapa cor → cor que leva `old` e sua rampa para `new` com os mesmos desvios.

    `others`: outras cores-base trocadas no mesmo mapa (um tom é atribuído à
    família mais próxima, para duas famílias parecidas não se misturarem).
    """
    colors = Sprite(sprite.pixels).colors()
    L0, C0, h0 = to_lch(old)
    L1, C1, h1 = to_lch(new)
    rivals = [o for o in (others or []) if o != old]
    result: dict[RGBA, RGBA] = {}
    for c in family(colors, old):
        lab = srgb_to_oklab(np.array(c[:3]))
        if rivals:
            dists = [np.sum((lab - srgb_to_oklab(np.array(r[:3]))) ** 2) for r in rivals]
            if min(dists) < np.sum((lab - srgb_to_oklab(np.array(old[:3]))) ** 2):
                continue
        L, C, h = to_lch(c)
        dh = (h - h0 + 180) % 360 - 180
        scale = C / C0 if C0 > 0.03 else 1.0
        result[c] = from_lch(min(0.98, max(0.03, L1 + (L - L0))), C1 * scale if C0 > 0.03 else C1, h1 + dh, c[3])
    result[old] = new
    return result


def merge_close(frames: list[Sprite], min_delta: float = 0.03) -> list[Sprite]:
    """Funde cores quase iguais (ΔE OKLab < min_delta) em todos os quadros juntos;
    fica a cor mais frequente do grupo."""
    if not frames:
        return frames
    colors = Sprite(np.concatenate([f.pixels for f in frames], axis=1)).colors()
    labs = [srgb_to_oklab(np.array(c[:3])) for c in colors]
    mapping: dict[RGBA, RGBA] = {}
    for i, c in enumerate(colors):  # do mais frequente para o menos
        if c in mapping:
            continue
        for j in range(i + 1, len(colors)):
            if colors[j] not in mapping and colors[j][3] == c[3] and np.sqrt(((labs[i] - labs[j]) ** 2).sum()) < min_delta:
                mapping[colors[j]] = c
    if not mapping:
        return frames
    return [swap_exact(f, mapping) for f in frames]


def to_palette(sprite: Sprite, colors: list[RGBA]) -> Sprite:
    """Mapeia cada cor para a mais próxima de uma paleta (em OKLab)."""
    out = sprite.copy()
    palette = np.array([c[:3] for c in colors if c[3] > 0])
    opaque = out.pixels[..., 3] > 0
    idx = nearest(out.pixels[opaque, :3], palette)
    out.pixels[opaque, :3] = palette[idx]
    return out


def load_maps(path: str | Path) -> dict[str, dict[str, str]]:
    """Lê um arquivo de mapas: {"mapas": {"nome": {"#de": "#para", ...}}}."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: JSON inválido ({exc})") from None
    maps = data.get("mapas", data)
    if not isinstance(maps, dict) or not all(isinstance(v, dict) for v in maps.values()):
        raise ValueError(f"{path}: esperado {{\"mapas\": {{\"nome\": {{\"#de\": \"#para\"}}}}}}")
    return maps


def parse_swaps(pairs: dict[str, str] | list[str]) -> list[tuple[RGBA, RGBA]]:
    """Aceita {"#de": "#para"} ou ["#de:#para", ...]."""
    items = pairs.items() if isinstance(pairs, dict) else [p.split(":", 1) for p in pairs]
    out = []
    for item in items:
        if len(item) != 2:
            raise ValueError(f"troca inválida: {item!r} (use #de:#para)")
        out.append((parse_color(item[0]), parse_color(item[1])))
    return out


def recolor_sprite(sprite: Sprite, swaps: list[tuple[RGBA, RGBA]] = (), tint: str | None = None,
                   palette: list[RGBA] | None = None, keep_ramps: bool = True) -> Sprite:
    out = sprite
    if swaps:
        mapping: dict[RGBA, RGBA] = {}
        bases = [old for old, _ in swaps]
        for old, new in swaps:
            if keep_ramps:
                for k, v in swap_family(sprite, old, new, bases).items():
                    mapping.setdefault(k, v)
            mapping[old] = new
        out = swap_exact(out, mapping)
    if tint:
        out = apply_tint(out, tint)
    if palette:
        out = to_palette(out, palette)
    return out


def recolor(art: Art, name: str | None = None, **kwargs) -> Art:
    frames = [recolor_sprite(f, **kwargs) for f in art.frames]
    return Art(name or art.name, frames, art.fps, dict(art.meta))
