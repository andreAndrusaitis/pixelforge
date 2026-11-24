"""Música chiptune por código: sequenciador de canais com notas em texto.

    {
      "name": "tema",
      "bpm": 120,
      "loop": 2,
      "canais": [
        {"onda": "quadrada", "duty": 0.25, "volume": 0.3, "dur": 0.5,
         "notas": "E5 G5 A5:1 . | C6 B5 A5 G5:2"},
        {"onda": "triangulo", "volume": 0.4, "notas": "A2:2 F2:2 | C3:2 G2:2"},
        {"bateria": true, "volume": 0.5, "dur": 0.5, "notas": "k h s h k k s h"}
      ]
    }

Tokens (durações em tempos/beats; sem `:n` vale o `dur` do canal, padrão 1):
`C4`, `F#3`, `Bb5:0.5` nota · `.` ou `R` pausa · `-` estende a nota anterior ·
`|` separador visual. Na bateria: `k` bumbo, `s` caixa, `h` chimbal, `x` batida.
Os demais campos do canal são parâmetros de camada do `sfx` (envelope, vibrato…).
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path

import numpy as np

from .sfx import Layer, plain, render_layer
from .wavio import DEFAULT_RATE

NOTE_INDEX = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}
NOTE_RE = re.compile(r"^([A-Ga-g])([#b]?)(-?\d)$")

DRUMS = {
    "k": {"onda": "seno", "freq": 150, "deslize": -5, "decaimento": 0.18, "curva": 1.5, "volume": 1.0},
    "s": {"onda": "ruido", "freq": 6000, "decaimento": 0.14, "curva": 2, "passa_alta": 900, "volume": 0.7},
    "h": {"onda": "ruido", "freq": 12000, "decaimento": 0.04, "curva": 2, "passa_alta": 6000, "volume": 0.35},
    "x": {"onda": "ruido", "freq": 3000, "deslize": -2, "decaimento": 0.1, "curva": 2, "volume": 0.7},
}

CHANNEL_KEYS = {"notas", "dur", "bateria", "nome", "oitava"}
INSTRUMENT_DEFAULTS = {"ataque": 0.005, "decaimento": 0.08, "sustentacao": 0.7, "soltura": 0.06}


def note_freq(name: str) -> float:
    """"A4" → 440.0; aceita sustenido (#) e bemol (b)."""
    match = NOTE_RE.match(name)
    if not match:
        raise ValueError(f"nota inválida: '{name}' (use ex.: C4, F#3, Bb5)")
    letter, accidental, octave = match.groups()
    semis = NOTE_INDEX[letter.lower()] + {"#": 1, "b": -1, "": 0}[accidental]
    midi = 12 * (int(octave) + 1) + semis
    return 440.0 * 2 ** ((midi - 69) / 12)


def parse_notes(text: str, default_beats: float = 1.0) -> list[tuple[str | None, float]]:
    """Texto → lista de (token, tempos). Token None = pausa."""
    events: list[list] = []
    for raw in text.replace(",", " ").split():
        if raw == "|":
            continue
        token, _, beats = raw.partition(":")
        try:
            length = float(beats) if beats else default_beats
        except ValueError:
            raise ValueError(f"duração inválida em '{raw}'") from None
        if length <= 0:
            raise ValueError(f"duração deve ser positiva em '{raw}'")
        if token == "-":
            if not events:
                raise ValueError("'-' precisa de uma nota antes")
            events[-1][1] += length
        elif token in (".", "R", "r"):
            events.append([None, length])
        else:
            events.append([token, length])
    return [(t, b) for t, b in events]


def load_song(source: str | Path | dict) -> dict:
    if isinstance(source, dict):
        return source
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"arquivo não encontrado: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("name", path.stem)
    return data


def _instrument(channel: dict) -> Layer:
    params = {**INSTRUMENT_DEFAULTS, **{plain(k): v for k, v in channel.items() if plain(k) not in CHANNEL_KEYS}}
    return Layer.from_dict(params)


def render_channel(channel: dict, bpm: float, rate: int, seed: int) -> np.ndarray:
    beat = 60.0 / bpm
    drums = bool(channel.get("bateria"))
    events = parse_notes(str(channel.get("notas", "")), float(channel.get("dur", 1.0)))
    total = sum(b for _, b in events) * beat
    out = np.zeros(int(round(total * rate)) + rate * 2)
    rng = np.random.default_rng(seed)
    base = None if drums else _instrument(channel)
    volume = float(channel.get("volume", 0.5))
    cursor = 0.0
    for token, beats in events:
        length = beats * beat
        if token is not None:
            if drums:
                key = token.lower()
                if key not in DRUMS:
                    raise ValueError(f"batida desconhecida: '{token}' (use k, s, h, x)")
                layer = Layer.from_dict(DRUMS[key])
                layer = replace(layer, volume=layer.volume * volume)
            else:
                hold = max(0.0, length - base.ataque - base.decaimento - base.soltura * 0.5)
                layer = replace(base, freq=note_freq(token), manter=hold, atraso=0.0)
            part = render_layer(layer, rate, rng)
            start = int(round(cursor * rate))
            end = min(len(out), start + len(part))
            out[start:end] += part[: end - start]
        cursor += length
    return out[: int(round(total * rate))]


def render_song(song: dict, rate: int = DEFAULT_RATE, seed: int = 0) -> np.ndarray:
    """Mono float32; `loop` repete a música inteira n vezes."""
    bpm = float(song.get("bpm", 120))
    if bpm <= 0:
        raise ValueError("bpm deve ser positivo")
    channels = song.get("canais") or []
    if not channels:
        raise ValueError("música sem canais")
    parts = [render_channel(ch, bpm, rate, seed + i) for i, ch in enumerate(channels)]
    mix = np.zeros(max(len(p) for p in parts))
    for part in parts:
        mix[: len(part)] += part
    mix = np.tile(mix, max(1, int(song.get("loop", 1))))
    peak = float(np.max(np.abs(mix))) if mix.size else 0.0
    if peak > 0.95:
        mix *= 0.95 / peak
    return mix.astype(np.float32)

