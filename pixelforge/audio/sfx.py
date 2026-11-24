"""Efeitos chiptune procedurais (estilo sfxr), só numpy e determinísticos.

Um efeito é uma ou mais **camadas** somadas; cada camada é um oscilador com
envelope ADSR, deslize de frequência, vibrato, arpejo, duty e filtros. As chaves
do JSON são em português (acentos opcionais):

    {"onda": "quadrada", "freq": 300, "deslize": 2.5, "ataque": 0, "decaimento": 0.05,
     "sustentacao": 0.6, "manter": 0.1, "soltura": 0.1, "volume": 0.6}

ou {"camadas": [{...}, {..., "atraso": 0.3}]}. Mesma entrada + mesma semente =
mesmas amostras.
"""

from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, field, fields, replace
from pathlib import Path

import numpy as np

from .wavio import DEFAULT_RATE

WAVES = {
    "quadrada": "square", "square": "square",
    "triangulo": "triangle", "triangle": "triangle",
    "serra": "saw", "saw": "saw",
    "seno": "sine", "sine": "sine",
    "ruido": "noise", "noise": "noise",
}


def plain(text: str) -> str:
    """Minúsculas sem acentos: "Explosão" → "explosao"."""
    norm = unicodedata.normalize("NFKD", str(text).strip().lower())
    return "".join(c for c in norm if not unicodedata.combining(c))


@dataclass
class Layer:
    """Uma voz do efeito. Tempos em segundos, frequências em Hz."""

    onda: str = "quadrada"
    freq: float = 440.0
    deslize: float = 0.0          # oitavas por segundo (negativo = desce)
    deslize_acel: float = 0.0     # oitavas por segundo²
    freq_min: float = 20.0
    duty: float = 0.5             # fração alta da onda quadrada
    duty_varre: float = 0.0       # variação do duty por segundo
    ataque: float = 0.0
    decaimento: float = 0.1
    sustentacao: float = 0.0      # nível (0–1) depois do decaimento
    manter: float = 0.0           # tempo no nível de sustentação
    soltura: float = 0.0
    curva: float = 1.0            # expoente do envelope (>1 = queda mais natural)
    vibrato: float = 0.0          # profundidade em semitons
    vibrato_vel: float = 6.0      # Hz
    arpejo: list = field(default_factory=list)   # semitons, ex.: [0, 4, 7]
    arpejo_passo: float = 0.05    # segundos por nota do arpejo
    arpejo_ciclo: bool = True     # False = para na última nota
    harmonicos: list = field(default_factory=list)  # [[razão, ganho], ...]
    passa_baixa: float = 0.0      # Hz (0 = desligado)
    passa_alta: float = 0.0
    bits: int = 0                 # redução de bits (0 = desligado)
    volume: float = 0.5
    atraso: float = 0.0           # início da camada dentro do efeito

    @property
    def duration(self) -> float:
        return self.atraso + self.ataque + self.decaimento + self.manter + self.soltura

    @classmethod
    def from_dict(cls, data: dict) -> "Layer":
        names = {f.name for f in fields(cls)}
        values = {}
        for key, value in data.items():
            key = plain(key)
            if key not in names:
                raise ValueError(f"parâmetro de efeito desconhecido: '{key}'. Válidos: {', '.join(sorted(names))}")
            values[key] = value
        layer = cls(**values)
        if plain(layer.onda) not in WAVES:
            raise ValueError(f"onda '{layer.onda}' inválida. Use: quadrada, triangulo, serra, seno, ruido")
        return layer


@dataclass
class Effect:
    name: str
    layers: list[Layer]

    @property
    def duration(self) -> float:
        return max(layer.duration for layer in self.layers)

    def to_dict(self) -> dict:
        def clean(layer: Layer) -> dict:
            base = Layer()
            return {f.name: getattr(layer, f.name) for f in fields(Layer)
                    if getattr(layer, f.name) != getattr(base, f.name) or f.name in ("onda", "freq")}
        return {"name": self.name, "camadas": [clean(layer) for layer in self.layers]}


# --------------------------------------------------------------------------
# presets
# --------------------------------------------------------------------------

PRESETS: dict[str, list[dict]] = {
    "passo": [
        {"onda": "ruido", "freq": 2200, "deslize": -4, "decaimento": 0.06, "passa_baixa": 1800, "curva": 2, "volume": 0.6},
        {"onda": "triangulo", "freq": 140, "deslize": -2, "decaimento": 0.05, "curva": 2, "volume": 0.5},
    ],
    "pulo": [
        {"onda": "quadrada", "freq": 260, "deslize": 3.0, "duty": 0.5, "decaimento": 0.04, "sustentacao": 0.7,
         "manter": 0.08, "soltura": 0.12, "volume": 0.45},
    ],
    "moeda": [
        {"onda": "quadrada", "freq": 987.77, "duty": 0.5, "arpejo": [0, 5], "arpejo_passo": 0.07,
         "arpejo_ciclo": False, "decaimento": 0.02, "sustentacao": 0.8, "manter": 0.12, "soltura": 0.3,
         "curva": 1.5, "volume": 0.4},
    ],
    "magia": [
        {"onda": "triangulo", "freq": 523.25, "deslize": 0.6, "arpejo": [0, 4, 7, 12], "arpejo_passo": 0.045,
         "vibrato": 0.3, "vibrato_vel": 9, "ataque": 0.02, "decaimento": 0.1, "sustentacao": 0.7, "manter": 0.35,
         "soltura": 0.45, "harmonicos": [[1, 1], [2, 0.35], [3, 0.15]], "volume": 0.5},
        {"onda": "ruido", "freq": 9000, "passa_alta": 5000, "ataque": 0.1, "decaimento": 0.2, "sustentacao": 0.4,
         "manter": 0.25, "soltura": 0.4, "volume": 0.12},
    ],
    "golpe": [
        {"onda": "ruido", "freq": 1600, "deslize": -5, "decaimento": 0.14, "curva": 2, "passa_baixa": 4000, "volume": 0.8},
        {"onda": "quadrada", "freq": 220, "deslize": -7, "duty": 0.3, "decaimento": 0.09, "curva": 1.5, "volume": 0.5},
    ],
    "porta": [
        {"onda": "serra", "freq": 95, "deslize": 0.4, "vibrato": 2.5, "vibrato_vel": 11, "ataque": 0.05,
         "decaimento": 0.1, "sustentacao": 0.6, "manter": 0.3, "soltura": 0.1, "passa_baixa": 1400, "volume": 0.35},
        {"onda": "ruido", "freq": 500, "deslize": -1, "atraso": 0.55, "decaimento": 0.25, "curva": 2,
         "passa_baixa": 500, "volume": 0.9},
        {"onda": "seno", "freq": 75, "deslize": -1, "atraso": 0.55, "decaimento": 0.3, "curva": 1.5, "volume": 0.7},
    ],
    "explosao": [
        {"onda": "ruido", "freq": 700, "deslize": -1.2, "ataque": 0.005, "decaimento": 0.25, "sustentacao": 0.35,
         "manter": 0.15, "soltura": 0.9, "curva": 2, "passa_baixa": 3500, "volume": 0.9},
        {"onda": "seno", "freq": 70, "deslize": -1.5, "decaimento": 0.6, "curva": 1.5, "volume": 0.7},
    ],
    "menu": [
        {"onda": "quadrada", "freq": 1318.5, "duty": 0.25, "decaimento": 0.06, "curva": 1.5, "volume": 0.35},
    ],
    "dano": [
        {"onda": "serra", "freq": 520, "deslize": -3.5, "vibrato": 1.5, "vibrato_vel": 28, "decaimento": 0.05,
         "sustentacao": 0.6, "manter": 0.08, "soltura": 0.15, "passa_baixa": 5000, "volume": 0.45},
        {"onda": "ruido", "freq": 3000, "deslize": -3, "decaimento": 0.12, "curva": 2, "volume": 0.3},
    ],
    "sino": [
        {"onda": "seno", "freq": 880, "ataque": 0.002, "decaimento": 1.8, "curva": 2.5,
         "harmonicos": [[1, 1], [2.76, 0.45], [5.4, 0.25], [8.93, 0.12]], "volume": 0.55},
    ],
}


def preset_names() -> list[str]:
    return sorted(PRESETS)


def load_effect(source: str | Path | dict, name: str | None = None) -> Effect:
    """Preset pelo nome, arquivo .json ou dicionário já carregado."""
    if isinstance(source, dict):
        data = source
    else:
        key = plain(str(source))
        if key in PRESETS:
            return Effect(key, [Layer.from_dict(d) for d in PRESETS[key]])
        path = Path(source)
        if path.suffix.lower() != ".json":
            raise KeyError(f"efeito '{source}' não existe. Presets: {', '.join(preset_names())} (ou um arquivo .json)")
        if not path.is_file():
            raise FileNotFoundError(f"arquivo não encontrado: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        name = name or data.get("name") or path.stem
    if "base" in data:   # {"base": "pulo", "camadas": [{"freq": 400}]} ajusta um preset
        base = load_effect(data["base"])
        patches = data.get("camadas", [])
        layers = [replace(layer, **{plain(k): v for k, v in (patches[i] if i < len(patches) else {}).items()})
                  for i, layer in enumerate(base.layers)]
        return Effect(name or data.get("name") or base.name, layers)
    raw_layers = data.get("camadas", [data])
    layer_data = [{k: v for k, v in d.items() if k != "name"} for d in raw_layers]
    if not layer_data:
        raise ValueError("efeito sem camadas")
    return Effect(name or data.get("name") or "efeito", [Layer.from_dict(d) for d in layer_data])


def vary(effect: Effect, amount: float, seed: int) -> Effect:
    """Variação aleatória (±amount relativo) dos parâmetros numéricos — como o "mutate" do sfxr."""
    if amount <= 0:
        return effect
    rng = np.random.default_rng(seed + 7919)
    tweak = ("freq", "deslize", "decaimento", "manter", "soltura", "duty", "vibrato", "passa_baixa", "volume")
    layers = []
    for layer in effect.layers:
        changes = {}
        for key in tweak:
            value = getattr(layer, key)
            if value:
                changes[key] = value * (1 + rng.uniform(-amount, amount))
        changes["duty"] = float(np.clip(changes.get("duty", layer.duty), 0.05, 0.95))
        layers.append(replace(layer, **changes))
    return Effect(effect.name, layers)


# --------------------------------------------------------------------------
# síntese
# --------------------------------------------------------------------------


def envelope(layer: Layer, n: int, rate: int) -> np.ndarray:
    points = [(0.0, 0.0), (layer.ataque, 1.0), (layer.ataque + layer.decaimento, layer.sustentacao),
              (layer.ataque + layer.decaimento + layer.manter, layer.sustentacao),
              (layer.ataque + layer.decaimento + layer.manter + layer.soltura, 0.0)]
    if layer.ataque <= 0:
        points[0] = (0.0, 1.0)
    times, values = zip(*points)
    env = np.interp(np.arange(n) / rate, np.array(times) + np.arange(5) * 1e-9, values)
    return env ** layer.curva if layer.curva != 1 else env


def frequency_curve(layer: Layer, t: np.ndarray) -> np.ndarray:
    octaves = layer.deslize * t + 0.5 * layer.deslize_acel * t * t
    semis = np.zeros_like(t)
    if layer.vibrato:
        semis += layer.vibrato * np.sin(2 * np.pi * layer.vibrato_vel * t)
    if layer.arpejo:
        steps = (t / max(layer.arpejo_passo, 1e-4)).astype(np.int64)
        steps = steps % len(layer.arpejo) if layer.arpejo_ciclo else np.minimum(steps, len(layer.arpejo) - 1)
        semis += np.asarray(layer.arpejo, dtype=np.float64)[steps]
    freq = layer.freq * np.exp2(octaves + semis / 12.0)
    return np.clip(freq, layer.freq_min, 20000.0)


def oscillator(wave: str, phase: np.ndarray, duty: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    frac = phase % 1.0
    if wave == "square":
        return np.where(frac < duty, 1.0, -1.0)
    if wave == "triangle":
        return 4.0 * np.abs(frac - 0.5) - 1.0
    if wave == "saw":
        return 2.0 * frac - 1.0
    if wave == "sine":
        return np.sin(2 * np.pi * phase)
    # ruído: um valor novo a cada meio período (sample-and-hold), como o sfxr
    index = np.floor(phase * 2).astype(np.int64)
    values = rng.uniform(-1.0, 1.0, int(index[-1]) + 2 if len(index) else 1)
    return values[index]


def spectral_filter(signal: np.ndarray, rate: int, low: float, high: float) -> np.ndarray:
    """Passa-baixa/alta de 2ª ordem (só magnitude, fase zero) via FFT."""
    if not (low or high) or len(signal) < 4:
        return signal
    spectrum = np.fft.rfft(signal)
    f = np.fft.rfftfreq(len(signal), 1.0 / rate)
    gain = np.ones_like(f)
    if low:
        gain /= np.sqrt(1 + (f / low) ** 4)
    if high:
        gain *= (f / high) ** 2 / np.sqrt(1 + (f / high) ** 4)
    return np.fft.irfft(spectrum * gain, len(signal))


def render_layer(layer: Layer, rate: int, rng: np.random.Generator) -> np.ndarray:
    body = layer.duration - layer.atraso
    n = max(1, int(round(body * rate)))
    t = np.arange(n) / rate
    freq = frequency_curve(layer, t)
    phase = np.cumsum(freq / rate)
    duty = np.clip(layer.duty + layer.duty_varre * t, 0.02, 0.98)
    wave = WAVES[plain(layer.onda)]
    partials = layer.harmonicos or [[1, 1]]
    total_gain = sum(abs(g) for _, g in partials) or 1.0
    signal = sum(g * oscillator(wave, phase * r, duty, rng) for r, g in partials) / total_gain
    signal = spectral_filter(signal, rate, layer.passa_baixa, layer.passa_alta)
    signal = signal * envelope(layer, n, rate) * layer.volume
    if layer.bits:
        steps = 2 ** (int(layer.bits) - 1)
        signal = np.round(signal * steps) / steps
    pad = int(round(layer.atraso * rate))
    return np.concatenate([np.zeros(pad), signal])


def synth(effect: Effect, seed: int = 0, rate: int = DEFAULT_RATE) -> np.ndarray:
    """Amostras mono float32. Pico limitado a 0,98 (sem clipping)."""
    rng = np.random.default_rng(seed)
    parts = [render_layer(layer, rate, rng) for layer in effect.layers]
    out = np.zeros(max(len(p) for p in parts))
    for part in parts:
        out[: len(part)] += part
    peak = float(np.max(np.abs(out))) if out.size else 0.0
    if peak > 0.98:
        out *= 0.98 / peak
    return out.astype(np.float32)
