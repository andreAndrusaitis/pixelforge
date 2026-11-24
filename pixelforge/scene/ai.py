"""Animação por IA dentro da cena: prepara os clipes antes de renderizar.

    "planos": [{ "dur": 5, "ia": {"origem": "quadro", "movimento": "nuvens correndo, poças tremulando",
                                 "regiao": [[0, 0, 640, 140]], "dur": 4} }]
    "camadas": [{ "arte": "ceu", "parallax": 0.1, "ia": {"movimento": "clouds drifting", "dur": 4} }]

- origem `quadro`: o quadro do plano (mundo sem efeitos nem interface) no início do clipe;
  o clipe pixelizado substitui cenário + atores no plano (efeitos, diálogo e legendas
  continuam por cima);
- origem `imagem`: uma arte do tamanho da tela, animada no lugar do mundo;
- origem `sprite` + `ator`: anima só o sprite do ator (fundo recortado, paleta dele) e o
  ator usa esses quadros durante o plano;
- `ia` numa camada do cenário: a própria camada anima (em laço `vaivem` por padrão).

A paleta é travada na da imagem de partida; `regiao` limita o que pode mudar. Os clipes
brutos ficam em cache por hash (`out/<cena>/_ia/`), então renderizar de novo não regera.
Sem o extra `[video-ia]` (ou com `--sem-ia`), tudo fica parado, com aviso.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .script import AI_MAX_DUR, AISpec, SceneError
from .timeline import Timeline


@dataclass
class AIReport:
    where: str
    detail: str
    attempts: list[dict] = field(default_factory=list)


def ai_targets(timeline: Timeline) -> list[tuple[AISpec, object]]:
    """[(spec, alvo)]: alvo = número do plano ou a camada (Layer) do cenário."""
    targets: list[tuple[AISpec, object]] = []
    seen = set()
    for state in timeline.frames:
        for layer in (state.backdrop.layers if state.backdrop is not None else []):
            if layer.ai is not None and id(layer) not in seen:
                seen.add(id(layer))
                targets.append((layer.ai, layer))
    for shot in timeline.scene.shots:
        if shot.ai is not None:
            targets.append((shot.ai, shot.index))
    return targets


def has_ai(timeline: Timeline) -> bool:
    return bool(ai_targets(timeline))


def region_mask(size: tuple[int, int], regions: list[tuple[int, int, int, int]]) -> np.ndarray | None:
    if not regions:
        return None
    w, h = size
    mask = np.zeros((h, w), bool)
    for x, y, rw, rh in regions:
        mask[max(0, y):max(0, y + rh), max(0, x):max(0, x + rw)] = True
    return mask


def _source(timeline: Timeline, spec: AISpec, target, library) -> tuple[np.ndarray, str, tuple | None]:
    """(imagem de partida, tipo para a nota, cor de fundo a recortar)."""
    from .compose import render_world

    if not isinstance(target, int):        # camada
        return target.frames[0], "cenario", None
    start, end = timeline.shot_ranges[target - 1]
    index = min(end - 1, start + int(round(spec.start * timeline.fps)))
    state = timeline.frames[index]
    if spec.origin == "quadro":
        return render_world(timeline, state), "cena", None
    if spec.origin == "imagem":
        image = library.image(spec.image, timeline.scene.folder)[..., :3]
        w, h = timeline.resolution
        if image.shape[:2] != (h, w):
            raise SceneError(f"{spec.where}.imagem: a arte tem {image.shape[1]}x{image.shape[0]}, "
                             f"a tela {w}x{h} (use uma arte do tamanho da tela)")
        return image, "cena", None
    view = next((a for a in state.actors if a.name == spec.actor), None)
    if view is None:
        raise SceneError(f"{spec.where}.ator: '{spec.actor}' não está visível no início do clipe")
    from ..ai_video.sprite import key_color
    from ..ai_video.pixelize import palette_of
    pixels = view.sheet.frame(view.anim, view.elapsed)
    return pixels, "personagem", key_color(palette_of(pixels))


def prepare(timeline: Timeline, library, config, *, cache_dir: Path, use_ai: bool = True,
            generator=None, log=print) -> tuple[list[AIReport], list[str]]:
    """Gera/lê do cache e pixeliza todos os clipes de IA da cena. Devolve (relatórios, avisos)."""
    targets = ai_targets(timeline)
    if not targets:
        return [], []
    if generator is None and use_ai:
        from ..ai_video.wan import BackendError, WanI2V, dependencies_ok, installed
        if not dependencies_ok() or not installed():
            what = "extra [video-ia]" if not dependencies_ok() else "pesos (python -m pixelforge video-ia baixar)"
            return [], [f"vídeo por IA indisponível ({what}): {len(targets)} animação(ões) por IA ficam paradas"]
    if not use_ai and generator is None:
        return [], [f"--sem-ia: {len(targets)} animação(ões) por IA ficam paradas"]

    from ..ai_video.clips import make_clip
    from ..audio.ai.common import BackendError

    reports, warnings = [], []
    for spec, target in targets:
        image, tipo, key = _source(timeline, spec, target, library)
        if not isinstance(target, int):
            shot_dur = AI_MAX_DUR
        else:
            shot_dur = timeline.durations[target - 1] - spec.start
        seconds = min(spec.dur or shot_dur, AI_MAX_DUR)
        fps = spec.fps or timeline.fps
        size = (image.shape[1], image.shape[0])
        palette = None
        if spec.palette_from:
            from ..ai_video.pixelize import palette_of
            arts = [image] + [library.art(library.resolve(ref, timeline.scene.folder)).frames[0].pixels
                              for ref in spec.palette_from]
            palette = np.unique(np.concatenate([palette_of(a) for a in arts]), axis=0)
        log(f"{spec.where}: {spec.motion!r} ({seconds:g} s, {size[0]}x{size[1]})")
        try:
            clip = make_clip(image, spec.motion, seconds, fps=fps, seed=spec.seed, cache_dir=cache_dir,
                             config=config, tipo=tipo, region=region_mask(size, spec.regions), key=key,
                             palette=palette, generator=generator, log=log)
        except BackendError as exc:      # GPU ocupada, modelo ausente…: a cena sai, parada nesse trecho
            warnings.append(f"{spec.where}: {exc} — fica parado")
            continue
        if isinstance(target, int):
            timeline.ai_clips[target] = clip.frames
        else:
            target.frames = [f if f.shape[-1] == 4 else np.dstack([f, target.frames[0][..., 3]])
                             for f in clip.frames]
            target.fps, target.loop = fps, spec.loop
        reports.append(AIReport(spec.where, clip.describe(), clip.attempts))
    return reports, warnings
