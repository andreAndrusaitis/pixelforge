"""WAV com a stdlib (`wave`): leitura/gravação PCM, reamostragem e medidas de nível.

Convenção interna: áudio é `np.ndarray` float32 em [-1, 1], formato (n,) para mono
ou (n, canais) para estéreo.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

DEFAULT_RATE = 44100


def as_2d(samples: np.ndarray) -> np.ndarray:
    """(n,) → (n, 1); (n, c) inalterado."""
    samples = np.asarray(samples, dtype=np.float32)
    return samples[:, None] if samples.ndim == 1 else samples


def write_wav(path: Path | str, samples: np.ndarray, rate: int = DEFAULT_RATE) -> Path:
    """Grava PCM 16 bits. Valores fora de [-1, 1] são cortados."""
    path = Path(path)
    data = as_2d(samples)
    if data.ndim != 2 or data.shape[1] not in (1, 2):
        raise ValueError(f"áudio deve ser mono ou estéreo, não {data.shape}")
    pcm = (np.clip(data, -1.0, 1.0) * 32767.0).round().astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as out:
        out.setnchannels(data.shape[1])
        out.setsampwidth(2)
        out.setframerate(int(rate))
        out.writeframes(pcm.tobytes())
    return path


def read_wav(path: Path | str) -> tuple[np.ndarray, int]:
    """Lê PCM 8/16/24/32 bits; devolve (amostras float32 (n, canais), taxa)."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"áudio não encontrado: {path}")
    try:
        with wave.open(str(path), "rb") as src:
            channels, width, rate = src.getnchannels(), src.getsampwidth(), src.getframerate()
            raw = src.readframes(src.getnframes())
    except wave.Error as exc:
        if "unknown format: 3" in str(exc):          # IEEE float (ACE-Step, soundfile)
            return _read_float_wav(path)
        raise ValueError(f"{path}: WAV não suportado ({exc})") from None
    if width == 1:
        data = (np.frombuffer(raw, np.uint8).astype(np.float32) - 128.0) / 128.0
    elif width == 2:
        data = np.frombuffer(raw, "<i2").astype(np.float32) / 32768.0
    elif width == 3:
        b = np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(np.int32)
        ints = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        ints = np.where(ints & 0x800000, ints - (1 << 24), ints)
        data = ints.astype(np.float32) / float(1 << 23)
    elif width == 4:
        data = np.frombuffer(raw, "<i4").astype(np.float32) / float(1 << 31)
    else:
        raise ValueError(f"{path}: {width * 8} bits por amostra não suportado")
    return data.reshape(-1, channels), rate


def _read_float_wav(path: Path) -> tuple[np.ndarray, int]:
    """WAV IEEE float 32/64 bits (o módulo `wave` só lê PCM inteiro)."""
    raw = path.read_bytes()
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError(f"{path}: não é um WAV")
    pos, fmt, data = 12, None, None
    while pos + 8 <= len(raw):
        cid, size = raw[pos:pos + 4], int.from_bytes(raw[pos + 4:pos + 8], "little")
        body = raw[pos + 8:pos + 8 + size]
        if cid == b"fmt ":
            fmt = body
        elif cid == b"data":
            data = body
        pos += 8 + size + (size & 1)
    if fmt is None or data is None:
        raise ValueError(f"{path}: WAV sem blocos fmt/data")
    channels = int.from_bytes(fmt[2:4], "little")
    rate = int.from_bytes(fmt[4:8], "little")
    bits = int.from_bytes(fmt[14:16], "little")
    if bits not in (32, 64):
        raise ValueError(f"{path}: float de {bits} bits não suportado")
    samples = np.frombuffer(data[: len(data) - len(data) % (bits // 8 * channels)], "<f4" if bits == 32 else "<f8")
    return samples.astype(np.float32).reshape(-1, channels), rate


def resample(samples: np.ndarray, rate_from: int, rate_to: int) -> np.ndarray:
    """Reamostragem linear (suficiente para mixagem; preserva o formato mono/estéreo)."""
    if rate_from == rate_to or len(samples) == 0:
        return np.asarray(samples, dtype=np.float32)
    data = as_2d(samples)
    n_out = max(1, round(len(data) * rate_to / rate_from))
    x_old = np.arange(len(data), dtype=np.float64)
    x_new = np.arange(n_out, dtype=np.float64) * (rate_from / rate_to)
    out = np.stack([np.interp(x_new, x_old, data[:, c]) for c in range(data.shape[1])], axis=1)
    out = out.astype(np.float32)
    return out[:, 0] if np.ndim(samples) == 1 else out


def to_channels(samples: np.ndarray, channels: int) -> np.ndarray:
    data = as_2d(samples)
    if data.shape[1] == channels:
        return data
    if channels == 1:
        return data.mean(axis=1, keepdims=True)
    return np.repeat(data[:, :1], channels, axis=1) if data.shape[1] == 1 else data[:, :channels]


def levels(samples: np.ndarray) -> dict:
    """Pico e RMS em dBFS (para conferir o nível)."""
    data = np.asarray(samples, dtype=np.float64)
    peak = float(np.max(np.abs(data))) if data.size else 0.0
    rms = float(np.sqrt(np.mean(data ** 2))) if data.size else 0.0
    db = lambda v: round(float(20 * np.log10(v)), 1) if v > 0 else float("-inf")  # noqa: E731
    return {"peak": peak, "peak_db": db(peak), "rms_db": db(rms)}


def describe(path: Path | str) -> str:
    data, rate = read_wav(path)
    lv = levels(data)
    kind = "mono" if data.shape[1] == 1 else "estéreo"
    return f"{len(data) / rate:.2f} s, {rate} Hz {kind}, pico {lv['peak_db']} dBFS, RMS {lv['rms_db']} dBFS"
