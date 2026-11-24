"""Retoque por código de uma spec (o "pincel" do ciclo do crítico).

Cada operação é um dicionário com uma chave; a lista é aplicada em ordem
(`ia retocar <spec> <ops.json>`). Coordenadas no pixel lógico.

  {"pixels": [[x, y, "#hex"], ...]}                      pinta pixels ("transparent" apaga)
  {"retangulo": [x0, y0, x1, y1, "#de", "#para"]}        troca uma cor dentro da caixa
  {"familia": ["#antiga", "#nova"]}                       troca a família de cor (rampa inteira)
  {"rampa": [x0, y0, x1, y1, ["#escuro", ..., "#claro"]], "so_cores": [...]}
                                                          caixa → N tons pela luminância
  {"moda": [x0, y0, x1, y1], "janela": 3}                funde o ruído (cor mais comum na janela)
  {"traco": [[[x, y, largura], ...], "#hex"]}            polilinha que afina/engrossa (dobras)
  {"rim": [x0, y0, x1, y1, "#hex", "esq|dir|cima"], "fora": "#fundo"}
                                                          1 px na borda da silhueta do lado dado
  {"poligono_fundo": [[[x, y], ...], "#de", "#para"]}    troca a cor FORA do polígono (fundo)
  {"apagar": [x0, y0, x1, y1]}                           caixa → transparente
  {"transparente": [[x, y], ymin]}                       flood fill da cor da semente → transparente
  {"deslocar": [dx, dy, "#preenchimento"]}               move a figura (composição)
  {"escalar": [x0, y0, x1, y1, fator]}                   amplia a caixa por vizinho (cabeça maior)
  {"limpar_olho": [x0, y0, x1, y1, "#pele"]}             escuros/brilhos da caixa → pele
  {"selout": true} | {"limpeza": n}                      contorno seletivo | órfãos
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from .palettes import parse_color
from .process import cleanup
from .recolor import swap_exact, swap_family
from .shading import selout
from .sprite import Sprite

LUMA = np.array([0.299, 0.587, 0.114])


def _rgba(value) -> np.ndarray:
    return np.array(parse_color(value), dtype=np.uint8)


def _match(px: np.ndarray, color) -> np.ndarray:
    return np.all(px == _rgba(color), axis=-1)


def apply_ops(sprite: Sprite, ops: list[dict]) -> Sprite:
    sprite = sprite.copy()
    for i, op in enumerate(ops):
        kind = next((k for k in op if k in HANDLERS), None)
        if kind is None:
            raise ValueError(f"retoque #{i + 1}: operação desconhecida {sorted(op)}")
        try:
            sprite = HANDLERS[kind](sprite, op) or sprite
        except (TypeError, ValueError, IndexError) as exc:
            raise ValueError(f"retoque #{i + 1} ({kind}): {exc}") from None
    return sprite


def _pixels(s: Sprite, op: dict) -> None:
    h, w = s.pixels.shape[:2]
    for x, y, c in op["pixels"]:
        if 0 <= x < w and 0 <= y < h:
            s.pixels[y, x] = parse_color(c)


def _rect(s: Sprite, op: dict) -> None:
    x0, y0, x1, y1, a, b = op["retangulo"]
    region = s.pixels[y0:y1, x0:x1]
    region[_match(region, a)] = _rgba(b)


def _family(s: Sprite, op: dict) -> Sprite:
    old, new = (parse_color(c) for c in op["familia"])
    return swap_exact(s, swap_family(s, old, new))


def _ramp(s: Sprite, op: dict) -> None:
    x0, y0, x1, y1, ramp = op["rampa"]
    ramp = np.array([parse_color(c) for c in ramp], dtype=np.uint8)
    region = s.pixels[y0:y1, x0:x1]
    mask = region[..., 3] > 0
    if op.get("so_cores"):
        mask &= np.any([_match(region, c) for c in op["so_cores"]], axis=0)
    if not mask.any():
        return
    lum = region[..., :3].astype(float) @ LUMA
    cuts = np.quantile(lum[mask], np.linspace(0, 1, len(ramp) + 1)[1:-1])
    region[mask] = ramp[np.searchsorted(cuts, lum)[mask]]


def _mode(s: Sprite, op: dict) -> None:
    x0, y0, x1, y1 = op["moda"]
    k = int(op.get("janela", 3))
    r = k // 2
    src = s.pixels.copy()
    h, w = src.shape[:2]
    for y in range(max(r, y0), min(h - r, y1)):
        for x in range(max(r, x0), min(w - r, x1)):
            if src[y, x, 3] == 0:
                continue
            block = src[y - r:y - r + k, x - r:x - r + k].reshape(-1, 4)
            block = block[block[:, 3] > 0]
            values, counts = np.unique(block, axis=0, return_counts=True)
            if counts.max() > len(block) // 2:
                s.pixels[y, x] = values[counts.argmax()]


def _stroke(s: Sprite, op: dict) -> None:
    pts, c = op["traco"]
    col = _rgba(c)
    h, w = s.pixels.shape[:2]
    for (xa, ya, wa), (xb, yb, wb) in zip(pts, pts[1:]):
        n = max(abs(xb - xa), abs(yb - ya)) + 1
        for t in np.linspace(0, 1, n):
            x, y = round(xa + (xb - xa) * t), round(ya + (yb - ya) * t)
            width = max(1, round(wa + (wb - wa) * t))
            for dx in range(-(width // 2), width - width // 2):
                if 0 <= y < h and 0 <= x + dx < w and s.pixels[y, x + dx, 3] > 0:
                    s.pixels[y, x + dx] = col


def _rim(s: Sprite, op: dict) -> None:
    x0, y0, x1, y1, c, side = op["rim"]
    col = _rgba(c)
    inside = s.pixels[..., 3] > 0
    if op.get("fora"):  # fundo opaco: "fora" é a cor do fundo
        inside = ~_match(s.pixels, op["fora"])
    if side in ("esq", "dir"):
        for y in range(y0, y1):
            xs = np.nonzero(inside[y, x0:x1])[0]
            if len(xs):
                s.pixels[y, x0 + (xs[0] if side == "esq" else xs[-1])] = col
    elif side == "cima":
        for x in range(x0, x1):
            ys = np.nonzero(inside[y0:y1, x])[0]
            if len(ys):
                s.pixels[y0 + ys[0], x] = col
    else:
        raise ValueError(f"lado deve ser esq, dir ou cima, recebido {side!r}")


def _polygon_bg(s: Sprite, op: dict) -> None:
    poly, a, b = op["poligono_fundo"]
    mask = Image.new("L", (s.width, s.height), 0)
    ImageDraw.Draw(mask).polygon([tuple(p) for p in poly], fill=255)
    hit = _match(s.pixels, a) & (np.array(mask) == 0)
    s.pixels[hit] = _rgba(b)


def _erase(s: Sprite, op: dict) -> None:
    x0, y0, x1, y1 = op["apagar"]
    s.pixels[y0:y1, x0:x1] = 0


def _flood_clear(s: Sprite, op: dict) -> None:
    (sx, sy), ymin = op["transparente"]
    old = s.pixels[sy, sx].copy()
    h, w = s.pixels.shape[:2]
    stack, seen = [(sx, sy)], set()
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and ymin <= y < h):
            continue
        seen.add((x, y))
        if not np.array_equal(s.pixels[y, x], old):
            continue
        s.pixels[y, x] = 0
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]


def _shift(s: Sprite, op: dict) -> None:
    dx, dy, fill = op["deslocar"]
    moved = np.empty_like(s.pixels)
    moved[...] = _rgba(fill)
    h, w = moved.shape[:2]
    src = s.pixels[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
    moved[max(0, dy):max(0, dy) + src.shape[0], max(0, dx):max(0, dx) + src.shape[1]] = src
    s.pixels[...] = moved


def _scale(s: Sprite, op: dict) -> None:
    x0, y0, x1, y1, factor = op["escalar"]
    box = Image.fromarray(s.pixels[y0:y1, x0:x1].copy(), "RGBA")
    big = np.array(box.resize((round(box.width * factor), round(box.height * factor)), Image.Resampling.NEAREST))
    region = s.pixels[y0:y1, x0:x1]
    region[region[..., 3] > 0] = 0
    bx, by = (x0 + x1) // 2 - big.shape[1] // 2, y1 - big.shape[0]
    h, w = s.pixels.shape[:2]
    ys, xs = np.nonzero(big[..., 3] > 0)
    ty, tx = ys + by, xs + bx
    ok = (ty >= 0) & (ty < h) & (tx >= 0) & (tx < w)
    s.pixels[ty[ok], tx[ok]] = big[ys[ok], xs[ok]]


def _clear_eye(s: Sprite, op: dict) -> None:
    x0, y0, x1, y1, c = op["limpar_olho"]
    region = s.pixels[y0:y1, x0:x1]
    lum = region[..., :3].astype(float) @ LUMA
    region[((lum < 120) | (lum > 200)) & (region[..., 3] > 0)] = _rgba(c)


HANDLERS = {
    "pixels": _pixels, "retangulo": _rect, "familia": _family, "rampa": _ramp, "moda": _mode,
    "traco": _stroke, "rim": _rim, "poligono_fundo": _polygon_bg, "apagar": _erase,
    "transparente": _flood_clear, "deslocar": _shift, "escalar": _scale, "limpar_olho": _clear_eye,
    "selout": lambda s, op: selout(s), "limpeza": lambda s, op: cleanup(s, int(op["limpeza"])),
}
