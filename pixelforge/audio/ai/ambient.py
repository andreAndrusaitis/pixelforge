"""Ambientes e efeitos por descrição (texto → áudio), via diffusers.

- `audioldm2` (padrão): cvssp/audioldm2, aberto (sem login), 16 kHz mono, cabe em 8 GB.
- `stable-audio`: stabilityai/stable-audio-open-1.0, 44,1 kHz estéreo; o repositório é
  restrito (gated): aceite a licença em huggingface.co e faça `hf auth login` antes.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .common import BackendError, device, models_dir, require, use_hf_cache

MODELS = {
    "audioldm2": "cvssp/audioldm2",
    "stable-audio": "stabilityai/stable-audio-open-1.0",
}
DEFAULT_MODEL = "audioldm2"
NEGATIVE = "low quality, distorted, noise, music, speech"

_pipes: dict = {}


def _load(model: str, models: Path | None, dev: str):
    key = (model, str(models), dev)
    if key in _pipes:
        return _pipes[key]
    use_hf_cache(models_dir(models))
    torch = require("torch", "ambiente por IA")
    diffusers = require("diffusers", "ambiente por IA")
    cls = diffusers.AudioLDM2Pipeline if model == "audioldm2" else diffusers.StableAudioPipeline
    dtype = torch.float16 if dev == "cuda" else torch.float32
    try:
        pipe = cls.from_pretrained(MODELS[model], torch_dtype=dtype)
    except Exception as exc:
        text = str(exc)
        if model == "stable-audio" and ("gated" in text.lower() or "401" in text or "403" in text):
            raise BackendError("Stable Audio Open é restrito: aceite a licença em "
                               "https://huggingface.co/stabilityai/stable-audio-open-1.0 e rode `hf auth login`; "
                               "ou use --modelo audioldm2 (aberto)") from None
        raise BackendError(f"não consegui carregar {MODELS[model]}: {text[:300]}") from exc
    if model == "audioldm2":
        _patch_gpt2(pipe.language_model)
    if dev == "cuda":
        pipe.enable_model_cpu_offload()     # cabe folgado em 8 GB
    else:
        pipe = pipe.to(dev)
    _pipes[key] = pipe
    return pipe


def _patch_gpt2(language_model) -> None:
    """transformers 5 tirou os métodos de geração do GPT2Model, que o AudioLDM2 do
    diffusers ainda chama; devolve-os misturando o GenerationMixin na instância."""
    if hasattr(language_model, "_update_model_kwargs_for_generation"):
        return
    from transformers import GenerationMixin
    base = type(language_model)

    def forward(self, *args, **kwargs):
        out = base.forward(self, *args, **kwargs)
        if getattr(out, "hidden_states", None) is None:   # o pipeline lê hidden_states[-1]
            out.hidden_states = (out.last_hidden_state,)
        return out

    language_model.__class__ = type(base.__name__ + "WithGeneration", (base, GenerationMixin), {"forward": forward})


def generate(prompt: str, seconds: float = 8.0, model: str = DEFAULT_MODEL, seed: int = 0, steps: int | None = None,
             models: Path | None = None, dev: str | None = None) -> tuple[np.ndarray, int]:
    """Descrição (de preferência em inglês) → (amostras float32, taxa)."""
    if model not in MODELS:
        raise ValueError(f"modelo '{model}' inválido. Use: {', '.join(MODELS)}")
    dev = device(dev)
    torch = require("torch", "ambiente por IA")
    pipe = _load(model, models, dev)
    generator = torch.Generator("cpu").manual_seed(int(seed))
    if model == "audioldm2":
        out = pipe(prompt, negative_prompt=NEGATIVE, num_inference_steps=steps or 100,
                   audio_length_in_s=float(seconds), num_waveforms_per_prompt=1, generator=generator)
        audio, rate = np.asarray(out.audios[0], dtype=np.float32), 16000
    else:
        out = pipe(prompt, negative_prompt=NEGATIVE, num_inference_steps=steps or 100,
                   audio_end_in_s=float(min(seconds, 47.0)), num_waveforms_per_prompt=1, generator=generator)
        audio = out.audios[0].float().cpu().numpy().T.astype(np.float32)   # (n, 2)
        rate = pipe.vae.sampling_rate
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 0:
        audio = audio * (0.89 / peak)      # normaliza em -1 dBFS
    return audio, rate
