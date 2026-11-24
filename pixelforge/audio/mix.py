"""Mixagem: trilha + efeitos em instantes + falas → uma faixa estéreo; junção ao MP4.

API para o motor de cena (etapa 5):

    from pixelforge.audio.mix import render_plan, mux_video
    samples, rate = render_plan(plano, base_dir=Path("."))      # plano = dict do roteiro de áudio
    write_wav("out/cena/cena.wav", samples, rate)
    mux_video("out/cena/cena.mp4", "out/cena/cena.wav", "out/cena/cena_som.mp4")

ou, com amostras já prontas, `mix_clips([Clip(...), ...], duracao)`.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import music, sfx
from .wavio import DEFAULT_RATE, as_2d, read_wav, resample, to_channels, write_wav


@dataclass
class Clip:
    """Um som posicionado na faixa. Tempos em segundos."""

    samples: np.ndarray
    rate: int = DEFAULT_RATE
    start: float = 0.0
    volume: float = 1.0
    fade_in: float = 0.0
    fade_out: float = 0.0
    loop: bool = False       # repete até o fim da faixa
    pan: float = 0.0         # -1 esquerda … 1 direita (só fontes mono)
    speech: bool = False     # fala: abafa a trilha enquanto toca

    @property
    def length(self) -> float:
        return len(self.samples) / self.rate


def _fade(n: int, fade_in: int, fade_out: int) -> np.ndarray:
    gain = np.ones(n, dtype=np.float32)
    if fade_in > 0:
        k = min(fade_in, n)
        gain[:k] *= np.linspace(0.0, 1.0, k, endpoint=False, dtype=np.float32)
    if fade_out > 0:
        k = min(fade_out, n)
        gain[n - k:] *= np.linspace(1.0, 0.0, k, dtype=np.float32)
    return gain


def _pan(data: np.ndarray, pan: float) -> np.ndarray:
    if data.shape[1] != 1:
        return data
    angle = (np.clip(pan, -1, 1) + 1) * np.pi / 4      # potência constante
    return np.concatenate([data * np.cos(angle), data * np.sin(angle)], axis=1)


def mix_clips(clips: list[Clip], duration: float | None = None, rate: int = DEFAULT_RATE,
              duck: float = 1.0, duck_fade: float = 0.15, limit: bool = True) -> np.ndarray:
    """Soma os clipes numa faixa estéreo (n, 2) float32.

    `duck` < 1 multiplica os clipes `loop` (trilha) enquanto houver fala tocando.
    Sem `duration`, a faixa termina no fim do último clipe que não é loop.
    """
    if duration is None:
        ends = [c.start + c.length for c in clips if not c.loop] or [c.start + c.length for c in clips] or [0.0]
        duration = max(ends)
    n = int(round(duration * rate))
    out = np.zeros((n, 2), dtype=np.float32)

    speech_mask = np.zeros(n, dtype=np.float32)
    for clip in clips:
        if clip.speech:
            a = max(0, int(round(clip.start * rate)))
            b = min(n, a + int(round(clip.length * rate)))
            speech_mask[a:b] = 1.0
    if duck < 1.0 and speech_mask.any():
        k = max(1, int(duck_fade * rate))
        kernel = np.ones(k, dtype=np.float32) / k
        speech_mask = np.clip(np.convolve(speech_mask, kernel, mode="same") * 1.5, 0, 1)
    track_gain = 1.0 - (1.0 - duck) * speech_mask

    for clip in clips:
        data = _pan(as_2d(resample(clip.samples, clip.rate, rate)), clip.pan)
        data = to_channels(data, 2)
        start = int(round(clip.start * rate))
        if start >= n or len(data) == 0:
            continue
        span = n - max(start, 0)
        if clip.loop:
            reps = int(np.ceil(span / len(data)))
            data = np.tile(data, (reps, 1))[:span]
        else:
            data = data[: span]
        if start < 0:
            data = data[-start:]
            start = 0
        gain = _fade(len(data), int(clip.fade_in * rate), int(clip.fade_out * rate)) * clip.volume
        if clip.loop:
            gain = gain * track_gain[start:start + len(data)]
        out[start:start + len(data)] += data * gain[:, None]

    if limit:
        peak = float(np.max(np.abs(out))) if out.size else 0.0
        if peak > 0.98:
            out *= 0.98 / peak
    return out


# --------------------------------------------------------------------------
# roteiro de áudio (JSON)
# --------------------------------------------------------------------------


def load_source(entry: dict, base_dir: Path, rate: int = DEFAULT_RATE) -> tuple[np.ndarray, int]:
    """Resolve a fonte de um item: `arquivo` (WAV), `efeito` (preset/JSON/dict),
    `musica` (JSON do sequenciador) ou `texto` (voz por IA, extra [audio-ia])."""
    seed = int(entry.get("semente", 0))
    if "arquivo" in entry:
        return read_wav(_path(entry["arquivo"], base_dir))
    if "efeito" in entry:
        source = entry["efeito"]
        if isinstance(source, str) and source.lower().endswith(".json"):
            source = _path(source, base_dir)
        effect = sfx.vary(sfx.load_effect(source), float(entry.get("variar", 0)), seed)
        return sfx.synth(effect, seed, rate), rate
    if "musica" in entry:
        source = entry["musica"]
        song = music.load_song(_path(source, base_dir) if isinstance(source, str) else source)
        return music.render_song(song, rate, seed), rate
    if "texto" in entry:
        from .ai import voice
        return voice.speak(entry["texto"], voice=entry.get("voz"), speed=float(entry.get("velocidade", 1.0)))
    raise ValueError(f"item sem fonte (use arquivo, efeito, musica ou texto): {entry}")


def _path(value: str, base_dir: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() or path.exists() else base_dir / path


def _clip(entry: dict, base_dir: Path, rate: int, *, loop: bool = False, speech: bool = False) -> Clip:
    samples, src_rate = load_source(entry, base_dir, rate)
    return Clip(samples, src_rate, start=float(entry.get("t", entry.get("inicio", 0.0))),
                volume=float(entry.get("volume", 1.0)), fade_in=float(entry.get("fade_in", 0.0)),
                fade_out=float(entry.get("fade_out", 0.0)), loop=bool(entry.get("loop", loop)),
                pan=float(entry.get("pan", 0.0)), speech=speech)


def plan_clips(plan: dict, base_dir: Path = Path("."), rate: int = DEFAULT_RATE) -> list[Clip]:
    clips = []
    if plan.get("trilha"):
        clips.append(_clip(plan["trilha"], base_dir, rate, loop=True))
    for entry in plan.get("eventos", []):
        clips.append(_clip(entry, base_dir, rate))
    for entry in plan.get("falas", []):
        clips.append(_clip(entry, base_dir, rate, speech=True))
    return clips


def render_plan(plan: dict, base_dir: Path = Path("."), rate: int | None = None) -> tuple[np.ndarray, int]:
    """Roteiro de áudio → (amostras estéreo, taxa). Ver docs/manual.md, seção Som."""
    rate = int(rate or plan.get("taxa", DEFAULT_RATE))
    clips = plan_clips(plan, base_dir, rate)
    if not clips:
        raise ValueError("roteiro de áudio vazio: informe trilha, eventos ou falas")
    duration = plan.get("duracao")
    if duration is None and plan.get("video"):
        duration = video_duration(_path(plan["video"], base_dir))
    return mix_clips(clips, None if duration is None else float(duration), rate,
                     duck=float(plan.get("abafar", 1.0))), rate


# --------------------------------------------------------------------------
# vídeo (FFmpeg do imageio-ffmpeg, extra [video])
# --------------------------------------------------------------------------


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
    except ImportError:
        raise RuntimeError("juntar áudio ao MP4 precisa do FFmpeg: pip install -e .[video]") from None
    return imageio_ffmpeg.get_ffmpeg_exe()


def video_duration(video: Path) -> float:
    import imageio_ffmpeg  # noqa: F401  (mesma dependência do ffmpeg_exe)
    from imageio_ffmpeg import count_frames_and_secs
    try:
        return float(count_frames_and_secs(str(video))[1])
    except Exception as exc:
        raise ValueError(f"não consegui ler a duração de {video}: {exc}") from None


def mux_video(video: Path | str, audio: Path | str, out: Path | str, bitrate: str = "192k") -> Path:
    """Copia o vídeo e acrescenta o áudio (AAC). Áudio curto é completado com silêncio;
    o resultado tem a duração do vídeo (`-shortest` com `apad` trava no FFmpeg 7)."""
    video, audio, out = Path(video), Path(audio), Path(out)
    if out.resolve() == video.resolve():
        raise ValueError(f"a saída não pode ser o próprio vídeo de entrada: {out}")
    for path in (video, audio):
        if not path.is_file():
            raise FileNotFoundError(f"arquivo não encontrado: {path}")
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(video), "-i", str(audio),
           "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", bitrate,
           "-af", "apad", "-t", f"{video_duration(video):.3f}", str(out)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg falhou: {result.stderr.strip()[-500:]}")
    return out


def render_plan_to_files(plan: dict, out_dir: Path, base_dir: Path = Path(".")) -> list[Path]:
    """Grava `<nome>.wav` e, se o plano tiver `video`, `<nome>.mp4` com o som."""
    name = plan.get("name", "mix")
    samples, rate = render_plan(plan, base_dir)
    wav = write_wav(out_dir / f"{name}.wav", samples, rate)
    paths = [wav]
    if plan.get("video"):
        video = _path(plan["video"], base_dir)
        target = Path(plan["saida"]) if plan.get("saida") else out_dir / f"{name}.mp4"
        if target.resolve() == video.resolve():
            target = target.with_name(f"{target.stem}_som.mp4")
        paths.append(mux_video(video, wav, target))
    return paths


def trim_silence(samples: np.ndarray, rate: int, threshold_db: float = -45.0, keep: float = 0.05) -> np.ndarray:
    """Corta o silêncio do fim (abaixo de `threshold_db` dBFS), mantendo `keep` s de cauda."""
    data = np.asarray(samples, dtype=np.float32)
    loud = np.flatnonzero(np.max(np.abs(as_2d(data)), axis=1) > 10 ** (threshold_db / 20))
    if not len(loud):
        return data
    return data[: min(len(data), int(loud[-1]) + 1 + int(keep * rate))]


def make_loop(samples: np.ndarray, rate: int, crossfade: float = 1.0) -> np.ndarray:
    """Corta o silêncio final e funde o fim no começo (crossfade) para repetir sem emenda."""
    data = trim_silence(samples, rate)
    k = min(int(crossfade * rate), len(data) // 3)
    if k <= 0:
        return data
    ramp = np.linspace(0.0, 1.0, k, dtype=np.float32)
    if data.ndim == 2:
        ramp = ramp[:, None]
    out = data[:-k].copy()
    out[:k] = data[:k] * ramp + data[-k:] * (1.0 - ramp)
    return out
