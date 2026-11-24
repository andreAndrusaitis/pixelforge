"""Linha do tempo: planos → quadros, com câmera, atores, diálogo, efeitos,
títulos, legendas e transições de cada quadro, e a agenda de sons da cena.

Tudo em pixel inteiro e determinístico. Cada plano começa no quadro
`round(início_em_s × fps)`, então a soma das durações não acumula erro. O estado
dos atores (posição, animação, visibilidade) persiste entre planos; um `andar`
que não terminou no plano continua no seguinte.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .actors import ActorView, SpriteSheet
from .dialog import DialogView, LinePlan, box_extent, plan_line, view_at
from .effects import _rand, active
from .library import Backdrop, Library
from .script import (FRAMINGS, RGB, TITLE_DUR, Action, Caption, Effect, Line, Scene, SceneError, Sound, Title,
                     Transition)

CLOSE_ZOOM = FRAMINGS["close"]


@dataclass
class FrameState:
    index: int
    time: float
    shot: int                       # número do plano (1, 2, ...)
    camera: tuple[int, int]         # canto superior esquerdo da vista, em px do cenário
    backdrop: Backdrop
    background: RGB
    fade: tuple[RGB, float] | None  # (cor, quanto 0–1 já em degraus)
    transition: str = "fade"        # "fade" ou "cortina" (como `fade` é desenhado)
    zoom: int = 1
    shake: tuple[int, int] = (0, 0)
    actors: list[ActorView] = field(default_factory=list)
    dialog: DialogView | None = None
    effects: list[tuple[Effect, float]] = field(default_factory=list)
    title: tuple[Title, float, float] | None = None       # (título, s desde que entrou, s até sair)
    captions: list[Caption] = field(default_factory=list)
    ai: tuple[int, float] | None = None                    # (plano, s desde o início do clipe de IA)


@dataclass
class Cue:
    """Um som agendado: instante absoluto (s) na cena."""

    time: float
    sound: Sound
    repeat: int = 0                 # n-ésima repetição (passos): muda a semente


@dataclass
class Spoken:
    """Uma fala ou legenda narrada, com o instante (s) em que começa."""

    time: float
    text: str
    where: str
    line: Line | None = None
    caption: Caption | None = None
    plan: LinePlan | None = None    # páginas da fala (bipes de máquina de escrever)
    actor: str | None = None


@dataclass
class _Actor:
    sheet: SpriteSheet
    x: int
    y: int
    facing: str
    anim: str
    anim_t0: float
    visible: bool
    alpha: float


@dataclass
class _Move:
    actor: str
    t0: float
    t1: float
    start: tuple[int, int]
    end: tuple[int, int]
    after: str


@dataclass
class _Ramp:
    actor: str
    t0: float
    t1: float
    a0: float
    a1: float


class Timeline:
    def __init__(self, scene: Scene, library: Library, resolution: tuple[int, int], fps: int,
                 scale: int = 1):
        self.scene = scene
        self.resolution = resolution
        self.fps = fps
        self.scale = scale              # ampliação usada na exportação
        folder = scene.folder
        self.sheets = {name: library.sprite(spec.sprite, folder) for name, spec in scene.actors.items()}
        self.dialogs = [self._plan_dialogs(shot, library) for shot in scene.shots]
        self.durations = [shot.dur if shot.dur is not None else
                          (plans[-1][0] + plans[-1][1].total) if plans else TITLE_DUR
                          for shot, plans in zip(scene.shots, self.dialogs)]
        self.shot_ranges = shot_ranges(self.durations, fps)
        self.captions = [caption_times(shot.captions) for shot in scene.shots]
        self.frames: list[FrameState] = []
        self.cues: list[Cue] = []
        self.spoken: list[Spoken] = []
        self.ai_clips: dict[int, list[np.ndarray]] = {}    # plano → quadros (ver scene.ai.prepare)
        self._build(library)
        self._apply_fades()

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def duration(self) -> float:
        return self.frame_count / self.fps

    def index_at(self, t: float) -> int:
        if t < 0 or t > self.duration + 1e-9:
            raise ValueError(f"--t {t}: fora da cena (0 a {self.duration:.2f} s)")
        return min(int(t * self.fps + 1e-9), self.frame_count - 1)

    def at(self, t: float) -> FrameState:
        return self.frames[self.index_at(t)]

    def shot_start(self, shot: int) -> float:
        """Instante (s) em que o plano `shot` (1, 2, ...) começa."""
        return self.shot_ranges[shot - 1][0] / self.fps

    # ----------------------------------------------------------------------

    def _plan_dialogs(self, shot, library: Library) -> list[tuple[float, LinePlan]]:
        plans, t = [], 0.0
        for line in shot.lines:
            portrait = library.image(line.portrait, self.scene.folder) if line.portrait else None
            try:   # close no retrato: o retrato vai grande para a tela, não para a caixa
                plan = plan_line(line, self.resolution, None if line.closeup == "retrato" else portrait)
            except ValueError as exc:
                raise SceneError(str(exc)) from None
            if line.closeup == "retrato":
                plan.closeup = portrait
            start = line.start if line.start is not None else t
            plans.append((start, plan))
            t = start + plan.total
        return plans

    def _build(self, library: Library) -> None:
        width, height = self.resolution
        folder: Path | None = self.scene.folder
        backdrop = library.backdrop(self.scene.backdrop, folder) if self.scene.backdrop is not None else None
        background = self.scene.background
        camera, zoom = (0, 0), 1

        actors: dict[str, _Actor] = {}
        for name, spec in self.scene.actors.items():
            sheet = self.sheets[name]
            anim = sheet.check(spec.anim, f"atores.{name}.anim") if spec.anim else sheet.default_anim()
            actors[name] = _Actor(sheet, spec.pos[0], spec.pos[1], spec.facing, anim, 0.0,
                                  spec.visible, 1.0 if spec.visible else 0.0)
        moves: list[_Move] = []
        ramps: list[_Ramp] = []

        for shot, (start, end), plans in zip(self.scene.shots, self.shot_ranges, self.dialogs):
            shot_t0 = start / self.fps
            if shot.backdrop is not None:
                new = library.backdrop(shot.backdrop, folder)
                if new is not backdrop and shot.camera is None:
                    camera = (0, 0)   # nova locação: câmera volta ao canto
                backdrop = new
            if shot.background is not None:
                background = shot.background

            spec = shot.camera
            if spec is not None and (spec.zoom is not None or spec.framing is not None):
                zoom = spec.zoom or FRAMINGS[spec.framing]
            view_w, view_h = width // zoom, height // zoom
            limit = camera_limits(backdrop, view_w, view_h)
            clamp = lambda p, lim=limit: (_clamp(p[0], lim[0]), _clamp(p[1], lim[1]))  # noqa: E731
            n = end - start
            if spec is not None and spec.end is not None:
                a, b = clamp(spec.start or camera), clamp(spec.end)
                path = [interpolate(a, b, j / (n - 1) if n > 1 else 1.0, spec.curve) for j in range(n)]
            else:
                fixed = clamp(spec.pos if spec is not None and spec.pos is not None else camera)
                path = [fixed] * n
            follow_x = None

            for sound in shot.sounds:
                self.cues.append(Cue(shot_t0 + sound.start, sound))
            for line_start, plan in plans:
                line = plan.line
                self.spoken.append(Spoken(shot_t0 + line_start, line.text, line.where, line=line, plan=plan,
                                          actor=line.actor))
            for caption_start, caption in self.captions[shot.index - 1]:
                if caption.narrate:
                    self.spoken.append(Spoken(shot_t0 + caption_start, caption.text, caption.where,
                                              caption=caption))
            shot_end_t = end / self.fps

            pending = sorted(shot.actions, key=lambda a: a.start)
            for j in range(n):
                index = start + j
                t = index / self.fps
                while pending and shot_t0 + pending[0].start <= t + 1e-9:
                    action = pending.pop(0)
                    self._start(action, shot_t0 + action.start, actors, moves, ramps)
                _advance(t, actors, moves, ramps)

                dialog, speaker, page_t0, closeup = None, None, 0.0, None
                for line_start, plan in plans:
                    view = view_at(plan, t - shot_t0 - line_start)
                    if view is not None:
                        dialog, speaker = view, plan.line.actor
                        page_t0 = shot_t0 + line_start + plan.pages[view.page].start
                        closeup = plan.line.closeup

                views = []
                for name, actor in actors.items():
                    if not actor.visible:
                        continue
                    anim, t0 = actor.anim, actor.anim_t0
                    if (name == speaker and dialog is not None and dialog.typing
                            and "falar" in actor.sheet.animations):
                        anim, t0 = "falar", page_t0
                    views.append(ActorView(name, actor.sheet, actor.x, actor.y, actor.facing,
                                           anim, t - t0, actor.alpha))

                pos = path[j]
                if spec is not None and spec.framing is not None and j == 0:
                    pos = clamp(framing(spec.framing, actors[spec.target] if spec.target else None,
                                        view_w, view_h, camera))
                    path = [pos] * n
                if spec is not None and spec.follow is not None:
                    follow_x = follow(actors[spec.follow].x, pos[0] if follow_x is None else follow_x,
                                      view_w, spec.slack)
                    pos = clamp((follow_x, pos[1]))
                    follow_x = pos[0]
                base_camera = pos
                frame_zoom = zoom
                if closeup == "ator" and speaker is not None:   # corte para o close de quem fala
                    frame_zoom = max(zoom, CLOSE_ZOOM)
                    close_w, close_h = width // frame_zoom, height // frame_zoom
                    lim = camera_limits(backdrop, close_w, close_h)
                    side = dialog.plan.line.position
                    pos = clamp(framing("close", actors[speaker], close_w, close_h, pos,
                                        box_extent(self.resolution) // frame_zoom, side), lim)
                shake = (0, 0)
                if spec is not None and spec.shake is not None:
                    amplitude, dur = spec.shake
                    local = t - shot_t0
                    if local < dur:
                        k = amplitude * (1 - local / dur)
                        ids = np.array([index])
                        shake = (round((_rand(7, ids, 0)[0] * 2 - 1) * k), round((_rand(7, ids, 1)[0] * 2 - 1) * k))

                effects = [(e, t) for e in self.scene.effects if active(e, t)]
                effects += [(e, t - shot_t0) for e in shot.effects if active(e, t - shot_t0)]
                title = None
                if shot.title is not None:
                    local = t - shot_t0 - shot.title.start
                    left = (shot.title.dur if shot.title.dur is not None else shot_end_t - shot_t0
                            - shot.title.start) - local
                    if local >= 0 and left > 1e-9:
                        title = (shot.title, local, left)
                captions = [c for c0, c in self.captions[shot.index - 1] if c0 <= t - shot_t0 < c0 + c.length]
                ai = None
                if shot.ai is not None and t - shot_t0 + 1e-9 >= shot.ai.start:
                    ai = (shot.index, t - shot_t0 - shot.ai.start)
                self.frames.append(FrameState(index, t, shot.index, pos, backdrop, background, None,
                                              zoom=frame_zoom, shake=shake, actors=views, dialog=dialog,
                                              effects=effects, title=title, captions=captions, ai=ai))
            camera = base_camera
            for action in pending:
                raise SceneError(f"{action.where}: inicio {action.start:g} s passa do fim do plano "
                                 f"({self.durations[shot.index - 1]:g} s)")

    def _start(self, action: Action, t: float, actors: dict[str, _Actor], moves: list[_Move],
               ramps: list[_Ramp]) -> None:
        actor = actors[action.actor]
        sheet = actor.sheet
        if action.sound is not None and (action.sound.repeat is None or action.to is None):
            self.cues.append(Cue(t + action.sound.start, action.sound))
        for anim in (action.anim, action.after):
            if anim is not None:
                sheet.check(anim, action.where)
        if action.pos is not None:
            actor.x, actor.y = action.pos
        if action.facing is not None:
            actor.facing = action.facing
        if action.appear:
            actor.visible = True
            actor.alpha = 0.0 if action.fade else 1.0
            if action.fade:
                ramps.append(_Ramp(action.actor, t, t + action.fade, 0.0, 1.0))
        if action.vanish:
            if action.fade:
                ramps.append(_Ramp(action.actor, t, t + action.fade, actor.alpha, 0.0))
            else:
                actor.visible, actor.alpha = False, 0.0
        if action.to is not None:
            moves[:] = [m for m in moves if m.actor != action.actor]
            dx, dy = action.to[0] - actor.x, action.to[1] - actor.y
            dist = math.hypot(dx, dy)
            dur = action.dur if action.dur is not None else dist / action.speed
            if action.sound is not None and action.sound.repeat is not None:   # passos
                k = 0
                while k * action.sound.repeat < dur - 1e-9:
                    self.cues.append(Cue(t + action.sound.start + k * action.sound.repeat, action.sound, k))
                    k += 1
            previous = actor.anim
            walk = action.anim or ("andar" if "andar" in sheet.animations else previous)
            after = action.after or ("parado" if "parado" in sheet.animations else previous)
            _set_anim(actor, walk, t)
            if action.facing is None and dx:
                actor.facing = "direita" if dx > 0 else "esquerda"
            moves.append(_Move(action.actor, t, t + dur, (actor.x, actor.y), action.to, after))
        elif action.anim is not None:
            _set_anim(actor, action.anim, t)

    def _apply_fades(self) -> None:
        total = self.frame_count
        amounts = [0.0] * total
        styles: list[tuple[RGB, str] | None] = [None] * total

        def put(index: int, transition: Transition, amount: float) -> None:
            amount = quantize(amount, transition.steps)
            if amount > amounts[index]:
                kind = "cortina" if transition.kind == "cortina" else "fade"
                amounts[index], styles[index] = amount, (transition.color, kind)

        intro, outro = self.scene.intro, self.scene.outro
        if intro.kind != "corte":
            k = _frames(intro.dur, self.fps, total)
            for j in range(k):
                put(j, intro, 1 - j / k)
        if outro.kind != "corte":
            k = _frames(outro.dur, self.fps, total)
            for j in range(k):
                put(total - k + j, outro, (j + 1) / k)
        for shot, (start, end), (prev_start, _) in zip(self.scene.shots[1:], self.shot_ranges[1:],
                                                       self.shot_ranges):
            transition = shot.transition
            if transition is None or transition.kind == "corte":
                continue
            k_out = _frames(transition.dur / 2, self.fps, start - prev_start)
            k_in = _frames(transition.dur / 2, self.fps, end - start)
            for j in range(k_out):
                put(start - k_out + j, transition, (j + 1) / k_out)
            for j in range(k_in):
                put(start + j, transition, 1 - j / k_in)

        for state, amount, style in zip(self.frames, amounts, styles):
            if amount > 0:
                state.fade, state.transition = (style[0], amount), style[1]


def _set_anim(actor: _Actor, anim: str, t: float) -> None:
    if actor.anim != anim:
        actor.anim, actor.anim_t0 = anim, t


def _advance(t: float, actors: dict[str, _Actor], moves: list[_Move], ramps: list[_Ramp]) -> None:
    for move in list(moves):
        actor = actors[move.actor]
        span = move.t1 - move.t0
        u = 1.0 if span <= 0 else min(1.0, max(0.0, (t - move.t0) / span))
        actor.x = _round(move.start[0] + (move.end[0] - move.start[0]) * u)
        actor.y = _round(move.start[1] + (move.end[1] - move.start[1]) * u)
        if u >= 1.0:
            _set_anim(actor, move.after, move.t1)
            moves.remove(move)
    for ramp in list(ramps):
        actor = actors[ramp.actor]
        u = min(1.0, max(0.0, (t - ramp.t0) / (ramp.t1 - ramp.t0)))
        actor.alpha = ramp.a0 + (ramp.a1 - ramp.a0) * u
        if u >= 1.0:
            ramps.remove(ramp)
            if ramp.a1 == 0:
                actor.visible = False


def caption_times(captions: list[Caption]) -> list[tuple[float, Caption]]:
    """[(início em s relativo ao plano, legenda)]: sem `inicio`, logo depois da anterior."""
    times, t = [], 0.0
    for caption in captions:
        start = caption.start if caption.start is not None else t
        times.append((start, caption))
        t = start + caption.length
    return times


def framing(kind: str, actor: "_Actor | None", view_w: int, view_h: int,
            current: tuple[int, int], covered: int = 0, side: str = "baixo") -> tuple[int, int]:
    """Canto da câmera para um enquadramento pronto (antes do limite do cenário).

    geral: o ator inteiro com chão em volta (pé a 4/5 da altura); medio: o ator
    centrado na vertical; close: a cabeça (quarto de cima do sprite) no centro do
    espaço livre — `covered` px da vista (em `side`) ficam sob a caixa de diálogo.
    `geral` sem ator mantém a posição atual."""
    if actor is None:
        return current
    w, h = actor.sheet.size
    top = actor.y - actor.sheet.anchor[1]
    x = actor.x - view_w // 2
    if kind == "geral":
        return (x, actor.y - view_h * 4 // 5)
    if kind == "medio":
        return (x, top + h // 2 - view_h // 2)
    free = view_h - covered
    center = free // 2 if side == "baixo" else covered + free // 2
    return (x, top + h // 4 - center)


def follow(target_x: int, camera_x: int, view_w: int, slack: int) -> int:
    """Câmera que segue com folga: só anda quando o ator sai da faixa central ±`slack`."""
    center = camera_x + view_w // 2
    if target_x > center + slack:
        return target_x - slack - view_w // 2
    if target_x < center - slack:
        return target_x + slack - view_w // 2
    return camera_x


def shot_ranges(durations: list[float], fps: int) -> list[tuple[int, int]]:
    """[(primeiro quadro, quadro após o último)] de cada plano; mínimo 1 quadro."""
    ranges, elapsed, start = [], 0.0, 0
    for dur in durations:
        elapsed += dur
        end = max(_round(elapsed * fps), start + 1)
        ranges.append((start, end))
        start = end
    return ranges


def camera_limits(backdrop: Backdrop | None, width: int, height: int) -> tuple[int | None, int | None]:
    """Maior x/y da câmera sem sair do cenário (None = sem limite)."""
    if backdrop is None:
        return (0, 0)
    bw, bh = backdrop.size
    return (None if bw is None else max(0, bw - width), None if bh is None else max(0, bh - height))


def interpolate(a: tuple[int, int], b: tuple[int, int], u: float, curve: str) -> tuple[int, int]:
    if curve == "suave":
        u = u * u * (3 - 2 * u)
    return (_round(a[0] + (b[0] - a[0]) * u), _round(a[1] + (b[1] - a[1]) * u))


def quantize(amount: float, steps: int) -> float:
    return min(1.0, max(0.0, _round(amount * steps) / steps))


def _clamp(value: int, upper: int | None) -> int:
    value = max(0, value)
    return value if upper is None else min(value, upper)


def _frames(seconds: float, fps: int, available: int) -> int:
    return max(1, min(_round(seconds * fps), available))


def _round(value: float) -> int:
    """Arredonda .5 para cima (o round do Python arredonda para o par)."""
    return math.floor(value + 0.5)
