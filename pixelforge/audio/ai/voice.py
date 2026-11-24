"""Voz com Kokoro TTS (hexgrad/Kokoro-82M, Apache-2.0), português do Brasil."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .common import BackendError, device, models_dir, require, use_hf_cache

RATE = 24000
VOICES = {"pf_dora": "feminina", "pm_alex": "masculina", "pm_santa": "masculina (grave)"}
DEFAULT_VOICE = "pf_dora"
REPO = "hexgrad/Kokoro-82M"

_pipelines: dict = {}


def _pipeline(models: Path | None, dev: str | None):
    key = (str(models), dev)
    if key not in _pipelines:
        use_hf_cache(models_dir(models))
        kokoro = require("kokoro", "voz (Kokoro)")
        try:
            _pipelines[key] = kokoro.KPipeline(lang_code="p", repo_id=REPO, device=device(dev))
        except Exception as exc:  # espeak-ng ausente, download falhou…
            raise BackendError(f"não consegui iniciar o Kokoro: {exc}") from exc
    return _pipelines[key]


def speak(text: str, voice: str | None = None, speed: float = 1.0, models: Path | None = None,
          dev: str | None = None) -> tuple[np.ndarray, int]:
    """Texto → (amostras mono float32, 24000). Frases longas são divididas pelo próprio Kokoro."""
    voice = voice or DEFAULT_VOICE
    if voice not in VOICES:
        raise ValueError(f"voz '{voice}' inválida. Vozes em português: {', '.join(VOICES)}")
    if not text.strip():
        raise ValueError("texto vazio")
    pipeline = _pipeline(models, dev)
    chunks = []
    for result in pipeline(text, voice=voice, speed=speed):
        audio = result[2] if isinstance(result, tuple) else result.audio
        if audio is not None:
            chunks.append(np.asarray(audio.detach().cpu() if hasattr(audio, "detach") else audio, dtype=np.float32))
            chunks.append(np.zeros(int(0.12 * RATE), dtype=np.float32))   # respiro entre trechos
    if not chunks:
        raise BackendError("o Kokoro não devolveu áudio")
    return np.concatenate(chunks[:-1]), RATE
