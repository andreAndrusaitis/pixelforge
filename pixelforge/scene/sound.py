"""Som da cena (etapa 5): bloco `audio` do roteiro → faixa estéreo sincronizada.

Monta clipes (`pixelforge.audio.mix.Clip`) a partir da linha do tempo e mistura
com `mix_clips`:

- trilha e ambientes em loop pela cena inteira (fade de entrada/saída seguindo as
  transições da cena, se não houver `fade_in`/`fade_out`);
- efeitos em instantes (`audio.eventos`), presos a planos (`sons`) ou a ações
  (`som`, com `repetir` para passos enquanto o ator anda);
- falas: voz por IA (Kokoro, extra `[audio-ia]`), WAV gravado (`arquivo`) ou
  bipes de máquina de escrever, um por letra digitada; legendas com `narrar`.

Sem `[audio-ia]`, o que for procedural continua: falas viram bipes, e trilha,
ambiente ou voz por descrição/texto são pulados — sempre com aviso. Resultados de
IA ficam em cache (`<saída>/_som/`), então a segunda renderização é rápida.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from ..audio import mix, sfx
from ..audio.wavio import DEFAULT_RATE, read_wav, write_wav
from .script import SceneError, Sound
from .timeline import Spoken, Timeline

BIP_PITCH = 520.0     # Hz do bipe padrão; atores podem ter `tom`
BIP_EVERY = 2         # um bipe a cada N letras (como nos RPGs)
AMBIENT_SECONDS = 10.0


@dataclass
class SoundReport:
    samples: np.ndarray
    rate: int
    clips: int
    warnings: list[str] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return len(self.samples) / self.rate


def ai_available(what: str) -> bool:
    """IA de som instalada? `what`: voz | ambiente | musica."""
    from ..audio.ai.common import available
    if what == "voz":
        return available("kokoro") and available("torch")
    if what == "ambiente":
        return available("diffusers") and available("torch")
    from ..audio.ai.music import ace_dir, ace_python
    try:
        return ace_python(ace_dir()).is_file()
    except Exception:
        return False


class SceneSound:
    def __init__(self, timeline: Timeline, use_ai: bool = True, cache_dir: Path | None = None,
                 art_dir: Path | None = None, rate: int = DEFAULT_RATE):
        self.timeline = timeline
        self.scene = timeline.scene
        self.use_ai = use_ai
        self.cache_dir = cache_dir
        self.art_dir = art_dir
        self.rate = rate
        self.warnings: list[str] = []
        self._ai: dict[str, bool] = {}
        self._warned: set[str] = set()

    # ------------------------------------------------------------------

    def render(self) -> SoundReport:
        clips = self.clips()
        duration = self.timeline.duration
        audio = self.scene.audio
        duck = audio.duck if audio is not None else 1.0
        samples = mix.mix_clips(clips, duration, self.rate, duck=duck)
        if audio is not None and audio.volume != 1.0:
            samples = np.clip(samples * audio.volume, -0.98, 0.98).astype(np.float32)
        return SoundReport(samples, self.rate, len(clips), self.warnings)

    def clips(self) -> list[mix.Clip]:
        audio = self.scene.audio
        clips: list[mix.Clip] = []
        if audio is not None:
            for sound in [audio.track, *audio.ambience]:
                if sound is not None:
                    clip = self._clip(sound, 0.0, background=True)
                    if clip is not None:
                        clips.append(clip)
            for sound in audio.events:
                start = sound.start + (self.timeline.shot_start(sound.shot) if sound.shot else 0.0)
                clips += filter(None, [self._clip(sound, start)])
        for cue in self.timeline.cues:
            clips += filter(None, [self._clip(cue.sound, cue.time, repeat=cue.repeat)])
        for spoken in self.timeline.spoken:
            clips += self._speech(spoken)
        end = self.timeline.duration
        return [c for c in clips if c.start < end]

    # ------------------------------------------------------------------

    def _clip(self, sound: Sound, start: float, background: bool = False, repeat: int = 0) -> mix.Clip | None:
        loaded = self._load(sound, repeat)
        if loaded is None:
            return None
        samples, rate = loaded
        fade_in, fade_out = sound.fade_in, sound.fade_out
        if background:   # trilha/ambiente acompanham as transições de entrada e saída da cena
            if fade_in is None and self.scene.intro.kind != "corte":
                fade_in = self.scene.intro.dur
            if fade_out is None and self.scene.outro.kind != "corte":
                fade_out = self.scene.outro.dur
        return mix.Clip(samples, rate, start=start, volume=sound.volume, fade_in=fade_in or 0.0,
                        fade_out=fade_out or 0.0, loop=sound.loop, pan=sound.pan)

    def _load(self, sound: Sound, repeat: int = 0) -> tuple[np.ndarray, int] | None:
        kind, source = sound.kind, dict(sound.source)
        if repeat:
            source["semente"] = int(source.get("semente", 0)) + repeat
        if kind in ("arquivo", "efeito", "musica"):
            value = source[kind]
            if isinstance(value, str) and (kind == "arquivo" or value.lower().endswith(".json")):
                source[kind] = str(self._path(value, sound.where))
            try:
                return mix.load_source(source, self.scene.folder or Path("."), self.rate)
            except (KeyError, ValueError, OSError) as exc:
                raise SceneError(f"{sound.where}: {exc.args[0] if exc.args else exc}") from None
        if kind == "texto":
            return self._voice(source["texto"], source.get("voz"), float(source.get("velocidade", 1.0)),
                               sound.where)
        # descricao: trilha por IA (ACE-Step) na trilha; ambiente por IA (AudioLDM2) no resto
        what = "musica" if sound is (self.scene.audio.track if self.scene.audio else None) else "ambiente"
        return self._describe(what, source["descricao"], float(source.get("duracao", 0) or 0),
                              int(source.get("semente", 0)), sound.where)

    def _path(self, value: str, where: str) -> Path:
        candidates = [Path(value)] if Path(value).is_absolute() else []
        if self.scene.folder is not None:
            candidates.append(self.scene.folder / value)
        if self.art_dir is not None:
            candidates.append(self.art_dir / value)
        candidates.append(Path(value))
        for path in candidates:
            if path.is_file():
                return path
        raise SceneError(f"{where}: arquivo '{value}' não encontrado (procurado na pasta do roteiro e em art/)")

    # ------------------------------------------------------------------ IA

    def _has(self, what: str) -> bool:
        if not self.use_ai:
            return False
        if what not in self._ai:
            self._ai[what] = ai_available(what)
        return self._ai[what]

    def _warn(self, key: str, message: str) -> None:
        if key not in self._warned:
            self._warned.add(key)
            self.warnings.append(message)

    def _cached(self, kind: str, params: dict, make) -> tuple[np.ndarray, int]:
        if self.cache_dir is None:
            return make()
        digest = hashlib.sha1(json.dumps([kind, params], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        path = self.cache_dir / f"{kind}_{digest[:12]}.wav"
        if path.is_file():
            return read_wav(path)
        samples, rate = make()
        write_wav(path, samples, rate)
        return samples, rate

    def _voice(self, text: str, voice: str | None, speed: float, where: str) -> tuple[np.ndarray, int] | None:
        if not self._has("voz"):
            self._warn("voz", "voz por IA indisponível (extra [audio-ia]"
                       + (", ou --sem-ia" if not self.use_ai else "") + "): falas com texto ficam sem voz")
            return None
        from ..audio.ai import voice as tts
        try:
            return self._cached("voz", {"t": text, "v": voice, "s": speed},
                                lambda: tts.speak(text, voice=voice, speed=speed))
        except ValueError as exc:
            raise SceneError(f"{where}: {exc}") from None

    def _describe(self, what: str, prompt: str, seconds: float, seed: int, where: str):
        label = {"musica": "trilha por IA (ACE-Step)", "ambiente": "ambiente por IA (AudioLDM2)"}[what]
        if not self._has(what):
            hint = "python -m pixelforge som instalar musica" if what == "musica" else "extra [audio-ia]"
            self._warn(what, f"{label} indisponível ({hint}); '{where}' ficou sem som")
            return None
        seconds = seconds or (min(self.timeline.duration, 30.0) if what == "musica" else AMBIENT_SECONDS)
        params = {"p": prompt, "d": seconds, "s": seed}
        if what == "ambiente":
            from ..audio.ai import ambient
            return self._cached("ambiente", params,
                                lambda: ambient.generate(prompt, seconds=seconds, seed=seed))
        from ..audio.ai import music as ace

        def make():
            out = (self.cache_dir or Path("out/som")) / "_ace_tmp.wav"
            result = ace.generate(prompt, seconds=seconds, out=out, seed=seed)
            return read_wav(result["path"])
        return self._cached("musica", params, make)

    # ------------------------------------------------------------------ falas

    def _speech(self, spoken: Spoken) -> list[mix.Clip]:
        audio = self.scene.audio
        voices = audio.voices if audio is not None else None
        mode = voices.mode if voices is not None else "nenhum"
        line, caption = spoken.line, spoken.caption
        if line is not None and line.audio:   # fala gravada vale em qualquer modo
            samples, rate = read_wav(self._path(line.audio, line.where))
            return [mix.Clip(samples, rate, start=spoken.time, volume=voices.volume if voices else 1.0,
                             speech=True)]
        if mode == "nenhum":
            return []
        actor = self.scene.actors.get(spoken.actor) if spoken.actor else None
        if mode == "auto":
            if caption is not None:
                voice = caption.voice or voices.narrator or voices.voice
            else:
                voice = line.voice or (actor.voice if actor else None) or voices.voice
            if self._has("voz"):
                loaded = self._voice(spoken.text, voice, voices.speed, spoken.where)
                if line is not None and loaded is not None and len(loaded[0]) / loaded[1] > line_span(spoken) + 0.5:
                    self.warnings.append(f"{spoken.where}: a voz dura {len(loaded[0]) / loaded[1]:.1f} s, "
                                         f"mais que a caixa ({line_span(spoken):.1f} s); "
                                         "aumente 'fim' ou diminua 'velocidade' da fala")
                return [mix.Clip(*loaded, start=spoken.time, volume=voices.volume, speech=True)] if loaded else []
            self._warn("voz-fala", "voz por IA indisponível (extra [audio-ia]"
                       + ("" if self.use_ai else " desligado por --sem-ia")
                       + "): falas viram bipes de máquina de escrever"
                       + ("; legendas narradas ficam em silêncio" if any(s.caption for s in self.timeline.spoken)
                          else ""))
        if line is None:   # legenda narrada sem voz: só o texto
            return []
        pitch = actor.pitch if actor is not None and actor.pitch else BIP_PITCH
        return [mix.Clip(typewriter(spoken, pitch, self.rate), self.rate, start=spoken.time,
                         volume=voices.bip)]


def line_span(spoken: Spoken) -> float:
    return spoken.plan.total if spoken.plan is not None else 0.0


def blip(pitch: float, rate: int) -> np.ndarray:
    effect = sfx.load_effect({"onda": "quadrada", "freq": pitch, "duty": 0.25, "ataque": 0.0,
                              "decaimento": 0.045, "sustentacao": 0.0, "volume": 0.6})
    return sfx.synth(effect, 0, rate)


def typewriter(spoken: Spoken, pitch: float, rate: int = DEFAULT_RATE) -> np.ndarray:
    """Bipes sincronizados com as letras que aparecem na caixa (um a cada BIP_EVERY)."""
    plan = spoken.plan
    sample = blip(pitch, rate)
    out = np.zeros(int(plan.total * rate) + len(sample) + 1, np.float32)
    speed = plan.line.speed
    for page in plan.pages:
        text = "".join(page.lines)
        for i, ch in enumerate(text):
            if i % BIP_EVERY or not ch.isalnum():
                continue
            a = int((page.start + (i + 1) / speed) * rate)
            out[a:a + len(sample)] += sample[: len(out) - a]
    return out


def render_scene_audio(timeline: Timeline, use_ai: bool = True, cache_dir: Path | None = None,
                       art_dir: Path | None = None, rate: int = DEFAULT_RATE) -> SoundReport:
    return SceneSound(timeline, use_ai, cache_dir, art_dir, rate).render()


def has_sound(timeline: Timeline) -> bool:
    """A cena tem algo para tocar? (bloco `audio`, `sons`, `som` nas ações ou fala gravada)."""
    scene = timeline.scene
    return (scene.audio is not None or bool(timeline.cues)
            or any(s.line is not None and s.line.audio for s in timeline.spoken))
