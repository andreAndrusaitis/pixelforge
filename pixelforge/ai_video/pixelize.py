"""Pixelização temporal: clipe de vídeo da IA → animação em pixel art estável.

O vídeo da IA é liso, em alta resolução, e muda um pouco em todo quadro. Para virar
pixel art que não "ferve":

1. **fps baixo**: escolhe quadros do clipe para 8–12 fps (cara de animação);
2. **grade fixa**: recorta na proporção do alvo e reduz por média de área para a
   resolução nativa — o mesmo pixel do clipe cai sempre na mesma célula;
3. **mediana temporal** (janela de 3 quadros) antes de quantizar: some o ruído que
   aparece em um quadro só;
4. **paleta travada**: todos os quadros na mesma paleta (a da cena/sprite), em Oklab;
5. **histerese de cor**: um pixel só troca de cor se a nova for melhor que a atual
   por uma margem — é o que mata a cintilação entre duas cores vizinhas;
6. **limpeza de órfãos**: pixel isolado (nenhum vizinho igual) vira a cor da maioria;
7. **só o que se move**: com o quadro original (`base`), um pixel só é repintado onde o
   clipe mudou de verdade em relação ao seu 1º quadro (distância Oklab > `motion`); no
   resto fica o pixel original — preserva o dithering e os detalhes do artista;
8. **região**: fora das áreas animadas (`regiao`), o quadro original fica intacto.

Tudo determinístico e só numpy + Pillow.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

from ..color import kmeans_palette, srgb_to_oklab

HYSTERESIS = 0.035     # distância Oklab que a cor nova precisa ganhar da atual para trocar
MEDIAN = 3             # quadros da mediana temporal (ímpar; 1 = desliga)
KEY_DISTANCE = 0.12    # Oklab: até aqui da cor de fundo vira transparente (sprites)
MOTION = 0.06          # Oklab: mudança mínima, contra o 1º quadro do clipe, para repintar um pixel


@dataclass
class PixelizeOptions:
    size: tuple[int, int]                  # (largura, altura) nativas
    fps_in: float = 24.0
    fps_out: int = 12
    palette: np.ndarray | None = None      # (k, 3) uint8; None = k-means do clipe inteiro
    colors: int = 32                       # cores do k-means quando não há paleta
    hysteresis: float = HYSTERESIS
    median: int = MEDIAN
    cleanup: bool = True
    key: tuple[int, int, int] | None = None   # cor de fundo a remover (sprite → alfa)
    key_distance: float = KEY_DISTANCE
    motion: float | None = MOTION          # None = repinta tudo (sem detecção de movimento)


def resample_times(n_in: int, fps_in: float, fps_out: float) -> list[int]:
    """Índices de quadros do clipe para o fps de saída (sem passar do fim)."""
    if n_in <= 0:
        return []
    duration = n_in / fps_in
    n_out = max(1, int(round(duration * fps_out)))
    return [min(n_in - 1, int(round(i * fps_in / fps_out))) for i in range(n_out)]


def fit_crop(frame: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    """Recorte central na proporção de `size` (sem distorcer)."""
    h, w = frame.shape[:2]
    tw, th = size
    target = tw / th
    if w / h > target:
        cw = int(round(h * target))
        x0 = (w - cw) // 2
        return frame[:, x0:x0 + cw]
    ch = int(round(w / target))
    y0 = (h - ch) // 2
    return frame[y0:y0 + ch]


def downscale(frame: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    """Média de área (BOX) na grade fixa do alvo."""
    image = Image.fromarray(np.ascontiguousarray(fit_crop(frame, size)[..., :3]), "RGB")
    return np.asarray(image.resize(size, Image.BOX), dtype=np.uint8)


def temporal_median(frames: np.ndarray, window: int) -> np.ndarray:
    """Mediana por pixel numa janela de `window` quadros (bordas repetidas)."""
    if window <= 1 or len(frames) < 2:
        return frames
    r = window // 2
    padded = np.concatenate([frames[:1].repeat(r, 0), frames, frames[-1:].repeat(r, 0)])
    stack = np.stack([padded[i:i + len(frames)] for i in range(window)])
    return np.median(stack, axis=0).astype(np.uint8)


def lock_palette(frames: np.ndarray, colors: int) -> np.ndarray:
    """Paleta única para o clipe todo (k-means em amostra de todos os quadros)."""
    step = max(1, len(frames) // 8)
    sample = frames[::step].reshape(-1, 3)
    return kmeans_palette(sample, colors).astype(np.uint8)


def quantize(frames: np.ndarray, palette: np.ndarray, hysteresis: float = HYSTERESIS,
             cleanup: bool = True, initial: np.ndarray | None = None) -> np.ndarray:
    """Quadros RGB → índices da paleta, com histerese entre quadros e limpeza de órfãos.

    `initial`: índices de partida (ex.: o quadro original já em pixel art), para o
    primeiro quadro do clipe começar exatamente igual ao que já estava na tela."""
    pal_lab = srgb_to_oklab(palette.astype(np.float64))
    n, h, w = frames.shape[:3]
    out = np.empty((n, h, w), np.int32)
    prev = initial
    for i in range(n):
        lab = srgb_to_oklab(frames[i].reshape(-1, 3).astype(np.float64))
        dist = np.sqrt(((lab[:, None, :] - pal_lab[None]) ** 2).sum(axis=2))      # (pixels, k)
        best = dist.argmin(axis=1)
        if prev is not None:
            keep = prev.reshape(-1)
            gain = dist[np.arange(len(best)), keep] - dist[np.arange(len(best)), best]
            best = np.where(gain > hysteresis, best, keep)
        idx = best.reshape(h, w)
        if cleanup:
            idx = remove_orphans(idx)
        out[i] = idx
        prev = idx
    return out


def remove_orphans(idx: np.ndarray) -> np.ndarray:
    """Pixel sem nenhum vizinho (4-conexo) igual vira a cor mais comum dos 8 vizinhos."""
    h, w = idx.shape
    padded = np.pad(idx, 1, mode="edge")
    neigh4 = [padded[0:h, 1:w + 1], padded[2:h + 2, 1:w + 1], padded[1:h + 1, 0:w], padded[1:h + 1, 2:w + 2]]
    lonely = np.ones((h, w), bool)
    for n in neigh4:
        lonely &= n != idx
    if not lonely.any():
        return idx
    neigh8 = neigh4 + [padded[0:h, 0:w], padded[0:h, 2:w + 2], padded[2:h + 2, 0:w], padded[2:h + 2, 2:w + 2]]
    stack = np.stack(neigh8, axis=-1)[lonely]                      # (m, 8)
    out = idx.copy()
    majority = np.array([np.bincount(row).argmax() for row in stack])
    out[lonely] = majority
    return out


def key_alpha(frames: np.ndarray, key: tuple[int, int, int], distance: float = KEY_DISTANCE) -> np.ndarray:
    """Máscara opaca (n, h, w): pixels longe da cor de fundo `key`, com mediana temporal."""
    lab = srgb_to_oklab(frames.reshape(-1, 3).astype(np.float64))
    k = srgb_to_oklab(np.array([key], np.float64))[0]
    opaque = (np.sqrt(((lab - k) ** 2).sum(axis=1)) > distance).reshape(frames.shape[:3])
    if len(opaque) >= 3:
        opaque = temporal_median(opaque.astype(np.uint8)[..., None] * 255, 3)[..., 0] > 127
    return opaque


def pixelize_clip(frames: list[np.ndarray] | np.ndarray, options: PixelizeOptions,
                  base: np.ndarray | None = None, region: np.ndarray | None = None) -> list[np.ndarray]:
    """Clipe (lista de RGB de qualquer tamanho) → quadros nativos RGB (ou RGBA com `key`).

    `base`: o quadro original em pixel art (RGB nativo); com ele a histerese parte das
    cores originais e, com `region` (máscara bool nativa), só a região muda."""
    picks = resample_times(len(frames), options.fps_in, options.fps_out)
    small = np.stack([downscale(np.asarray(frames[i]), options.size) for i in picks])
    small = temporal_median(small, options.median)
    palette = options.palette if options.palette is not None else lock_palette(small, options.colors)
    palette = np.asarray(palette, np.uint8)[:, :3]
    initial = None
    if base is not None:
        initial = quantize(base[None, ..., :3], palette, hysteresis=0.0, cleanup=False)[0]
    idx = quantize(small, palette, options.hysteresis, options.cleanup, initial)
    rgb = palette[idx]
    if base is not None:
        keep = np.zeros(idx.shape, bool) if options.motion is None else ~moving(small, options.motion, base)
        if region is not None:
            keep |= ~region[None]
        rgb = np.where(keep[..., None], base[None, ..., :3], rgb)
    if options.key is None:
        return list(rgb)
    alpha = key_alpha(small, options.key, options.key_distance)
    return [np.dstack([f, a.astype(np.uint8) * 255]) for f, a in zip(rgb, alpha)]


def moving(frames: np.ndarray, threshold: float = MOTION, base: np.ndarray | None = None) -> np.ndarray:
    """Máscara (n, h, w) do que mudou: distância Oklab > `threshold` contra o 1º quadro do clipe
    E (com `base`) contra a média 3×3 do original — onde a nuvem já passou e o céu voltou a ser
    o de antes, o pixel (dithering incluído) volta a ser o original. Mediana temporal (some o
    pisca de 1 quadro) e 1 px de folga em volta."""
    lab = srgb_to_oklab(frames.reshape(-1, 3).astype(np.float64)).reshape(frames.shape)
    diff = np.sqrt(((lab - lab[:1]) ** 2).sum(axis=-1)) > threshold
    if base is not None:
        b = srgb_to_oklab(base[..., :3].reshape(-1, 3).astype(np.float64)).reshape(base.shape[:2] + (3,))
        pad = np.pad(b, ((1, 1), (1, 1), (0, 0)), mode="edge")
        h, w = b.shape[:2]
        local = sum(pad[y:y + h, x:x + w] for y in range(3) for x in range(3)) / 9
        diff &= np.sqrt(((lab - local[None]) ** 2).sum(axis=-1)) > threshold
    if len(diff) >= 3:
        diff = temporal_median(diff.astype(np.uint8)[..., None] * 255, 3)[..., 0] > 127
    grown = diff.copy()
    grown[:, 1:] |= diff[:, :-1]
    grown[:, :-1] |= diff[:, 1:]
    grown[:, :, 1:] |= diff[:, :, :-1]
    grown[:, :, :-1] |= diff[:, :, 1:]
    return grown


def palette_of(image: np.ndarray, max_colors: int = 48) -> np.ndarray:
    """Paleta de uma arte já em pixel art: cores opacas únicas (ou k-means se forem muitas)."""
    rgba = image if image.shape[-1] == 4 else np.dstack([image, np.full(image.shape[:2], 255, np.uint8)])
    opaque = rgba[..., 3] > 127
    colors = np.unique(rgba[opaque][:, :3], axis=0)
    if len(colors) <= max_colors:
        return colors.astype(np.uint8)
    return kmeans_palette(rgba[opaque][:, :3], max_colors).astype(np.uint8)


def flicker(frames: list[np.ndarray]) -> float:
    """Fração média de pixels que mudam entre quadros consecutivos (0 = parado)."""
    if len(frames) < 2:
        return 0.0
    stack = np.stack([f[..., :3] for f in frames])
    return float((stack[1:] != stack[:-1]).any(axis=-1).mean())
