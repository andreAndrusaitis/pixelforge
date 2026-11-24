"""Filtros de imagem em numpy: Kuwahara, bordas (Sobel) e redução por blocos."""

from __future__ import annotations

import numpy as np


def _integral(a: np.ndarray) -> np.ndarray:
    """Imagem integral com linha/coluna de zeros no início."""
    out = np.zeros((a.shape[0] + 1, a.shape[1] + 1) + a.shape[2:], dtype=np.float64)
    out[1:, 1:] = a.cumsum(0).cumsum(1)
    return out


def kuwahara(rgb: np.ndarray, radius: int, valid: np.ndarray | None = None) -> np.ndarray:
    """Filtro de Kuwahara: achata áreas e preserva bordas.

    Para cada pixel, olha os 4 quadrantes (r+1)x(r+1) ao redor e usa a média do
    quadrante de menor variância de luminância. `valid` (bool HxW) restringe o
    cálculo aos pixels da figura, para o fundo não vazar nas bordas.
    """
    if radius < 1:
        return rgb.copy()
    h, w = rgb.shape[:2]
    r = radius
    img = rgb.astype(np.float64)
    weight = np.ones((h, w)) if valid is None else valid.astype(np.float64)
    lum = img @ np.array([0.299, 0.587, 0.114])

    pad = lambda a: np.pad(a, ((r, r), (r, r)) + ((0, 0),) * (a.ndim - 2), mode="edge")
    wp = np.pad(weight, r, mode="constant")
    S_w = _integral(wp)
    S_c = _integral(pad(img) * wp[..., None])
    S_l = _integral(pad(lum) * wp)
    S_l2 = _integral(pad(lum) ** 2 * wp)

    best_var = np.full((h, w), np.inf)
    result = img.copy()
    size = r + 1
    for oy, ox in ((0, 0), (0, r), (r, 0), (r, r)):
        y0, x0 = oy, ox
        y1, x1 = y0 + size, x0 + size

        def box(S):
            return S[y1 : y1 + h, x1 : x1 + w] - S[y0 : y0 + h, x1 : x1 + w] - S[y1 : y1 + h, x0 : x0 + w] + S[y0 : y0 + h, x0 : x0 + w]

        n = box(S_w)
        ok = n >= size * size * 0.5
        n_safe = np.maximum(n, 1e-9)
        mean_l = box(S_l) / n_safe
        var = np.where(ok, box(S_l2) / n_safe - mean_l**2, np.inf)
        better = var < best_var
        best_var = np.where(better, var, best_var)
        mean_c = box(S_c) / n_safe[..., None]
        result[better] = mean_c[better]
    return np.clip(result, 0, 255)


def sobel(lum: np.ndarray) -> np.ndarray:
    """Magnitude do gradiente (Sobel 3x3)."""
    p = np.pad(lum.astype(np.float64), 1, mode="edge")
    gx = (p[:-2, 2:] + 2 * p[1:-1, 2:] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[1:-1, :-2] + p[2:, :-2])
    gy = (p[2:, :-2] + 2 * p[2:, 1:-1] + p[2:, 2:]) - (p[:-2, :-2] + 2 * p[:-2, 1:-1] + p[:-2, 2:])
    return np.hypot(gx, gy)


def blocks(a: np.ndarray, k: int) -> np.ndarray:
    """(H*k, W*k, ...) → (H, W, k*k, ...): cada pixel da grade com seus k² pixels de origem."""
    h, w = a.shape[0] // k, a.shape[1] // k
    rest = a.shape[2:]
    v = a[: h * k, : w * k].reshape((h, k, w, k) + rest)
    v = np.moveaxis(v, 2, 1)
    return v.reshape((h, w, k * k) + rest)


def center_weights(k: int) -> np.ndarray:
    """Pesos (k*k,) maiores no centro do bloco: posições ficam mais precisas."""
    c = (k - 1) / 2
    ys, xs = np.mgrid[0:k, 0:k]
    d2 = ((ys - c) ** 2 + (xs - c) ** 2) / max(c, 0.5) ** 2
    return (0.6 + 0.4 * np.exp(-d2)).reshape(-1)
