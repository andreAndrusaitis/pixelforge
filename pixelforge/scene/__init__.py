"""Motor de cena: roteiro JSON → quadros → storyboard, GIF, WebP e MP4.

    from pixelforge.scene import open_scene, render_all
    timeline = open_scene("art/cenas/chegada.json", config)
    frames = render_all(timeline)

Design: docs/specs/2026-10-21-pixelforge-cena-design.md (etapas 1–5: cenário em
camadas, parallax, câmera, atores, diálogo, efeitos, transições, exportação, som —
`sound` —, títulos e legendas — `text` — e quadros de referência — `golden`).
"""

from __future__ import annotations

from pathlib import Path

from ..config import Config
from .actors import ActorView, SpriteSheet
from .compose import render_all, render_frame, storyboard
from .library import Backdrop, Layer, Library
from .script import Scene, SceneError, load_scene, parse_resolution, parse_scene
from .timeline import FrameState, Timeline
from .video import FORMATS, has_mp4, save_gif, save_mp4, save_webp

__all__ = [
    "ActorView", "Backdrop", "FORMATS", "SpriteSheet", "FrameState", "Layer", "Library", "Scene", "SceneError", "Timeline",
    "has_mp4", "load_scene", "open_scene", "parse_resolution", "parse_scene", "render_all",
    "render_frame", "save_gif", "save_mp4", "save_webp", "storyboard", "settings",
]


def settings(scene: Scene, config: Config, resolution=None, scale: int | None = None,
             fps: int | None = None) -> tuple[tuple[int, int], int, int]:
    """(resolução, escala, fps): linha de comando > roteiro > [cena] do pixelforge.toml."""
    defaults = config.data["cena"]
    size = parse_resolution(resolution or scene.resolution or defaults["resolucao"], defaults["presets"])
    scale = scale or scene.scale or int(defaults["escala"])
    fps = fps or scene.fps or int(defaults["fps"])
    if scale < 1 or fps < 1:
        raise SceneError("escala e fps devem ser >= 1")
    return size, scale, fps


def open_scene(path: str | Path, config: Config, resolution=None, scale: int | None = None,
               fps: int | None = None) -> Timeline:
    scene = load_scene(path)
    size, scale, fps = settings(scene, config, resolution, scale, fps)
    library = Library(config.art_dir)
    timeline = Timeline(scene, library, size, fps, scale)
    timeline.library = library
    return timeline
