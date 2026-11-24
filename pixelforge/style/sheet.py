"""Folha visual da decomposição: nativa, rampas da paleta, valores, clusters,
contorno + seta de luz + ponto focal, e as métricas em texto."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from .analyze import ramps

PANEL = 300
BG = (24, 20, 37)
INK = (234, 228, 214)
DIM = (150, 144, 160)


def _fit(arr: np.ndarray) -> Image.Image:
    img = Image.fromarray(arr)
    h, w = arr.shape[:2]
    s = max(1, min(PANEL // max(w, 1), PANEL // max(h, 1)))
    img = img.resize((w * s, h * s), Image.Resampling.NEAREST)
    if img.width > PANEL or img.height > PANEL:
        img.thumbnail((PANEL, PANEL), Image.Resampling.NEAREST)
    return img


def _panel(img: Image.Image, title: str) -> Image.Image:
    p = Image.new("RGB", (PANEL + 16, PANEL + 34), BG)
    p.paste(img.convert("RGBA"), ((PANEL + 16 - img.width) // 2, 28 + (PANEL - img.height) // 2), img.convert("RGBA"))
    ImageDraw.Draw(p).text((8, 8), title, fill=INK)
    return p


def _checker(h: int, w: int) -> np.ndarray:
    ys, xs = np.mgrid[0:h, 0:w]
    v = np.where(((xs // 4) + (ys // 4)) % 2 == 0, 60, 48).astype(np.uint8)
    return np.dstack([v, v, v, np.full((h, w), 255, np.uint8)])


def build_sheet(metrics: dict, extras: dict) -> Image.Image:
    native = extras["native"]
    h, w = native.shape[:2]
    base = _checker(h, w).astype(np.float64)
    a = native[..., 3:4] / 255.0
    flat = (native[..., :3] * a + base[..., :3] * (1 - a)).astype(np.uint8)
    panels = [_panel(_fit(flat), f"nativa {w}x{h} (grade x{metrics['grade']['escala']})")]

    pal = extras["palette"]
    rows = ramps(pal)
    share = pal.counts / pal.counts.sum()
    sw = Image.new("RGB", (PANEL, PANEL), BG)
    d = ImageDraw.Draw(sw)
    cell = max(6, min(28, PANEL // max(max((len(r) for r in rows), default=1), len(rows), 1)))
    for j, ramp in enumerate(rows[: PANEL // cell]):
        for i, idx in enumerate(ramp[: PANEL // cell]):
            if share[idx] < 0.0005:
                continue
            d.rectangle([i * cell, j * cell, i * cell + cell - 2, j * cell + cell - 2],
                        fill=tuple(int(v) for v in pal.centers_rgb[idx]))
    panels.append(_panel(sw, f"rampas ({metrics['paleta']['cores_efetivas']} cores efetivas)"))

    L = extras["L"]
    q = (np.clip(L, 0, 1) * 6).astype(int).clip(0, 5) * 51
    panels.append(_panel(_fit(np.dstack([q, q, q]).astype(np.uint8)), f"valores (contraste {metrics['valor']['contraste']})"))

    comp = extras["components"]
    rng = np.random.default_rng(3)
    colors = rng.integers(40, 255, size=(comp.max() + 2, 3)).astype(np.uint8)
    cm = colors[comp + 1]
    cm[comp < 0] = 20
    panels.append(_panel(_fit(cm), f"clusters (medio {metrics['clusters']['tamanho_medio']} px)"))

    over = flat.copy()
    over = (over * 0.45).astype(np.uint8)
    if extras.get("edge") is not None:
        over[extras["edge"]] = (255, 210, 90)
    oimg = _fit(over).convert("RGB")
    s = oimg.width / w
    dd = ImageDraw.Draw(oimg)
    fx, fy = extras["focal"]
    cx, cy = fx * oimg.width, fy * oimg.height
    dd.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], outline=(255, 90, 90), width=2)
    for t in (1 / 3, 2 / 3):
        dd.line([oimg.width * t, 0, oimg.width * t, oimg.height], fill=(90, 90, 120))
        dd.line([0, oimg.height * t, oimg.width, oimg.height * t], fill=(90, 90, 120))
    vx, vy = extras["light"]
    n = (vx * vx + vy * vy) ** 0.5 or 1
    ox, oy = oimg.width / 2, oimg.height / 2
    dd.line([ox, oy, ox + vx / n * 60, oy - vy / n * 60], fill=(255, 240, 160), width=3)
    dd.ellipse([ox + vx / n * 60 - 4, oy - vy / n * 60 - 4, ox + vx / n * 60 + 4, oy - vy / n * 60 + 4], fill=(255, 240, 160))
    panels.append(_panel(oimg, f"contorno, luz ({metrics['luz']['de_onde']}), foco"))

    text = Image.new("RGB", (PANEL + 16, PANEL + 34), BG)
    td = ImageDraw.Draw(text)
    y = 8
    for key in ("paleta", "valor", "clusters", "contorno", "luz_de_borda", "luz", "composicao", "figura"):
        if key not in metrics:
            continue
        vals = ", ".join(f"{k}={v}" for k, v in metrics[key].items() if not isinstance(v, (dict, list)) or k == "ponto_focal")
        td.text((8, y), key, fill=(255, 205, 117))
        y += 13
        for chunk in [vals[i:i + 46] for i in range(0, len(vals), 46)][:4]:
            td.text((12, y), chunk, fill=DIM)
            y += 12
        y += 3
    panels.append(text)

    pw, ph = panels[0].width, panels[0].height
    sheet = Image.new("RGB", (pw * 3, ph * 2 + 30), BG)
    ImageDraw.Draw(sheet).text((10, 8), f"decomposicao - {metrics.get('arquivo', '')}", fill=INK)
    for i, p in enumerate(panels):
        sheet.paste(p, ((i % 3) * pw, 30 + (i // 3) * ph))
    return sheet
