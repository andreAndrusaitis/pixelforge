"""Som do PixelForge: efeitos chiptune, música por sequenciador, mixagem e (opcional) IA local.

O núcleo (`sfx`, `music`, `mix`, `wavio`) só usa stdlib + numpy. Os backends de IA
ficam em `pixelforge.audio.ai` e só são importados quando usados (extra `[audio-ia]`).
"""

from .mix import Clip, mix_clips, mux_video, render_plan
from .music import load_song, render_song
from .sfx import PRESETS, Effect, Layer, load_effect, synth, vary
from .wavio import DEFAULT_RATE, levels, read_wav, write_wav

__all__ = ["Clip", "mix_clips", "mux_video", "render_plan", "load_song", "render_song", "PRESETS", "Effect",
           "Layer", "load_effect", "synth", "vary", "DEFAULT_RATE", "levels", "read_wav", "write_wav"]
