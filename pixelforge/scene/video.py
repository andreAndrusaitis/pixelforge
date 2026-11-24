"""Exportação de quadros: GIF e WebP animado (Pillow), MP4 via imageio-ffmpeg.

A escala é sempre inteira com vizinho mais próximo. MP4 só existe com o extra
`[video]` (pip install -e .[video]); sem ele, `has_mp4()` é falso.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from ..export import upscale

FORMATS = ("gif", "webp", "mp4")
MP4_CRF = 12


def has_mp4() -> bool:
    try:
        import imageio_ffmpeg  # noqa: F401
    except ImportError:
        return False
    return True


def frame_ms(fps: int) -> int:
    return max(1, round(1000 / fps))


def save_gif(frames: list[np.ndarray], path: Path, fps: int, scale: int) -> None:
    """Paleta exata quando a cena tem até 256 cores; senão quantiza a cena
    inteira numa paleta só (sem dithering, para não sujar o pixel)."""
    indexed, palette = _index_frames(frames)
    images = []
    for idx in indexed:
        image = Image.fromarray(idx, "P")
        image.putpalette(palette)
        images.append(upscale(image, scale))
    images[0].save(path, save_all=True, append_images=images[1:], duration=frame_ms(fps),
                   loop=0, optimize=False, disposal=1)


def _index_frames(frames: list[np.ndarray]) -> tuple[list[np.ndarray], list[int]]:
    stack = np.stack(frames)                                   # (n, h, w, 3)
    packed = (stack[..., 0].astype(np.uint32) << 16) | (stack[..., 1].astype(np.uint32) << 8) | stack[..., 2]
    colors, inverse = np.unique(packed, return_inverse=True)
    if len(colors) <= 256:
        rgb = [(int(c) >> 16 & 255, int(c) >> 8 & 255, int(c) & 255) for c in colors]
        indexed = inverse.reshape(packed.shape).astype(np.uint8)
        return list(indexed), _flat_palette(rgb)

    # amostra de quadros empilhados → paleta global → cada quadro mapeado nela
    step = max(1, len(frames) // 24)
    sample = Image.fromarray(np.concatenate(frames[::step], axis=0), "RGB")
    reference = sample.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    indexed = [np.array(Image.fromarray(f, "RGB").quantize(palette=reference, dither=Image.Dither.NONE))
               for f in frames]
    return indexed, reference.getpalette()[:768]


def _flat_palette(colors: list[tuple[int, int, int]]) -> list[int]:
    flat = [v for c in colors for v in c]
    return flat + [0] * (768 - len(flat))


def save_webp(frames: list[np.ndarray], path: Path, fps: int, scale: int) -> None:
    images = [upscale(Image.fromarray(f, "RGB"), scale) for f in frames]
    images[0].save(path, save_all=True, append_images=images[1:], duration=frame_ms(fps),
                   loop=0, lossless=True, method=4)


def save_mp4(frames: list[np.ndarray], path: Path, fps: int, scale: int, audio: Path | None = None) -> None:
    """MP4 H.264; com `audio` (WAV), grava o vídeo mudo ao lado e junta o som (AAC)."""
    if audio is not None:
        from ..audio.mix import mux_video

        silent = path.with_name(f"{path.stem}_mudo{path.suffix}")
        save_mp4(frames, silent, fps, scale)
        try:
            mux_video(silent, audio, path)
        finally:
            silent.unlink(missing_ok=True)
        return

    import imageio_ffmpeg

    h, w = frames[0].shape[:2]
    # yuv420p exige lados pares: repete a última coluna/linha se preciso
    pad_w, pad_h = (w * scale) % 2, (h * scale) % 2
    size = (w * scale + pad_w, h * scale + pad_h)
    writer = imageio_ffmpeg.write_frames(
        str(path), size, fps=fps, codec="libx264", pix_fmt_in="rgb24", pix_fmt_out="yuv420p",
        quality=None, macro_block_size=1, ffmpeg_log_level="error",
        output_params=["-crf", str(MP4_CRF), "-preset", "medium", "-tune", "animation",
                       "-movflags", "+faststart"])
    writer.send(None)
    try:
        for frame in frames:
            big = np.repeat(np.repeat(frame, scale, axis=0), scale, axis=1)
            if pad_w or pad_h:
                big = np.pad(big, ((0, pad_h), (0, pad_w), (0, 0)), mode="edge")
            writer.send(np.ascontiguousarray(big).tobytes())
    finally:
        writer.close()
