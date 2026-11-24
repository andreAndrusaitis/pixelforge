"""Linha de comando: python -m pixelforge <comando> ...

  render    spec .json ou script .py → imagens
  convert   imagem de referência → pixel art (e, opcionalmente, spec .json)
  new       cria uma spec .json em branco para desenhar
  mask      cria máscara (polígono/elipse) para isolar a pessoa/objeto da foto
  compare   compara a arte com a foto de referência (painéis + nota de semelhança)
  palettes  lista paletas ou mostra uma (com amostra opcional)
  presets   lista os presets de conversão do pixelforge.toml
  cena        roteiro de cena .json → storyboard + GIF/WebP/MP4
  quadro      um quadro da cena no instante --t (PNG ampliado)
  storyboard  folha com início/meio/fim de cada plano
  golden      quadros de referência da cena: compara pixel a pixel (ou --regravar)
  video-ia    vídeo/animação por IA local (Wan 2.2) → pixel art estável (baixar, clipe, sprite, pixelizar)
  som       efeitos chiptune, música, voz, ambientes e mixagem (pixelforge.audio)
  acervo    índice de assets (art/acervo.json): listar, buscar, indexar, tag, versoes
  studio    estúdio web local (galeria, visualizador, retoque, cena, pedidos)
  estilo    decomposição técnica das referências e nota de uma arte contra elas
  mcp       servidor MCP local (stdio) para outros projetos chamarem o motor
  ia        IA de imagem local: rascunho por IA → pixel art (gerar, pixelizar, variar, modelos)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

from . import palettes as pal
from .artfile import load_art, load_script, to_art  # noqa: F401  (reexportados)
from .config import Config, load_config
from .convert import ConvertOptions, convert, parse_size, portable_path
from .export import ExportOptions, export, upscale
from .sprite import SPEC_KEYS, Art, SpecError, Sprite, load_spec, save_spec


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "handler", None):
        parser.print_help()
        return 1
    try:
        config = load_config(Path(args.config) if args.config else None)
        return args.handler(args, config)
    except (SpecError, ValueError, KeyError, FileNotFoundError) as exc:
        message = exc.args[0] if isinstance(exc, KeyError) and exc.args else exc
        print(f"erro: {message}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pixelforge", description="Pixel art gerada por código.")
    parser.add_argument("--config", help="caminho do pixelforge.toml (padrão: procura a partir da pasta atual)")
    sub = parser.add_subparsers(title="comandos")

    p = sub.add_parser("render", help="renderiza specs .json ou scripts .py")
    p.add_argument("files", nargs="+", type=Path)
    add_export_args(p)
    p.set_defaults(handler=cmd_render)

    p = sub.add_parser("convert", help="converte imagem de referência em pixel art")
    p.add_argument("image", type=Path)
    p.add_argument("--preset", help="preset do pixelforge.toml")
    p.add_argument("--size", help="lado ou LxA, ex.: 32 ou 32x48")
    p.add_argument("--palette", help="nome de paleta ou nº de cores adaptativas")
    p.add_argument("--dither", choices=["none", "floyd", "bayer2", "bayer4"])
    p.add_argument("--dither-strength", type=float)
    p.add_argument("--fit", choices=["contain", "cover", "stretch"])
    p.add_argument("--contrast", type=float)
    p.add_argument("--saturation", type=float)
    p.add_argument("--sharpness", type=float)
    p.add_argument("--resample", choices=["box", "nearest", "bilinear", "lanczos", "detail"])
    p.add_argument("--detail", type=float, help="peso de tons escuros no resample detail (0–2)")
    p.add_argument("--edge-spread", type=float, help="limiar de borda do resample detail (0.1–0.4)")
    p.add_argument("--merge", type=float, help="funde tons quase iguais (ΔE OKLab, ex.: 0.05; 0 desliga)")
    p.add_argument("--defringe", type=int, help="passadas removendo franja do fundo na borda (0 desliga)")
    p.add_argument("--smooth", choices=["none", "kuwahara"], help="suavização que preserva bordas")
    p.add_argument("--smooth-radius", type=int, help="raio do Kuwahara (0 = automático)")
    p.add_argument("--lines", type=float, help="força do traço vindo das bordas da foto (0–1)")
    p.add_argument("--line-threshold", type=float, help="quão forte a borda precisa ser (0–1)")
    p.add_argument("--crop", help="x,y,w,h em frações (0–1) ou pixels da foto")
    p.add_argument("--mask", help="imagem de máscara (branco = manter); veja o comando mask")
    p.add_argument("--focus", help="x,y,w,h (frações do quadro) que ganha mais cores, ex.: rosto")
    p.add_argument("--focus-weight", type=float)
    p.add_argument("--background", help='cor de fundo "#rrggbb" ("" = transparente)')
    p.add_argument("--alpha-threshold", type=int)
    p.add_argument("--remove-bg", help='"auto" (cor dos cantos) ou #rrggbb')
    p.add_argument("--bg-tolerance", type=int)
    p.add_argument("--no-trim", dest="trim", action="store_false", default=None)
    p.add_argument("--cleanup", type=int, help="passadas de limpeza (0 desliga)")
    p.add_argument("--outline", help='"auto", #rrggbb ou "" para desligar')
    p.add_argument("--name", help="nome da arte (padrão: nome do arquivo)")
    p.add_argument("--to-spec", action="store_true", help="também grava art/<nome>.json para retoque")
    add_export_args(p)
    p.set_defaults(handler=cmd_convert)

    p = sub.add_parser("new", help="cria spec .json em branco")
    p.add_argument("name")
    p.add_argument("--size", help="lado ou LxA (padrão: [new] size)")
    p.add_argument("--palette", help="paleta inicial (padrão: [new] palette)")
    p.add_argument("--frames", type=int, default=1, help="nº de frames de animação")
    p.add_argument("--force", action="store_true", help="sobrescreve se já existir")
    p.set_defaults(handler=cmd_new)

    p = sub.add_parser("mask", help="cria máscara a partir de polígonos/elipses")
    p.add_argument("image", type=Path)
    p.add_argument("--polygon", action="append", default=[],
                   help='pontos "x,y x,y ..." (frações 0–1 ou pixels); pode repetir')
    p.add_argument("--ellipse", action="append", default=[], help='"cx,cy,rx,ry"; pode repetir')
    p.add_argument("--subtract", action="append", default=[], help="polígono a remover da máscara")
    p.add_argument("--feather", type=float, default=0.6, help="suavização da borda, em %% do lado maior")
    p.add_argument("--out", type=Path, help="arquivo de saída (padrão: out/masks/<imagem>_mask.png)")
    p.set_defaults(handler=cmd_mask)

    p = sub.add_parser("compare", help="compara arte com a foto de referência")
    p.add_argument("art", type=Path, help="spec .json gerada por convert (guarda a origem) ou .png")
    p.add_argument("--image", type=Path, help="foto de referência (obrigatória para .png)")
    p.add_argument("--like", type=Path, help="spec convertida cuja foto e opções de preparo serão usadas")
    p.add_argument("--out", type=Path, help="arquivo do painel (padrão: out/<nome>/<nome>_compare.png)")
    p.set_defaults(handler=cmd_compare)

    p = sub.add_parser("palettes", help="lista paletas ou mostra uma")
    p.add_argument("name", nargs="?")
    p.add_argument("--swatch", action="store_true", help="grava amostra PNG em out/palettes/")
    p.set_defaults(handler=cmd_palettes)

    p = sub.add_parser("presets", help="lista presets de conversão")
    p.set_defaults(handler=cmd_presets)

    p = sub.add_parser("cena", help="renderiza um roteiro de cena: storyboard + vídeos")
    add_scene_args(p)
    p.add_argument("--formats", help="lista separada por vírgula: gif,webp,mp4 (padrão: [cena] formatos)")
    p.add_argument("--sem-som", action="store_true", help="ignora o bloco audio (MP4 mudo, sem WAV)")
    p.set_defaults(handler=cmd_cena)

    p = sub.add_parser("quadro", help="um quadro da cena no instante t (PNG ampliado)")
    add_scene_args(p)
    p.add_argument("--t", type=float, required=True, help="instante em segundos, ex.: 7.5")
    p.set_defaults(handler=cmd_quadro)

    p = sub.add_parser("storyboard", help="folha com início/meio/fim de cada plano")
    add_scene_args(p)
    p.set_defaults(handler=cmd_storyboard)

    # motor de arte: character, animate, recolor, shade, lint, tileset, tilemap, aseprite
    from .cli_art import add_art_commands
    add_art_commands(sub)

    # som: efeitos, música, voz, ambientes, mixagem
    from .audio.cli import add_audio_commands
    add_audio_commands(sub)

    # acervo e estúdio web
    add_library_parser(sub)

    p = sub.add_parser("studio", help="abre o estúdio web local (galeria, visualizador, retoque, pedidos)")
    p.add_argument("--porta", type=int, default=8765, help="porta em 127.0.0.1 (padrão: 8765; 0 = livre)")
    p.add_argument("--abrir", action="store_true", help="abre o navegador padrão")
    p.set_defaults(handler=cmd_studio)

    p = sub.add_parser("golden", help="compara quadros de cena com as referências salvas (testes golden)")
    p.add_argument("manifest", type=Path, nargs="?", default=Path("tests/golden/golden.json"),
                   help="manifesto {cenas: [{roteiro, quadros}]} (padrão: tests/golden/golden.json)")
    p.add_argument("--regravar", action="store_true", help="grava os quadros atuais como nova referência")
    p.add_argument("--out", type=Path, help="pasta dos quadros atuais e diffs (padrão: out/golden/)")
    p.set_defaults(handler=cmd_golden)

    # servidor MCP (extra [mcp])
    p = sub.add_parser("mcp", help="servidor MCP local (stdio) para outros projetos chamarem o motor")
    p.add_argument("--raiz", type=Path, help="raiz do repositório PixelForge (padrão: PIXELFORGE_RAIZ, "
                   "pasta atual ou a pasta do pacote)")
    p.set_defaults(handler=cmd_mcp)

    # estilo: decomposição das referências e nota técnica
    from .style.cli import add_style_commands
    add_style_commands(sub)
    # IA de imagem local: rascunho por IA → pixel art (gerar, pixelizar, variar, modelos)
    from .ai_image.cli import add_ai_commands
    add_ai_commands(sub)

    # vídeo e animação por IA local (extra [video-ia])
    from .ai_video.cli import add_video_ai_commands
    add_video_ai_commands(sub)
    return parser


def add_scene_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("script", type=Path, help="roteiro de cena .json")
    p.add_argument("--resolucao", help='preset ([cena.presets]), "LxA" ou L,A; ex.: hd, gba, 256x224')
    p.add_argument("--escala", type=int, help="ampliação inteira na exportação (ex.: 6 → 1920x1080 em hd)")
    p.add_argument("--fps", type=int, help="quadros por segundo")
    p.add_argument("--out", type=Path, help="pasta de saída (padrão: out/<nome>/)")
    p.add_argument("--sem-ia", action="store_true",
                   help="não usa IA (som por IA e animações \"ia\" ficam de fora): só o procedural, com aviso")


def add_export_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--formats", help="lista separada por vírgula: png,jpg,webp,gif,svg")
    p.add_argument("--scales", help="lista separada por vírgula, ex.: 1,8,16")
    p.add_argument("--out", type=Path, help="pasta de saída (padrão: out/<nome>/)")
    p.add_argument("--no-preview", dest="preview", action="store_false", default=None)


def export_options(args, config: Config) -> ExportOptions:
    out = config.data["output"]
    return ExportOptions(
        formats=_csv(args.formats) if args.formats else list(out["formats"]),
        scales=[int(s) for s in _csv(args.scales)] if args.scales else list(out["scales"]),
        preview=out["preview"] if args.preview is None else args.preview,
        jpg_background=out["jpg_background"],
        jpg_quality=out["jpg_quality"],
    )


def _csv(value: str) -> list[str]:
    return [v.strip().lower() for v in value.split(",") if v.strip()]


def _report(art: Art, paths: list[Path]) -> None:
    w, h = art.size
    frames = f", {len(art.frames)} frames" if len(art.frames) > 1 else ""
    print(f"{art.name}: {w}x{h}, {len(art.colors())} cores{frames}")
    for path in paths:
        print(f"  {path}")


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------


def cmd_render(args, config: Config) -> int:
    options = export_options(args, config)
    for file in args.files:
        art = load_art(file)
        out_dir = args.out or config.output_dir / art.name
        _report(art, export(art, out_dir, options))
    return 0


# --------------------------------------------------------------------------
# convert
# --------------------------------------------------------------------------

_CONVERT_FIELDS = ("palette", "dither", "dither_strength", "fit", "contrast", "saturation", "sharpness",
                   "resample", "alpha_threshold", "remove_bg", "bg_tolerance", "trim", "cleanup", "outline",
                   "detail", "edge_spread", "merge", "defringe", "smooth", "smooth_radius", "lines", "line_threshold", "crop", "mask",
                   "focus", "focus_weight", "background")


def cmd_convert(args, config: Config) -> int:
    values = config.preset(args.preset)
    if args.size:
        values["size"] = parse_size(args.size)
    for field in _CONVERT_FIELDS:
        value = getattr(args, field)
        if value is not None:
            values[field] = value
    if isinstance(values.get("palette"), str) and values["palette"].isdigit():
        values["palette"] = int(values["palette"])
    if values.get("mask"):
        values["mask"] = portable_path(values["mask"])

    options = ConvertOptions.from_dict(values)
    art = convert(args.image, options, name=args.name, palette_dirs=config.palette_dirs)
    out_dir = args.out or config.output_dir / art.name
    _report(art, export(art, out_dir, export_options(args, config)))
    if args.to_spec:
        print(f"  spec: {save_spec(art, config.art_dir / f'{art.name}.json')}")
    return 0


# --------------------------------------------------------------------------
# mask / compare
# --------------------------------------------------------------------------


def cmd_mask(args, config: Config) -> int:
    from .masks import build_mask, mask_preview

    if not (args.polygon or args.ellipse):
        raise ValueError("informe ao menos um --polygon ou --ellipse")
    with Image.open(args.image) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
    mask = build_mask(image.size, args.polygon, args.ellipse, args.subtract, args.feather)
    out = args.out or config.output_dir / "masks" / f"{args.image.stem}_mask.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    mask.save(out)
    preview = out.with_name(out.stem + "_preview.png")
    mask_preview(image, mask).save(preview)
    print(f"máscara: {out}")
    print(f"  conferir: {preview}")
    return 0


def cmd_compare(args, config: Config) -> int:
    from .compare import compare_image, reference_grid, similarity

    art = load_art(args.art)
    meta = load_spec(args.like).meta if args.like else art.meta
    source = args.image or (Path(meta["source"]) if "source" in meta else None)
    if source is None:
        raise ValueError("informe --image ou --like (a arte não guarda a foto de origem)")
    values = dict(meta.get("convert", {}))
    values["size"] = list(art.size)
    options = ConvertOptions.from_dict(values)
    reference = reference_grid(source, options)
    score = similarity(reference, art.frames[0], options.alpha_threshold)
    out = args.out or config.output_dir / art.name / f"{art.name}_compare.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    compare_image(reference, art.frames[0]).save(out)
    print(f"{art.name}: {score}")
    print(f"  painel: {out}")
    return 0


# --------------------------------------------------------------------------
# new / palettes / presets
# --------------------------------------------------------------------------


def cmd_new(args, config: Config) -> int:
    defaults = config.data["new"]
    width, height = parse_size(args.size or defaults["size"])
    palette_name = args.palette or defaults["palette"]
    colors = [c for c in pal.get(palette_name, config.palette_dirs) if c[3] > 0]
    if len(colors) > len(SPEC_KEYS):
        raise ValueError(f"paleta '{palette_name}' tem cores demais para uma spec")

    path = config.art_dir / f"{args.name}.json"
    if path.exists() and not args.force:
        raise ValueError(f"{path} já existe (use --force para sobrescrever)")

    keys = {color: SPEC_KEYS[i] for i, color in enumerate(colors)}
    art = Art(args.name, [Sprite.blank(width, height) for _ in range(max(args.frames, 1))])
    save_spec(art, path, keys)
    print(f"spec criada: {path} ({width}x{height}, paleta {palette_name})")
    for color, key in keys.items():
        print(f"  {key} = {pal.to_hex(color)}")
    return 0


def cmd_palettes(args, config: Config) -> int:
    found = pal.available(config.palette_dirs)
    if not args.name:
        for name, path in found.items():
            origin = "embutida" if path.parent == pal.BUILTIN_DIR else "usuário"
            print(f"{name:<14} {len(pal.load_hex_file(path)):>3} cores  ({origin})")
        return 0

    colors = pal.get(args.name, config.palette_dirs)
    for i, color in enumerate(colors):
        key = SPEC_KEYS[i] if i < len(SPEC_KEYS) else " "
        print(f"  {key} = {pal.to_hex(color)}")
    if args.swatch:
        swatch = Sprite.blank(len(colors), 1)
        for i, color in enumerate(colors):
            swatch.pixels[0, i] = color
        path = config.output_dir / "palettes" / f"{args.name.lower()}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        upscale(swatch.to_image(), 32).save(path)
        print(f"amostra: {path}")
    return 0


def cmd_presets(args, config: Config) -> int:
    default = config.data["convert"]["preset"]
    for name, values in config.data["presets"].items():
        merged = {**ConvertOptions().__dict__, **values}
        mark = " (padrão)" if name == default else ""
        size = parse_size(merged["size"])
        print(f"{name}{mark}: {size[0]}x{size[1]}, paleta {merged['palette']}, dither {merged['dither']}, "
              f"contorno {merged['outline'] or 'não'}, fundo {merged['remove_bg'] or 'mantido'}")
    return 0


# --------------------------------------------------------------------------
# cena / quadro / storyboard
# --------------------------------------------------------------------------


def _open_scene(args, config: Config):
    from .scene import open_scene

    resolution = args.resolucao
    if resolution and "," in resolution:
        try:
            resolution = [int(v) for v in resolution.split(",")]
        except ValueError:
            raise ValueError(f"--resolucao {args.resolucao}: use preset, LxA ou L,A") from None
    timeline = open_scene(args.script, config, resolution, args.escala, args.fps)
    out_dir = args.out or config.output_dir / timeline.scene.name
    out_dir.mkdir(parents=True, exist_ok=True)
    _prepare_scene_ai(timeline, out_dir, config, not getattr(args, "sem_ia", False))
    return timeline, out_dir


def _prepare_scene_ai(timeline, out_dir: Path, config: Config, use_ai: bool) -> None:
    """Animações `"ia"` da cena: gera (ou lê do cache) e pixeliza antes de renderizar."""
    from .scene.ai import has_ai, prepare

    if not has_ai(timeline):
        return
    reports, warnings = prepare(timeline, timeline.library, config, cache_dir=out_dir / "_ia", use_ai=use_ai,
                                log=lambda m: print(m, flush=True))
    for warning in warnings:
        print(f"aviso: {warning}", file=sys.stderr)
    for report in reports:
        print(f"  {report.where}: {report.detail}")


def _scene_header(timeline) -> None:
    w, h = timeline.resolution
    print(f"{timeline.scene.name}: {w}x{h} × {timeline.scale} ({w * timeline.scale}x{h * timeline.scale}), "
          f"{timeline.fps} fps, {len(timeline.scene.shots)} plano(s), {timeline.frame_count} quadros, "
          f"{timeline.duration:.2f} s")


def _write_storyboard(timeline, out_dir: Path) -> Path:
    from .scene import storyboard

    path = out_dir / f"{timeline.scene.name}_storyboard.png"
    storyboard(timeline).save(path)
    return path


def cmd_cena(args, config: Config) -> int:
    from .scene import FORMATS, has_mp4, render_all, save_gif, save_mp4, save_webp

    formats = _csv(args.formats) if args.formats else [f.lower() for f in config.data["cena"]["formatos"]]
    bad = [f for f in formats if f not in FORMATS]
    if bad:
        raise ValueError(f"formato(s) de cena não suportado(s): {', '.join(bad)}. Use: {', '.join(FORMATS)}")
    if "mp4" in formats and not has_mp4():
        print("aviso: MP4 precisa do extra [video] (pip install -e .[video]); seguindo com GIF.",
              file=sys.stderr)
        formats = [f for f in formats if f != "mp4"] or ["gif"]
        if "gif" not in formats:
            formats.append("gif")

    timeline, out_dir = _open_scene(args, config)
    _scene_header(timeline)
    print(f"  {_write_storyboard(timeline, out_dir)}")
    audio = None if args.sem_som else _write_scene_audio(timeline, out_dir, config, not args.sem_ia)
    frames = render_all(timeline)
    writers = {"gif": save_gif, "webp": save_webp, "mp4": save_mp4}
    for fmt in dict.fromkeys(formats):
        path = out_dir / f"{timeline.scene.name}.{fmt}"
        if fmt == "mp4":
            save_mp4(frames, path, timeline.fps, timeline.scale, audio=audio)
        else:
            writers[fmt](frames, path, timeline.fps, timeline.scale)
        print(f"  {path}" + (" (com som)" if fmt == "mp4" and audio else ""))
    if audio is not None and "mp4" not in formats:
        print("aviso: só o MP4 leva som; o áudio ficou no .wav ao lado.", file=sys.stderr)
    return 0


def _write_scene_audio(timeline, out_dir: Path, config: Config, use_ai: bool) -> Path | None:
    """Mixa o som da cena em <nome>.wav (ou None se a cena não tem som)."""
    from .audio.wavio import write_wav
    from .scene.sound import has_sound, render_scene_audio

    if not has_sound(timeline):
        return None
    report = render_scene_audio(timeline, use_ai, out_dir / "_som", config.art_dir)
    for warning in report.warnings:
        print(f"aviso: {warning}", file=sys.stderr)
    path = write_wav(out_dir / f"{timeline.scene.name}.wav", report.samples, report.rate)
    print(f"  {path} ({report.clips} som(ns), {report.duration:.2f} s)")
    return path


def cmd_quadro(args, config: Config) -> int:
    from .scene import render_frame

    timeline, out_dir = _open_scene(args, config)
    state = timeline.at(args.t)
    image = upscale(Image.fromarray(render_frame(timeline, state), "RGB"), timeline.scale)
    path = out_dir / f"{timeline.scene.name}_t{args.t:g}s.png"
    image.save(path)
    print(f"{timeline.scene.name}: quadro {state.index} (plano {state.shot}, t={state.time:.2f}s, "
          f"câmera {state.camera[0]},{state.camera[1]})")
    print(f"  {path}")
    return 0


def cmd_storyboard(args, config: Config) -> int:
    timeline, out_dir = _open_scene(args, config)
    _scene_header(timeline)
    print(f"  {_write_storyboard(timeline, out_dir)}")
    return 0


# --------------------------------------------------------------------------
# acervo / studio
# --------------------------------------------------------------------------


def add_library_parser(sub) -> None:
    p = sub.add_parser("acervo", help="biblioteca de assets (art/acervo.json): listar, buscar, indexar, tag")
    acervo = p.add_subparsers(title="ações", dest="acao")

    def filters(q: argparse.ArgumentParser) -> None:
        q.add_argument("--tipo", help="personagem | cenario | objeto | cena | som")
        q.add_argument("--tag", action="append", default=[], help="exige a tag (pode repetir)")
        q.add_argument("--projeto", help="projeto de origem")
        q.add_argument("--json", action="store_true", help="saída em JSON")

    q = acervo.add_parser("listar", help="lista o acervo (com filtros)")
    filters(q)
    q.set_defaults(handler=cmd_acervo_listar, texto="")
    q = acervo.add_parser("buscar", help="busca por nome, tag, tipo ou projeto")
    q.add_argument("texto", help="palavras procuradas (todas precisam aparecer)")
    filters(q)
    q.set_defaults(handler=cmd_acervo_listar)
    q = acervo.add_parser("indexar", help="reconstrói art/acervo.json varrendo art/")
    q.add_argument("--sem-miniaturas", dest="miniaturas", action="store_false",
                   help="não gera out/<nome>/<nome>_miniatura.png")
    q.set_defaults(handler=cmd_acervo_indexar)
    q = acervo.add_parser("tag", help="acrescenta/remove tags (e muda tipo/projeto) de um item")
    q.add_argument("nome")
    q.add_argument("tags", nargs="*", help="tags a acrescentar")
    q.add_argument("--remover", action="append", default=[], help="tag a remover (pode repetir)")
    q.add_argument("--tipo", help="novo tipo")
    q.add_argument("--projeto", help="novo projeto de origem")
    q.set_defaults(handler=cmd_acervo_tag)
    q = acervo.add_parser("versoes", help="histórico de versões de um item")
    q.add_argument("nome")
    q.set_defaults(handler=cmd_acervo_versoes)
    p.set_defaults(handler=lambda args, config: (p.print_help(), 1)[1])


def _library(config: Config):
    from .library import Library

    return Library.from_config(config).load_or_scan()


def _entry_line(entry) -> str:
    size = f"{entry.tamanho[0]}x{entry.tamanho[1]}" if entry.tamanho else "—"
    frames = f", {entry.quadros} quadros" if entry.quadros > 1 else ""
    parent = f" ← {entry.herda}" if entry.herda else ""
    tags = f"  #{' #'.join(entry.tags)}" if entry.tags else ""
    project = f" [{entry.projeto}]" if entry.projeto else ""
    return f"{entry.nome:<22} {entry.tipo:<10} {size}{frames}{project}{parent}{tags}\n    {entry.arquivo}"


def cmd_acervo_listar(args, config: Config) -> int:
    import json

    found = _library(config).search(args.texto, args.tipo, args.tag, args.projeto)
    if args.json:
        print(json.dumps([e.to_dict() for e in found], ensure_ascii=False, indent=2))
        return 0
    for entry in found:
        print(_entry_line(entry))
    print(f"{len(found)} item(ns)")
    return 0


def cmd_acervo_indexar(args, config: Config) -> int:
    from .library import Library

    library = Library.from_config(config)
    warnings = library.scan(thumbnails=args.miniaturas)
    print(f"acervo: {len(library.entries)} item(ns) → {library.index_path}")
    for warning in warnings:
        print(f"  aviso: {warning}", file=sys.stderr)
    return 0


def cmd_acervo_tag(args, config: Config) -> int:
    library = _library(config)
    entry = library.tag(args.nome, args.tags, args.remover, args.tipo, args.projeto)
    print(_entry_line(entry))
    return 0


def cmd_acervo_versoes(args, config: Config) -> int:
    library = _library(config)
    for entry in library.versions(args.nome):
        mark = " ◀" if entry.nome == library.get(args.nome).nome else ""
        print(f"v{entry.versao}  {entry.nome}{mark}  ({entry.arquivo})")
    return 0


def cmd_studio(args, config: Config) -> int:
    from .studio import serve

    serve(config, args.porta, open_browser=args.abrir)
    return 0


def cmd_golden(args, config: Config) -> int:
    from .scene.golden import run

    out_dir = args.out or config.output_dir / "golden"
    results = run(args.manifest, config, record=args.regravar, out_dir=out_dir)
    for result in results:
        print(f"  {result.describe()}")
    bad = [r for r in results if r.status in ("diferente", "faltando")]
    if bad:
        print(f"erro: {len(bad)} de {len(results)} quadro(s) não batem; atuais e diffs em {out_dir}. "
              "Se a mudança é intencional: --regravar", file=sys.stderr)
        return 1
    print(f"{len(results)} quadro(s) {'gravados' if args.regravar else 'iguais às referências'}.")
    return 0


def cmd_mcp(args, config: Config) -> int:
    from .mcp_server import find_root, serve

    serve(find_root(args.raiz))
    return 0
