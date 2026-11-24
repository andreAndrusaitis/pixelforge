"""Comandos `video-ia`: baixar, clipe, sprite, pixelizar.

    python -m pixelforge video-ia baixar
    python -m pixelforge video-ia clipe out/cena/cena_t7.5s.png --nativa 640x360 --movimento "vento no capim" --dur 3
    python -m pixelforge video-ia sprite art/personagens/ana.json --anim parado,andar,falar --quem "a girl in a red coat"
    python -m pixelforge video-ia pixelizar video.mp4 --tamanho 320x180 --paleta-de art/cenario.png
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image


def add_video_ai_commands(sub) -> None:
    p = sub.add_parser("video-ia", help="vídeo e animação por IA local (Wan 2.2) → pixel art estável")
    cmds = p.add_subparsers(title="ações", dest="acao")

    q = cmds.add_parser("baixar", help="baixa os pesos do Wan 2.2 TI2V-5B (~19,6 GB, Apache-2.0)")
    q.set_defaults(handler=cmd_baixar)

    q = cmds.add_parser("clipe", help="imagem (quadro, retrato, arte) + movimento → clipe em pixel art")
    q.add_argument("imagem", type=Path, help="PNG/spec/script; quadros ampliados precisam de --nativa")
    q.add_argument("--movimento", required=True, help='descrição do movimento, ex.: "chuva fina, vento no capim"')
    q.add_argument("--dur", type=float, default=3.0, help="segundos de clipe (padrão 3, máx. 5)")
    q.add_argument("--nativa", help="LxA da pixel art nativa (reduz um PNG ampliado, ex.: quadro --t)")
    q.add_argument("--fps", type=int, default=12, help="fps da animação em pixel (8–12; padrão 12)")
    q.add_argument("--semente", type=int, default=0)
    q.add_argument("--tipo", default="cena", choices=["cena", "cenario", "personagem", "retrato"],
                   help="tipo para a nota técnica (estilo comparar)")
    q.add_argument("--regiao", action="append", default=[], help="x,y,l,a nativos que podem mudar; pode repetir")
    q.add_argument("--passos", type=int, help="passos de amostragem (padrão 24)")
    q.add_argument("--out", type=Path, help="pasta de saída (padrão: out/video-ia/<nome>/)")
    q.set_defaults(handler=cmd_clipe)

    q = cmds.add_parser("sprite", help="anima um sprite por IA (parado/andar/falar) e grava a spec com animations")
    q.add_argument("sprite", type=Path, help="spec .json ou script .py do sprite")
    q.add_argument("--anim", default="parado,andar,falar", help="animações (nomes), separadas por vírgula")
    q.add_argument("--quem", default=None, help='quem é, em inglês (ex.: "a tall old man in a hat")')
    q.add_argument("--movimento", action="append", default=[], help='nome=descrição para trocar a padrão')
    q.add_argument("--quadros", type=int, help="quadros por animação (padrão: todos no fps)")
    q.add_argument("--fps", type=int, default=8)
    q.add_argument("--dur", type=float, default=2.0)
    q.add_argument("--semente", type=int, default=0)
    q.add_argument("--saida", type=Path, help="spec de saída (padrão: <sprite>_ia.json ao lado)")
    q.set_defaults(handler=cmd_sprite)

    q = cmds.add_parser("pixelizar", help="pixelização temporal de um vídeo qualquer (paleta travada, anti-cintilação)")
    q.add_argument("video", type=Path, help="MP4/GIF/WebP")
    q.add_argument("--tamanho", required=True, help="LxA nativo, ex.: 320x180")
    q.add_argument("--paleta-de", type=Path, help="imagem/arte cuja paleta é travada (padrão: k-means do clipe)")
    q.add_argument("--cores", type=int, default=32)
    q.add_argument("--fps", type=int, default=12)
    q.add_argument("--out", type=Path, help="pasta de saída (padrão: out/video-ia/<nome>/)")
    q.set_defaults(handler=cmd_pixelizar)


def _size(text: str) -> tuple[int, int]:
    try:
        w, h = (int(v) for v in text.lower().replace("×", "x").split("x"))
    except ValueError:
        raise ValueError(f"tamanho '{text}': use LxA, ex.: 320x180") from None
    return w, h


def _image(path: Path, native: str | None) -> np.ndarray:
    if path.suffix.lower() in (".json", ".py"):
        from ..artfile import load_art
        return load_art(path).frames[0].pixels
    with Image.open(path) as im:
        rgba = im.convert("RGBA")
        if native:
            rgba = rgba.resize(_size(native), Image.NEAREST)
        return np.array(rgba)


def _save_clip(frames: list[np.ndarray], out_dir: Path, name: str, fps: int, scale: int) -> list[Path]:
    from ..scene.video import has_mp4, save_gif, save_mp4

    out_dir.mkdir(parents=True, exist_ok=True)
    rgb = [f[..., :3] if f.shape[-1] == 3 else _over_checker(f) for f in frames]
    paths = [out_dir / f"{name}.gif"]
    save_gif(rgb, paths[0], fps, scale)
    if has_mp4() and frames[0].shape[-1] == 3:
        paths.append(out_dir / f"{name}.mp4")
        save_mp4(rgb, paths[-1], fps, scale)
    sheet = np.concatenate([f[..., :3] if f.shape[-1] == 3 else _over_checker(f) for f in frames[::max(1, len(frames) // 6)][:6]], axis=1)
    paths.append(out_dir / f"{name}_quadros.png")
    Image.fromarray(np.kron(sheet, np.ones((scale, scale, 1), np.uint8))).save(paths[-1])
    return paths


def _over_checker(rgba: np.ndarray) -> np.ndarray:
    h, w = rgba.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    bg = np.where(((yy // 4 + xx // 4) % 2)[..., None] == 0, 200, 160).astype(np.uint8).repeat(3, axis=2)
    a = rgba[..., 3:4] > 127
    return np.where(a, rgba[..., :3], bg)


def cmd_baixar(args, config) -> int:
    from .wan import base_dir, download, gguf_path

    t0 = time.time()
    download()
    print(f"Wan 2.2 TI2V-5B pronto em {time.time() - t0:.0f} s:\n  {base_dir()}\n  {gguf_path()}")
    return 0


def cmd_clipe(args, config) -> int:
    from .clips import make_clip

    image = _image(args.imagem, args.nativa)
    if image[..., 3].min() == 255:
        image = image[..., :3]
    regions = [tuple(int(v) for v in r.split(",")) for r in args.regiao]
    mask = None
    if regions:
        from ..scene.ai import region_mask
        mask = region_mask((image.shape[1], image.shape[0]), regions)
    out_dir = args.out or config.output_dir / "video-ia" / args.imagem.stem
    t0 = time.time()
    clip = make_clip(image, args.movimento, min(args.dur, 5.0), fps=args.fps, seed=args.semente,
                     cache_dir=config.output_dir / "video-ia" / "_cache", config=config, tipo=args.tipo,
                     region=mask, steps=args.passos, log=lambda m: print(m, flush=True))
    scale = max(1, 960 // image.shape[1])
    for path in _save_clip(clip.frames, out_dir, args.imagem.stem, clip.fps, scale):
        print(f"  {path}")
    print(f"{clip.describe()} — {time.time() - t0:.0f} s no total")
    return 0


def cmd_sprite(args, config) -> int:
    from ..artfile import load_art
    from .sprite import DEFAULT_WHO, animate_sprite, save_animated

    art = load_art(args.sprite)
    names = [n.strip() for n in args.anim.split(",") if n.strip()]
    custom = dict(m.split("=", 1) for m in args.movimento)
    anims = {n: custom.get(n) for n in names}
    t0 = time.time()
    result = animate_sprite(art, anims, seconds=args.dur, fps=args.fps, frames=args.quadros,
                            who=args.quem or DEFAULT_WHO, seed=args.semente,
                            cache_dir=config.output_dir / "video-ia" / "_cache", config=config,
                            log=lambda m: print(m, flush=True))
    out = args.saida or args.sprite.with_name(f"{args.sprite.stem}_ia.json")
    print(f"  {save_animated(art, result, out)}")
    for anim in result:
        print(f"  {anim.name}: {len(anim.frames)} quadros a {anim.fps} fps, semente {anim.seed}, nota {anim.score}")
        for path in _save_clip(anim.frames, config.output_dir / "video-ia" / out.stem, anim.name, anim.fps, 8):
            print(f"    {path}")
    print(f"total {time.time() - t0:.0f} s")
    return 0


def cmd_pixelizar(args, config) -> int:
    import imageio_ffmpeg  # noqa: F401  (extra [video])

    from .pixelize import PixelizeOptions, flicker, palette_of, pixelize_clip

    reader = imageio_ffmpeg.read_frames(str(args.video))
    meta = next(reader)
    w, h = meta["size"]
    frames = [np.frombuffer(b, np.uint8).reshape(h, w, 3) for b in reader]
    palette = palette_of(_image(args.paleta_de, None)) if args.paleta_de else None
    size = _size(args.tamanho)
    out = pixelize_clip(frames, PixelizeOptions(size, float(meta["fps"]), args.fps, palette=palette,
                                                colors=args.cores))
    out_dir = args.out or config.output_dir / "video-ia" / args.video.stem
    for path in _save_clip(out, out_dir, f"{args.video.stem}_pixel", args.fps, max(1, 960 // size[0])):
        print(f"  {path}")
    print(f"{len(out)} quadros, cintilação {flicker(out):.1%}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit("use: python -m pixelforge video-ia ...")
