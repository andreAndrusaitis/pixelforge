"""Cor perceptual (OKLab): conversão, cor mais próxima e paleta por k-means.

OKLab mede diferenças de cor como o olho percebe, o que mantém tons de pele
e sombras sutis corretos ao reduzir a paleta.
"""

from __future__ import annotations

import numpy as np

_M1 = np.array([
    [0.4122214708, 0.5363325363, 0.0514459929],
    [0.2119034982, 0.6806995451, 0.1073969566],
    [0.0883024619, 0.2817188376, 0.6299787005],
])
_M2 = np.array([
    [0.2104542553, 0.7936177850, -0.0040720468],
    [1.9779984951, -2.4285922050, 0.4505937099],
    [0.0259040371, 0.7827717662, -0.8086757660],
])
_M2_INV = np.array([
    [1.0, 0.3963377774, 0.2158037573],
    [1.0, -0.1055613458, -0.0638541728],
    [1.0, -0.0894841775, -1.2914855480],
])
_M1_INV = np.array([
    [4.0767416621, -3.3077115913, 0.2309699292],
    [-1.2684380046, 2.6097574011, -0.3413193965],
    [-0.0041960863, -0.7034186147, 1.7076147010],
])


def srgb_to_oklab(rgb: np.ndarray) -> np.ndarray:
    """(..., 3) sRGB 0–255 → (..., 3) OKLab (L em 0–1)."""
    c = np.asarray(rgb, dtype=np.float64) / 255.0
    linear = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    lms = np.cbrt(linear @ _M1.T)
    return lms @ _M2.T


def oklab_to_srgb(lab: np.ndarray) -> np.ndarray:
    """(..., 3) OKLab → (..., 3) sRGB uint8."""
    lms = (np.asarray(lab, dtype=np.float64) @ _M2_INV.T) ** 3
    linear = np.clip(lms @ _M1_INV.T, 0, 1)
    c = np.where(linear <= 0.0031308, linear * 12.92, 1.055 * linear ** (1 / 2.4) - 0.055)
    return np.clip(np.round(c * 255), 0, 255).astype(np.uint8)


def nearest_lab(lab: np.ndarray, palette_lab: np.ndarray, chunk: int = 65536) -> np.ndarray:
    """Índice da cor da paleta mais próxima para cada cor (em OKLab)."""
    flat = lab.reshape(-1, 3)
    out = np.empty(len(flat), dtype=np.int64)
    for start in range(0, len(flat), chunk):
        part = flat[start : start + chunk]
        out[start : start + chunk] = ((part[:, None, :] - palette_lab[None]) ** 2).sum(axis=2).argmin(axis=1)
    return out.reshape(lab.shape[:-1])


def nearest(rgb: np.ndarray, palette_rgb: np.ndarray) -> np.ndarray:
    return nearest_lab(srgb_to_oklab(rgb), srgb_to_oklab(palette_rgb))


def kmeans_palette(rgb: np.ndarray, k: int, weights: np.ndarray | None = None,
                   iterations: int = 20, seed: int = 0) -> np.ndarray:
    """Paleta de até k cores (N, 3) uint8-like int32, k-means ponderado em OKLab.

    Inicialização k-means++: sementes proporcionais à distância², então regiões
    pequenas de cor muito diferente (olhos, brilhos) ganham cor própria.
    Cores são agrupadas em 32 níveis por canal antes, para caber em memória.
    """
    rgb = np.asarray(rgb).reshape(-1, 3)
    w = np.ones(len(rgb)) if weights is None else np.asarray(weights, dtype=np.float64).reshape(-1)
    if len(rgb) == 0:
        return np.zeros((1, 3), dtype=np.int32)

    exact, inverse = np.unique(rgb, axis=0, return_inverse=True)
    if len(exact) <= k:
        return exact.astype(np.int32)

    binned = (rgb.astype(np.int64) >> 3)
    keys = binned[:, 0] * 1024 + binned[:, 1] * 32 + binned[:, 2]
    uniq_keys, inv = np.unique(keys, return_inverse=True)
    bin_w = np.bincount(inv, weights=w)
    lab_all = srgb_to_oklab(rgb)
    points = np.stack([np.bincount(inv, weights=lab_all[:, i] * w) for i in range(3)], axis=1)
    points /= np.maximum(bin_w, 1e-12)[:, None]
    weights_b = bin_w

    rng = np.random.default_rng(seed)
    centers = [points[np.argmax(weights_b)]]
    dist = ((points - centers[0]) ** 2).sum(axis=1)
    for _ in range(1, min(k, len(points))):
        prob = dist * np.sqrt(weights_b)
        if prob.sum() <= 0:
            break
        centers.append(points[rng.choice(len(points), p=prob / prob.sum())])
        dist = np.minimum(dist, ((points - centers[-1]) ** 2).sum(axis=1))
    centers = np.array(centers)

    for _ in range(iterations):
        labels = ((points[:, None, :] - centers[None]) ** 2).sum(axis=2).argmin(axis=1)
        sums = np.stack([np.bincount(labels, weights=points[:, i] * weights_b, minlength=len(centers))
                         for i in range(3)], axis=1)
        totals = np.bincount(labels, weights=weights_b, minlength=len(centers))
        new = np.where(totals[:, None] > 0, sums / np.maximum(totals, 1e-12)[:, None], centers)
        if np.allclose(new, centers, atol=1e-5):
            break
        centers = new

    return np.unique(oklab_to_srgb(centers).astype(np.int32), axis=0)
