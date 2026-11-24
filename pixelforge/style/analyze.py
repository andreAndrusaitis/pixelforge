"""Decomposição técnica de uma pixel art: grade real, paleta, valor, clusters,
contorno, luz, composição e figura. Só numpy + Pillow.

Usado em `estilo analisar` (referências → docs/estilo/analises/<n>.json) e em
`estilo comparar` (a arte nova medida com a mesma régua).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from ..color import srgb_to_oklab

MERGE_DELTA = 0.035        # tons mais próximos que isso (OKLab) contam como a mesma cor
MIN_SHARE = 0.002          # cor "efetiva": ao menos 0,2% dos pixels


# --------------------------------------------------------------------------
# grade real do pixel
# --------------------------------------------------------------------------


def _lattice_score(d: np.ndarray, scale: float, offset: float) -> float:
    n = len(d) + 1
    pos = np.round(np.arange(offset, n, scale)).astype(int) - 1
    pos = pos[(pos >= 0) & (pos < len(d))]
    if len(pos) < 3:
        return 0.0
    on = d[pos].mean()
    mask = np.ones(len(d), bool)
    mask[pos] = False
    off = d[mask].mean() if mask.any() else 0.0
    return float(on / (off + 1e-6))


def _best_axis(d: np.ndarray, max_scale: float) -> tuple[float, float, float]:
    """Melhor (escala, offset, razão). Múltiplos da escala real também pontuam alto
    (3× a grade ainda cai em bordas); fica a MENOR escala perto da melhor razão."""
    per_scale = []
    for scale in np.arange(2.0, max_scale + 0.001, 0.05):
        best = (float(scale), 0.0, 0.0)
        for offset in np.arange(0.0, scale, 0.5):
            r = _lattice_score(d, scale, offset)
            if r > best[2]:
                best = (float(scale), float(offset), r)
        per_scale.append(best)
    top = max(r for _, _, r in per_scale)
    for cand in per_scale:
        if cand[2] >= 0.75 * top:
            return cand
    return (1.0, 0.0, 0.0)


def detect_grid(rgb: np.ndarray, max_scale: float = 16.0) -> dict:
    """Escala do "pixel lógico" em x e y (aceita escala fracionária de imagens
    reamostradas). Razão < 1.6 = sem grade clara (imagem já nativa)."""
    g = rgb.astype(np.float64).mean(axis=-1)
    # borda "de verdade" (> 6 níveis) contada por coluna/linha: a grade de pixel se
    # alinha entre linhas; ruído de compressão (webp/jpg) e degradês, não
    dx = (np.abs(np.diff(g, axis=1)) > 6).mean(axis=0)
    dy = (np.abs(np.diff(g, axis=0)) > 6).mean(axis=1)
    sx, ox, rx = _best_axis(dx, max_scale)
    sy, oy, ry = _best_axis(dy, max_scale)
    if rx < 1.6 and ry < 1.6:
        # grade irregular (IA, reamostragem, compressão): estima o tamanho do bloco
        # pelo comprimento de corrida mais comum de cor igual
        s = _run_scale(g, max_scale)
        if s >= 3:
            return {"escala": s, "escala_x": s, "escala_y": s, "offset": [0, 0], "confianca": 0.0,
                    "metodo": "corridas"}
        return {"escala": 1.0, "escala_x": 1.0, "escala_y": 1.0, "offset": [0, 0], "confianca": round(max(rx, ry), 2)}
    if rx < 1.6:
        sx, ox = sy, oy
    if ry < 1.6:
        sy, oy = sx, ox
    if max(sx, sy) / min(sx, sy) > 1.6:          # um eixo pegou um múltiplo: vale o menor
        small = (sx, ox) if sx < sy else (sy, oy)
        sx, ox = sy, oy = small
    return {"escala": round((sx + sy) / 2, 2), "escala_x": round(sx, 2), "escala_y": round(sy, 2),
            "offset": [round(ox, 1), round(oy, 1)], "confianca": round(min(rx, ry), 2)}


def _run_scale(g: np.ndarray, max_scale: float) -> float:
    counts = np.zeros(int(max_scale) + 2)
    for arr in (g, g.T):
        same = np.abs(np.diff(arr, axis=1)) <= 3
        for row in same[:: max(1, len(same) // 300)]:
            edges = np.flatnonzero(np.diff(np.concatenate([[0], row.astype(int), [0]])))
            runs = edges[1::2] - edges[::2] + 1
            runs = runs[(runs >= 2) & (runs <= max_scale)]
            np.add.at(counts, runs, 1)
    lengths = np.arange(len(counts))
    area = counts * lengths                     # quantos pixels cada comprimento cobre
    area[:3] = 0
    if area.sum() == 0:
        return 1.0
    cum = np.cumsum(area) / area.sum()
    return float(int(np.searchsorted(cum, 0.5)))   # mediana ponderada pela área


def to_native(rgba: np.ndarray, grid: dict) -> np.ndarray:
    """Reduz à resolução nativa: mediana do miolo de cada célula da grade."""
    sx, sy = grid["escala_x"], grid["escala_y"]
    if sx <= 1.01 and sy <= 1.01:
        return rgba.copy()
    ox, oy = grid["offset"]
    h, w = rgba.shape[:2]
    nx, ny = max(1, int(round((w - ox) / sx))), max(1, int(round((h - oy) / sy)))
    xs = np.minimum(ox + np.arange(nx + 1) * sx, w)
    ys = np.minimum(oy + np.arange(ny + 1) * sy, h)
    out = np.zeros((ny, nx, 4), np.uint8)
    for j in range(ny):
        y0, y1 = int(round(ys[j])), int(round(ys[j + 1]))
        cy0, cy1 = y0 + (y1 - y0) // 4, y1 - (y1 - y0) // 4
        for i in range(nx):
            x0, x1 = int(round(xs[i])), int(round(xs[i + 1]))
            cx0, cx1 = x0 + (x1 - x0) // 4, x1 - (x1 - x0) // 4
            cell = rgba[cy0:max(cy1, cy0 + 1), cx0:max(cx1, cx0 + 1)].reshape(-1, 4)
            out[j, i] = np.median(cell, axis=0).astype(np.uint8)
    return out


# --------------------------------------------------------------------------
# paleta
# --------------------------------------------------------------------------


@dataclass
class Palette:
    centers_lab: np.ndarray     # (k, 3)
    centers_rgb: np.ndarray     # (k, 3) uint8
    counts: np.ndarray          # (k,)
    labels: np.ndarray          # (h, w) índice da cor (−1 = transparente)


def merge_palette(rgb: np.ndarray, opaque: np.ndarray, delta: float = MERGE_DELTA) -> Palette:
    flat = rgb.reshape(-1, 3)
    keep = opaque.reshape(-1)
    colors, inverse, counts = np.unique(flat[keep], axis=0, return_inverse=True, return_counts=True)
    lab = srgb_to_oklab(colors)
    order = np.argsort(-counts)
    centers: list[np.ndarray] = []
    weights: list[float] = []
    rgb_sum: list[np.ndarray] = []
    assign = np.zeros(len(colors), int)
    for idx in order:
        if centers:
            d = np.sqrt(((np.array(centers) - lab[idx]) ** 2).sum(axis=1))
            j = int(d.argmin())
            if d[j] < delta:
                assign[idx] = j
                wsum = weights[j] + counts[idx]
                centers[j] = (centers[j] * weights[j] + lab[idx] * counts[idx]) / wsum
                rgb_sum[j] = rgb_sum[j] + colors[idx].astype(np.float64) * counts[idx]
                weights[j] = wsum
                continue
        assign[idx] = len(centers)
        centers.append(lab[idx].copy())
        weights.append(float(counts[idx]))
        rgb_sum.append(colors[idx].astype(np.float64) * counts[idx])
    labels = np.full(flat.shape[0], -1, int)
    labels[keep] = assign[inverse.reshape(-1)]
    w = np.array(weights)
    centers_rgb = np.array([s / wi for s, wi in zip(rgb_sum, weights)]).round().astype(np.uint8)
    return Palette(np.array(centers), centers_rgb, w, labels.reshape(rgb.shape[:2]))


def _hue_deg(lab: np.ndarray) -> np.ndarray:
    return (np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) + 360) % 360


def ramps(pal: Palette, min_chroma: float = 0.025) -> list[list[int]]:
    """Agrupa cores em rampas (mesma família de matiz, do escuro ao claro)."""
    chroma = np.hypot(pal.centers_lab[:, 1], pal.centers_lab[:, 2])
    hue = _hue_deg(pal.centers_lab)
    groups: dict[int, list[int]] = {}
    for i in range(len(pal.counts)):
        key = -1 if chroma[i] < min_chroma else int(((hue[i] + 15) % 360) // 30)
        groups.setdefault(key, []).append(i)
    out = []
    for key, idx in sorted(groups.items()):
        idx.sort(key=lambda i: pal.centers_lab[i, 0])
        out.append(idx)
    return out


def hue_shift(pal: Palette) -> dict:
    """Quanto a matiz anda da sombra para a luz dentro de cada rampa (hue shifting)."""
    shifts = []
    share = pal.counts / pal.counts.sum()
    for ramp in ramps(pal):
        ramp = [i for i in ramp if share[i] > MIN_SHARE / 2]
        if len(ramp) < 3:
            continue
        lab = pal.centers_lab[ramp]
        if lab[-1, 0] - lab[0, 0] < 0.15:
            continue
        h = _hue_deg(lab)
        diff = (h[-1] - h[0] + 180) % 360 - 180
        shifts.append(abs(float(diff)))
    return {"rampas_medidas": len(shifts), "variacao_media_graus": round(float(np.mean(shifts)), 1) if shifts else 0.0}


# --------------------------------------------------------------------------
# máscaras e regiões
# --------------------------------------------------------------------------


def figure_mask(rgba: np.ndarray) -> tuple[np.ndarray | None, str]:
    """Máscara da figura: alfa, ou fundo liso tirado por inundação a partir da borda.
    None quando a imagem é uma cena cheia (fundo não liso)."""
    alpha = rgba[..., 3]
    if (alpha < 250).mean() > 0.05:
        return alpha > 127, "alfa"
    lab = srgb_to_oklab(rgba[..., :3])
    h, w = alpha.shape
    border = np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])
    ref = np.median(border, axis=0)
    close = np.sqrt(((border - ref) ** 2).sum(axis=1)) < 0.06
    if close.mean() < 0.85:
        return None, "cena"
    near = np.sqrt(((lab - ref) ** 2).sum(axis=-1)) < 0.07
    bg = np.zeros((h, w), bool)
    q: deque = deque()
    for y in range(h):
        for x in (0, w - 1):
            if near[y, x] and not bg[y, x]:
                bg[y, x] = True
                q.append((y, x))
    for x in range(w):
        for y in (0, h - 1):
            if near[y, x] and not bg[y, x]:
                bg[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= yy < h and 0 <= xx < w and near[yy, xx] and not bg[yy, xx]:
                bg[yy, xx] = True
                q.append((yy, xx))
    fig = ~bg
    if fig.mean() < 0.02:
        return None, "cena"
    return fig, "fundo-liso"


def components(labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Componentes conexos (4 vizinhos) de mesma cor. Devolve (mapa de id, tamanhos)."""
    h, w = labels.shape
    comp = np.full((h, w), -1, int)
    sizes = []
    for y in range(h):
        for x in range(w):
            if comp[y, x] >= 0 or labels[y, x] < 0:
                continue
            cid = len(sizes)
            color = labels[y, x]
            comp[y, x] = cid
            stack = [(y, x)]
            n = 0
            while stack:
                cy, cx = stack.pop()
                n += 1
                for yy, xx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= yy < h and 0 <= xx < w and comp[yy, xx] < 0 and labels[yy, xx] == color:
                        comp[yy, xx] = cid
                        stack.append((yy, xx))
            sizes.append(n)
    return comp, np.array(sizes, int)


def boundary(mask: np.ndarray) -> np.ndarray:
    pad = np.pad(mask, 1, constant_values=False)
    inner = pad[1:-1, :-2] & pad[1:-1, 2:] & pad[:-2, 1:-1] & pad[2:, 1:-1]
    return mask & ~inner


def _box(a: np.ndarray, k: int) -> np.ndarray:
    pad = np.pad(a, k // 2, mode="edge")
    c = np.cumsum(np.cumsum(pad, axis=0), axis=1)
    c = np.pad(c, ((1, 0), (1, 0)))
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


# --------------------------------------------------------------------------
# análise completa
# --------------------------------------------------------------------------


def analyze_array(rgba: np.ndarray, native: bool = False) -> tuple[dict, dict]:
    """(métricas, extras para a folha visual). `native=True` pula a detecção de grade."""
    grid = {"escala": 1.0, "escala_x": 1.0, "escala_y": 1.0, "offset": [0, 0], "confianca": 0.0}
    if not native:
        grid = detect_grid(rgba[..., :3])
    img = to_native(rgba, grid)
    h, w = img.shape[:2]
    mask, mask_kind = figure_mask(img)
    opaque = img[..., 3] > 127
    pal = merge_palette(img[..., :3], opaque)
    share = pal.counts / max(pal.counts.sum(), 1)
    lab = srgb_to_oklab(img[..., :3])
    L = lab[..., 0]
    chroma = np.hypot(lab[..., 1], lab[..., 2])
    region = mask if mask is not None else opaque

    m: dict = {"tamanho_nativo": [int(w), int(h)], "grade": grid, "mascara": mask_kind}

    # paleta
    eff = int((share >= MIN_SHARE).sum())
    cl = np.hypot(pal.centers_lab[:, 1], pal.centers_lab[:, 2])
    mean_c = float((cl * share).sum())
    accent = None
    cand = [i for i in range(len(share)) if share[i] < 0.15 and share[i] >= MIN_SHARE and cl[i] > max(1.6 * mean_c, 0.08)]
    if cand:
        a = max(cand, key=lambda i: cl[i])
        accent = {"cor": "#%02x%02x%02x" % tuple(int(v) for v in pal.centers_rgb[a]), "area": round(float(share[a]), 3)}
    m["paleta"] = {"cores_efetivas": eff, "cores_total": int(len(share)), "croma_media": round(mean_c, 3),
                   "destaque": accent, **hue_shift(pal)}

    # valor
    Lr = L[region] if region.any() else L.reshape(-1)
    p5, p95 = np.percentile(Lr, [5, 95])
    m["valor"] = {"media": round(float(Lr.mean()), 3), "desvio": round(float(Lr.std()), 3),
                  "contraste": round(float(p95 - p5), 3)}
    if mask is not None and (~mask).any():
        m["valor"]["figura_x_fundo"] = round(float(abs(L[mask].mean() - L[~mask].mean())), 3)

    # clusters
    labels = np.where(region, pal.labels, -1)
    comp, sizes = components(labels)
    npx = int(region.sum()) or 1
    m["clusters"] = {
        "tamanho_medio": round(float(npx / max(len(sizes), 1)), 2),
        "tamanho_mediano_ponderado": float(np.median(np.repeat(sizes, sizes))) if len(sizes) else 0.0,
        "orfaos": round(float((sizes == 1).sum() / npx), 4),
    }
    lb = pal.labels
    c = lb[1:-1, 1:-1]
    l_, r_, u_, d_ = lb[1:-1, :-2], lb[1:-1, 2:], lb[:-2, 1:-1], lb[2:, 1:-1]
    checker = (l_ == r_) & (u_ == d_) & (c != l_) & (c != u_) & (c >= 0)
    m["clusters"]["dithering"] = round(float(checker.mean()), 4)
    # densidade de detalhe: pixels da região com algum vizinho de outra cor
    lp = np.pad(labels, 1, constant_values=-2)
    ctr = lp[1:-1, 1:-1]
    diff = (lp[1:-1, :-2] != ctr) | (lp[1:-1, 2:] != ctr) | (lp[:-2, 1:-1] != ctr) | (lp[2:, 1:-1] != ctr)
    m["clusters"]["densidade_detalhe"] = round(float((diff & region).sum() / npx), 3)
    # tons por rampa e níveis de valor
    rs = [len([i for i in r if share[i] >= MIN_SHARE]) for r in ramps(pal)]
    rs = [n for n in rs if n > 0]
    m["paleta"]["tons_por_rampa"] = round(float(np.mean(rs)), 2) if rs else 0.0
    lv = np.round(Lr * 20).astype(int)
    _, lc = np.unique(lv, return_counts=True)
    m["valor"]["niveis"] = int((lc / lc.sum() >= 0.005).sum())

    # contorno e rim light
    extras: dict = {"native": img, "palette": pal, "components": comp, "L": L, "mask": mask}
    if mask is not None:
        edge = boundary(mask)
        Lf = L[mask]
        dark_t, light_t = np.percentile(Lf, [18, 85])
        e_L, e_c = L[edge], chroma[edge]
        dark = e_L <= dark_t
        n_edge = max(int(edge.sum()), 1)
        m["contorno"] = {"escuro": round(float((dark & (e_c < 0.05)).sum() / n_edge), 3),
                         "colorido": round(float((dark & (e_c >= 0.05)).sum() / n_edge), 3),
                         "ausente": round(float((~dark).sum() / n_edge), 3)}
        rim = edge & (L >= light_t)
        rim_rgb = img[..., :3][rim]
        m["luz_de_borda"] = {"fracao": round(float(rim.sum() / n_edge), 3),
                             "cor": "#%02x%02x%02x" % tuple(int(v) for v in rim_rgb.mean(axis=0)) if len(rim_rgb) else None}
        extras["edge"] = edge

    # direção da luz: do centro da região para o centro das luzes (15% mais claros).
    # (o gradiente somado se anula em figuras com rim light dos dois lados)
    ys_r, xs_r = np.nonzero(region)
    if len(ys_r):
        lr = L[ys_r, xs_r]
        top = lr >= np.percentile(lr, 85)
        cx, cy = xs_r.mean(), ys_r.mean()
        span = max(int(np.ptp(xs_r)), int(np.ptp(ys_r)), 1)
        vx = float((xs_r[top].mean() - cx) / span)
        vy = float(-(ys_r[top].mean() - cy) / span)
    else:
        vx = vy = 0.0
    total = 0.5
    ang = (np.degrees(np.arctan2(vy, vx)) + 360) % 360
    m["luz"] = {"angulo_graus": round(float(ang), 1), "forca": round(float(np.hypot(vx, vy) / total), 3),
                "de_onde": _dir_name(ang)}
    extras["light"] = (vx, vy)

    # composição: saliência = contraste local + croma
    sal = np.abs(L - _box(L, 9)) + 0.5 * chroma
    thr = np.percentile(sal, 97)
    ys, xs = np.nonzero(sal >= thr)
    fx, fy = float(xs.mean() / w), float(ys.mean() / h)
    thirds = min(np.hypot(fx - a, fy - b) for a in (1 / 3, 2 / 3) for b in (1 / 3, 2 / 3))
    local_std = np.sqrt(np.maximum(_box(L ** 2, 5) - _box(L, 5) ** 2, 0))
    m["composicao"] = {"ponto_focal": [round(fx, 3), round(fy, 3)], "dist_tercos": round(float(thirds), 3),
                       "espaco_negativo": round(float((local_std < 0.02).mean()), 3)}
    if mask is not None:
        ys, xs = np.nonzero(mask)
        bw, bh = xs.max() - xs.min() + 1, ys.max() - ys.min() + 1
        m["composicao"]["ocupacao"] = round(float(bw * bh / (w * h)), 3)
        m["figura"] = _figure(mask, ys.min(), ys.max())
    extras["focal"] = (fx, fy)
    return m, extras


def _dir_name(ang: float) -> str:
    names = ["direita", "cima-direita", "cima", "cima-esquerda", "esquerda", "baixo-esquerda", "baixo", "baixo-direita"]
    return names[int(((ang + 22.5) % 360) // 45)]


def _figure(mask: np.ndarray, top: int, bottom: int) -> dict:
    height = int(bottom - top + 1)
    widths = mask[top:bottom + 1].sum(axis=1).astype(float)
    sm = np.convolve(widths, np.ones(3) / 3, mode="same")
    lo, hi = int(height * 0.1), max(int(height * 0.45), int(height * 0.1) + 2)
    head = None
    if hi - lo > 2 and sm[:lo + 1].max() > 0:
        neck = lo + int(sm[lo:hi].argmin())
        if sm[neck] < 0.85 * sm[:neck + 1].max():
            head = neck
    out = {"altura_px": height, "largura_px": int(widths.max())}
    if head:
        out["cabeca_px"] = int(head)
        out["proporcao_cabecas"] = round(height / head, 2)
    return out


def analyze_file(path: str | Path, native: bool = False) -> tuple[dict, dict]:
    with Image.open(path) as im:
        rgba = np.array(im.convert("RGBA"))
    m, extras = analyze_array(rgba, native=native)
    m = {"arquivo": Path(path).name, "tamanho_original": [int(rgba.shape[1]), int(rgba.shape[0])], **m}
    return m, extras
