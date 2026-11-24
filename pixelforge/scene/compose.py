"""Composição de um quadro (numpy, resolução lógica) e folha de storyboard."""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ..export import upscale
from .actors import ActorView
from .dialog import draw as draw_dialog
from .effects import BAYER4, EffectContext
from .effects import apply as apply_effect
from .library import Layer, loop_index
from .text import draw_captions, draw_title
from .timeline import FrameState, Timeline, _round


def render_frame(timeline: Timeline, state: FrameState) -> np.ndarray:
    """Quadro RGB uint8 (altura, largura, 3) na resolução lógica.

    Ordem: camadas de fundo → atores (por y, o de baixo na frente) → camadas
    `frente` → zoom → efeitos → caixa de diálogo → legendas → título → transição."""
    zoom = state.zoom
    camera = (state.camera[0] + state.shake[0], state.camera[1] + state.shake[1])
    clip = ai_frame(timeline, state)
    if clip is not None and clip.shape[-1] == 3:   # plano inteiro animado por IA (origem quadro/imagem)
        canvas = clip.copy()
    else:
        canvas = render_world(timeline, state, sprite=clip)

    context = None
    for effect, elapsed in state.effects:
        context = context or EffectContext(elapsed, camera, zoom)
        context.t = elapsed
        canvas = apply_effect(canvas, effect, context)
    if state.dialog is not None or state.captions or state.title is not None:
        canvas = np.ascontiguousarray(canvas)
    if state.dialog is not None:
        draw_dialog(canvas, state.dialog)
    if state.captions:
        draw_captions(canvas, state.captions, state.dialog.plan.line.position if state.dialog else None)
    if state.title is not None:
        draw_title(canvas, *state.title)
    if state.fade is not None:
        color, amount = state.fade
        if state.transition == "cortina":
            canvas = curtain(canvas, color, amount)
        else:
            mixed = canvas.astype(np.float32) * (1 - amount) + np.array(color, np.float32) * amount
            canvas = np.floor(mixed + 0.5).astype(np.uint8)
    return canvas


def render_world(timeline: Timeline, state: FrameState, sprite: np.ndarray | None = None) -> np.ndarray:
    """Só o mundo (camadas, atores, zoom), sem efeitos nem interface — também é o
    quadro de partida da IA. `sprite`: quadro de IA no lugar do ator do plano."""
    width, height = timeline.resolution
    zoom = state.zoom
    view_w, view_h = -(-width // zoom), -(-height // zoom)
    canvas = np.empty((view_h, view_w, 3), dtype=np.uint8)
    canvas[:] = state.background
    camera = (state.camera[0] + state.shake[0], state.camera[1] + state.shake[1])
    layers = state.backdrop.layers if state.backdrop is not None else []
    for layer in layers:
        if not layer.front:
            draw_layer(canvas, layer, camera, state.time)
    ai_actor = timeline.scene.shots[state.shot - 1].ai.actor if sprite is not None else None
    for order, actor in sorted(enumerate(state.actors), key=lambda item: (item[1].y, item[0])):
        draw_actor(canvas, actor, camera, sprite if actor.name == ai_actor else None)
    for layer in layers:
        if layer.front:
            draw_layer(canvas, layer, camera, state.time)
    if zoom > 1:
        canvas = np.repeat(np.repeat(canvas, zoom, axis=0), zoom, axis=1)[:height, :width]
    return canvas


def ai_frame(timeline: Timeline, state: FrameState) -> np.ndarray | None:
    """Quadro do clipe de IA do plano neste instante (None = sem IA ou ainda não preparado)."""
    if state.ai is None:
        return None
    frames = timeline.ai_clips.get(state.ai[0])
    if not frames:
        return None
    spec = timeline.scene.shots[state.ai[0] - 1].ai
    fps = spec.fps or timeline.fps
    return frames[loop_index(int(state.ai[1] * fps + 1e-9), len(frames), spec.loop)]


def draw_actor(canvas: np.ndarray, actor: ActorView, camera: tuple[int, int],
               override: np.ndarray | None = None) -> None:
    pixels, x, y = actor.image(override)
    if actor.alpha < 1:   # aparecer/sumir com dithering ordenado: sem cores novas
        h, w = pixels.shape[:2]
        keep = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w] < actor.alpha
        pixels = pixels.copy()
        pixels[~keep, 3] = 0
    blit(canvas, pixels, x - camera[0], y - camera[1])


def curtain(canvas: np.ndarray, color, amount: float) -> np.ndarray:
    """Cortina: duas folhas fecham das laterais para o centro, em blocos de 8 px."""
    out = canvas.copy()
    h, w = out.shape[:2]
    block = max(1, 8 * max(1, h // 180))
    cover = int(math.ceil(amount * (w / 2) / block)) * block
    if cover:
        out[:, :min(cover, w)] = color
        out[:, max(w - cover, 0):] = color
        edge = (np.array(color, np.int32) + 48).clip(0, 255).astype(np.uint8)
        if cover < w // 2:   # barra da borda da cortina, um tom mais claro
            out[:, cover - 1:cover] = edge
            out[:, w - cover:w - cover + 1] = edge
    return out


def render_all(timeline: Timeline) -> list[np.ndarray]:
    return [render_frame(timeline, state) for state in timeline.frames]


def draw_layer(canvas: np.ndarray, layer: Layer, camera: tuple[int, int], t: float) -> None:
    src = layer.frame_at(t)
    h, w = src.shape[:2]
    x = layer.pos[0] - _round(camera[0] * layer.parallax)
    y = layer.pos[1] - _round(camera[1] * layer.parallax)
    xs = range(x % w - w, canvas.shape[1], w) if "x" in layer.repeat else [x]
    ys = range(y % h - h, canvas.shape[0], h) if "y" in layer.repeat else [y]
    for ty in ys:
        for tx in xs:
            blit(canvas, src, tx, ty)


def blit(canvas: np.ndarray, src: np.ndarray, x: int, y: int) -> None:
    """Cola `src` (RGBA) em `canvas` (RGB) com recorte e alfa."""
    ch, cw = canvas.shape[:2]
    sh, sw = src.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + sw, cw), min(y + sh, ch)
    if x0 >= x1 or y0 >= y1:
        return
    part = src[y0 - y:y1 - y, x0 - x:x1 - x]
    dst = canvas[y0:y1, x0:x1]
    alpha = part[..., 3]
    if alpha.min() == 255:
        dst[:] = part[..., :3]
        return
    a = alpha[..., None].astype(np.uint32)
    mixed = (part[..., :3].astype(np.uint32) * a + dst.astype(np.uint32) * (255 - a) + 127) // 255
    dst[:] = mixed.astype(np.uint8)


# --------------------------------------------------------------------------
# Storyboard: início, meio e fim de cada plano
# --------------------------------------------------------------------------

THUMB_TARGET = 560     # largura aproximada de cada miniatura, em px
SHEET_BG = (32, 32, 38)
LABEL = (230, 230, 235)
SUBTLE = (150, 150, 160)


def storyboard_frames(timeline: Timeline) -> list[list[int]]:
    """Índices [início, meio, fim] de cada plano (sem repetir em planos curtos)."""
    rows = []
    for start, end in timeline.shot_ranges:
        picks = [start, start + (end - start) // 2, end - 1]
        rows.append(sorted(set(picks)))
    return rows


def storyboard(timeline: Timeline) -> Image.Image:
    width, height = timeline.resolution
    scale = max(1, _round(THUMB_TARGET / width))
    tw, th = width * scale, height * scale
    pad, label_h, header_h = 16, 26, 44
    rows = storyboard_frames(timeline)
    columns = 3
    sheet_w = pad + columns * (tw + pad)
    sheet_h = header_h + len(rows) * (label_h + th + pad) + pad // 2
    sheet = Image.new("RGB", (sheet_w, sheet_h), SHEET_BG)
    draw = ImageDraw.Draw(sheet)
    font, small = _font(18), _font(15)

    scene = timeline.scene
    draw.text((pad, 12), f"{scene.name}  ·  {width}x{height} @ {timeline.fps} fps  ·  "
              f"{len(rows)} plano(s)  ·  {timeline.duration:.2f} s", fill=LABEL, font=font)
    for r, indices in enumerate(rows):
        top = header_h + r * (label_h + th + pad)
        for c, index in enumerate(indices):
            state = timeline.frames[index]
            left = pad + c * (tw + pad)
            draw.text((left, top + 2), f"plano {state.shot} · t={state.time:.2f}s", fill=LABEL, font=small)
            extra = f"cam {state.camera[0]},{state.camera[1]}"  # fonte padrão sem acentos
            draw.text((left + tw - draw.textlength(extra, font=small), top + 2), extra, fill=SUBTLE, font=small)
            frame = Image.fromarray(render_frame(timeline, state), "RGB")
            sheet.paste(upscale(frame, scale), (left, top + label_h))
    return sheet


def _font(size: int):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow sem FreeType
        return ImageFont.load_default()
