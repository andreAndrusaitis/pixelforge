"""Comandos do motor de arte (personagem, animação, paleta, sombra, lint, tiles, Aseprite).

Registrados no fim de `cli.build_parser` por `add_art_commands`.

  character  folha de personagem → sprite + retrato + animações (+ specs para a cena)
  animate    gera animações (parado, piscar, falar, andar) a partir de uma pose parada
  recolor    troca de paleta: mapas nomeados, tintas (noite, por-do-sol...), rampas
  shade      sombreamento e contorno automáticos a partir de arte chapada
  lint       aponta problemas de pixel art com coordenadas
  tileset    gera folha de tiles com autotile (blob 47 / 16)
  tilemap    monta um mapa a partir de grade de caracteres
  aseprite   exporta sheet + JSON do Aseprite, ou importa .ase/.aseprite/.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import Config
from .sprite import Art, save_spec


def _load_art(path: Path) -> Art:
    # load_art pode morar em cli.py ou em artfile.py (refatoração em andamento)
    try:
        from .artfile import load_art  # type: ignore[attr-defined]
    except ImportError:
        from .cli import load_art
    return load_art(path)


def _export(art: Art, out_dir: Path, args, config: Config) -> list[Path]:
    from .cli import export_options
    from .export import export

    return export(art, out_dir, export_options(args, config))


def _report(art: Art, paths: list[Path]) -> None:
    from .cli import _report as report

    report(art, paths)


def add_art_commands(sub) -> None:
    from .cli import add_export_args

    p = sub.add_parser("character", aliases=["personagem"],
                       help="folha de personagem → sprite, retrato e animações")
    p.add_argument("model", type=Path, help="modelo do personagem (ex.: art/personagens/ana.personagem.json)")
    p.add_argument("--variante", action="append", default=[], help="variante do modelo (pode repetir)")
    p.add_argument("--paleta", help="paleta nomeada do modelo (ex.: uniforme de uma casa)")
    p.add_argument("--mapa", help="tinta depois de desenhar: noite, por-do-sol, fantasma, sepia")
    p.add_argument("--name", help="nome de saída (padrão: nome do modelo + variantes)")
    p.add_argument("--spec-dir", type=Path, help="onde gravar as specs (padrão: pasta do modelo)")
    p.add_argument("--no-spec", dest="spec", action="store_false", help="não grava as specs .json")
    p.add_argument("--aseprite", action="store_true", help="também grava .aseprite em camadas")
    add_export_args(p)
    p.set_defaults(handler=cmd_character)

    p = sub.add_parser("animate", aliases=["animar"], help="gera animações a partir da pose parada")
    p.add_argument("art", type=Path)
    p.add_argument("--hip", type=int, help="linha do quadril (andar/respirar); padrão: estimado")
    p.add_argument("--chest", type=int, help="linha até onde o corpo desce ao respirar")
    p.add_argument("--eyes", help='pixels dos olhos para piscar, ex.: "12,10 15,10"')
    p.add_argument("--mouth", help="boca para falar: x,y,largura,altura")
    p.add_argument("--mouth-color", help="cor da boca aberta (padrão: a mais escura da região)")
    p.add_argument("--walk", type=int, choices=[0, 4, 6], default=4, help="quadros do andar (0 = sem)")
    p.add_argument("--split", type=int, help="coluna que separa a perna de trás da da frente")
    p.add_argument("--no-idle", dest="idle", action="store_false", help="sem respiração no parado")
    p.add_argument("--to-spec", type=Path, help="grava a spec com animations + anchor neste arquivo")
    add_export_args(p)
    p.set_defaults(handler=cmd_animate)

    p = sub.add_parser("recolor", help="troca de paleta (mapas, tintas, rampas)")
    p.add_argument("art", type=Path)
    p.add_argument("--map", dest="map_name", help="nome do mapa (de --maps) ou tinta: noite, por-do-sol, ...")
    p.add_argument("--maps", type=Path, help="arquivo JSON de mapas {\"mapas\": {nome: {\"#de\": \"#para\"}}}")
    p.add_argument("--swap", action="append", default=[], help='"#de:#para" (pode repetir); leva a rampa junto')
    p.add_argument("--exact", action="store_true", help="troca só a cor exata, sem a rampa")
    p.add_argument("--palette", help="força as cores para uma paleta (ex.: gameboy)")
    p.add_argument("--name", help="nome de saída (padrão: <nome>_<mapa>)")
    p.add_argument("--to-spec", type=Path, help="grava a spec recolorida (preserva animations/anchor)")
    p.add_argument("--ramps", action="store_true", help="só lista a rampa automática de cada cor da arte")
    add_export_args(p)
    p.set_defaults(handler=cmd_recolor)

    p = sub.add_parser("shade", aliases=["sombrear"], help="sombra e contorno automáticos em arte chapada")
    p.add_argument("art", type=Path)
    p.add_argument("--light", default="cima-esquerda", help="direção da luz (cima-esquerda, cima, direita...)")
    p.add_argument("--shadow", type=float, default=0.6, help="limiar de sombra 0–1 (maior = menos sombra)")
    p.add_argument("--highlight", type=float, default=0.2, help="limiar de luz 0–1 (maior = mais brilho)")
    p.add_argument("--outline", default="selout", help='selout, auto, #rrggbb ou "nenhum"')
    p.add_argument("--keep", action="append", default=[], help="cor que não recebe sombra (pode repetir)")
    p.add_argument("--name", help="nome de saída (padrão: <nome>_sombra)")
    p.add_argument("--to-spec", type=Path, help="grava a spec sombreada")
    add_export_args(p)
    p.set_defaults(handler=cmd_shade)

    p = sub.add_parser("lint", help="aponta problemas de pixel art com coordenadas")
    p.add_argument("files", nargs="+", type=Path)
    p.add_argument("--checks", help="lista: orfao,contorno,cores,banding,jaggies,contraste")
    p.add_argument("--max-colors", type=int, help="limite de cores (padrão: pelo tamanho)")
    p.add_argument("--bg", action="append", default=[], help="fundo para o teste de contraste (pode repetir)")
    p.add_argument("--json", action="store_true", help="saída em JSON")
    p.add_argument("--strict", action="store_true", help="código de saída 1 se houver problema")
    p.set_defaults(handler=cmd_lint)

    p = sub.add_parser("tileset", help="gera folha de tiles com autotile")
    p.add_argument("tileset", type=Path)
    add_export_args(p)
    p.set_defaults(handler=cmd_tileset)

    p = sub.add_parser("tilemap", aliases=["mapa"], help="monta mapa a partir de grade de caracteres")
    p.add_argument("map", type=Path)
    add_export_args(p)
    p.set_defaults(handler=cmd_tilemap)

    p = sub.add_parser("aseprite", help="exporta sheet + JSON (Godot/Unity) ou importa .ase/.json")
    p.add_argument("action", choices=["export", "import"])
    p.add_argument("file", type=Path)
    p.add_argument("--layout", choices=["linhas", "horizontal"], default="linhas")
    p.add_argument("--scale", type=int, default=1, help="escala da folha exportada")
    p.add_argument("--ase", action="store_true", help="export: também grava .aseprite")
    p.add_argument("--to-spec", type=Path, help="import: grava a spec .json (com animations)")
    p.add_argument("--out", type=Path, help="pasta de saída (padrão: out/<nome>/)")
    p.set_defaults(handler=cmd_aseprite, formats=None, scales=None, preview=None)


# --------------------------------------------------------------------------


def cmd_character(args, config: Config) -> int:
    from .animate import export_animations
    from .aseprite import art_to_ase
    from .character import LAYERS, build_portrait, build_sprite, load_model, model_name, model_sheet
    from .recolor import recolor

    model = load_model(args.model, args.variante, args.paleta)
    suffix = "".join(f"_{v}" for v in args.variante) + (f"_{args.paleta}" if args.paleta else "") \
        + (f"_{args.mapa}" if args.mapa else "")
    name = args.name or model_name(args.model) + suffix
    model.name = name
    sprite, sprite_layers = build_sprite(model)
    portrait, portrait_layers = build_portrait(model)
    if args.mapa:
        sprite = recolor(sprite, tint=args.mapa)
        portrait = recolor(portrait, tint=args.mapa)
    sheet = Art(name, [model_sheet(model, sprite, portrait)])
    out_dir = args.out or config.output_dir / name
    paths = _export(sheet, out_dir, args, config)
    sprite_sheet = Art(f"{name}_sprite", sprite.frames, sprite.fps, sprite.meta)
    paths += _export(sprite_sheet, out_dir, _no_preview(args), config)
    paths += _export(Art(f"{name}_retrato", portrait.frames, portrait.fps), out_dir, _no_preview(args), config)
    paths += export_animations(sprite, out_dir)
    paths += export_animations(portrait, out_dir)
    if args.spec:
        spec_dir = args.spec_dir or args.model.parent
        paths.append(save_spec(sprite, spec_dir / f"{name}.json"))
        paths.append(save_spec(portrait, spec_dir / f"{name}_retrato.json"))
    if args.aseprite:
        paths.append(art_to_ase(sprite, out_dir / f"{name}.aseprite", sprite_layers, LAYERS))
        paths.append(art_to_ase(portrait, out_dir / f"{name}_retrato.aseprite", portrait_layers, LAYERS))
    anims = ", ".join(sprite.meta["animations"])
    print(f"{name}: sprite {sprite.size[0]}x{sprite.size[1]} ({len(sprite.frames)} quadros), "
          f"retrato {portrait.size[0]}x{portrait.size[1]} ({len(model.expressions)} expressões)")
    print(f"  animações: {anims}")
    for path in paths:
        print(f"  {path}")
    if model.style == "pintado":
        _painted_review(sprite, portrait, config)
    return 0


def _painted_review(sprite: Art, portrait: Art, config: Config) -> None:
    """Estilo pintado: mede a nota técnica contra as referências e lembra o ciclo do crítico."""
    import numpy as np

    try:
        from .style.analyze import analyze_array
        from .style.cli import style_dir
        from .style.compare import load_references, score
    except ImportError:
        return
    refs = load_references(style_dir(config) / "referencias.json", style_dir(config) / "analises")
    if len(refs) < 5:
        print("  (sem decomposições das referências: rode `estilo analisar --refs` para medir a nota técnica)")
        return
    for label, art, tipo in (("sprite", sprite, "personagem"), ("retrato", portrait, "retrato")):
        metrics, _ = analyze_array(np.array(art.frames[0].pixels), native=True)
        result = score(metrics, refs, tipo)
        print(f"  nota técnica do {label}: {result.nota}/100 (refs próximas: "
              f"{', '.join(str(r.n) for r in result.nearest)})")
    print("  estilo pintado: passe pelo ciclo do crítico antes de entregar "
          "(agente critico-de-arte, NOTA ≥ 95 e nenhum critério < 8; docs/agentes.md)")


def _no_preview(args):
    clone = argparse.Namespace(**vars(args))
    clone.preview = False
    return clone


def cmd_animate(args, config: Config) -> int:
    from .animate import export_animations, generate, parse_points, validate_animations

    art = _load_art(args.art)
    mouth = tuple(int(v) for v in args.mouth.split(",")) if args.mouth else None
    if mouth is not None and len(mouth) != 4:
        raise ValueError("--mouth deve ser x,y,largura,altura")
    builder = generate(art.frames[0], idle=args.idle, chest=args.chest, eyes=parse_points(args.eyes) if args.eyes else None,
                       mouth=mouth, mouth_color=args.mouth_color, hip=args.hip, walk_frames=args.walk, split=args.split)
    meta = {k: v for k, v in art.meta.items() if k not in ("animations", "anchor")}
    result = builder.art(art.name, anchor=art.meta.get("anchor"), meta=meta, fps=art.fps)
    validate_animations(result)
    out_dir = args.out or config.output_dir / art.name
    paths = _export(result, out_dir, args, config) + export_animations(result, out_dir)
    if args.to_spec:
        paths.append(save_spec(result, args.to_spec))
    _report(result, paths)
    print(f"  animações: {', '.join(result.meta['animations'])}; âncora {result.meta['anchor']}")
    return 0


def cmd_recolor(args, config: Config) -> int:
    from . import palettes as pal
    from .recolor import TINTS, load_maps, parse_swaps, ramp, recolor

    art = _load_art(args.art)
    if args.ramps:
        for color in art.colors():
            print(f"  {pal.to_hex(color)}: {' '.join(pal.to_hex(c) for c in ramp(color))}")
        return 0
    swaps = parse_swaps(args.swap)
    tint = None
    if args.map_name:
        if args.maps:
            maps = load_maps(args.maps)
            if args.map_name not in maps:
                raise KeyError(f"mapa '{args.map_name}' não está em {args.maps}. Disponíveis: {', '.join(maps)}")
            swaps += parse_swaps(maps[args.map_name])
        elif args.map_name in TINTS:
            tint = args.map_name
        else:
            raise KeyError(f"mapa '{args.map_name}': use --maps arquivo.json ou uma tinta: {', '.join(TINTS)}")
    palette = pal.get(args.palette, config.palette_dirs) if args.palette else None
    if not (swaps or tint or palette):
        raise ValueError("informe --map, --swap ou --palette")
    name = args.name or f"{art.name}_{args.map_name or args.palette or 'recolor'}"
    result = recolor(art, name, swaps=swaps, tint=tint, palette=palette, keep_ramps=not args.exact)
    out_dir = args.out or config.output_dir / name
    paths = _export(result, out_dir, args, config)
    if args.to_spec:
        paths.append(save_spec(result, args.to_spec))
    _report(result, paths)
    return 0


def cmd_shade(args, config: Config) -> int:
    from .shading import auto_shade, outline

    art = _load_art(args.art)
    frames = [outline(auto_shade(f, args.light, args.shadow, args.highlight, keep=args.keep), args.outline)
              for f in art.frames]
    result = Art(args.name or f"{art.name}_sombra", frames, art.fps, dict(art.meta))
    out_dir = args.out or config.output_dir / result.name
    paths = _export(result, out_dir, args, config)
    if args.to_spec:
        paths.append(save_spec(result, args.to_spec))
    _report(result, paths)
    return 0


def cmd_lint(args, config: Config) -> int:
    from . import palettes as pal
    from .lint import CHECKS, lint_art, lint_report

    checks = [c.strip() for c in args.checks.split(",")] if args.checks else list(CHECKS)
    total = 0
    report = {}
    for file in args.files:
        art = _load_art(file)
        backgrounds = {bg: pal.parse_color(bg) for bg in args.bg} or None
        issues = lint_art(art, checks, args.max_colors, backgrounds)
        total += len(issues)
        if args.json:
            report[str(file)] = [i.to_dict() for i in issues]
        else:
            print(f"{file}: {len(issues)} problema(s)")
            text = lint_report(issues)
            print("\n".join(f"  {line}" for line in text.splitlines()))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    return 1 if args.strict and total else 0


def cmd_tileset(args, config: Config) -> int:
    from .tiles import load_tileset, tileset_sheet

    ts = load_tileset(args.tileset)
    sheet, index = tileset_sheet(ts)
    art = Art(ts.name, [sheet])
    out_dir = args.out or config.output_dir / ts.name
    paths = _export(art, out_dir, args, config)
    idx_path = Path(out_dir) / f"{ts.name}_tiles.json"
    idx_path.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    paths.append(idx_path)
    _report(art, paths)
    for name, t in ts.terrains.items():
        print(f"  terreno {name}: {t.mode}, {len(t.tiles)} tiles")
    return 0


def cmd_tilemap(args, config: Config) -> int:
    from .tiles import load_map, render_map

    tm = load_map(args.map)
    art = Art(tm.name, [render_map(tm)])
    out_dir = args.out or config.output_dir / tm.name
    _report(art, _export(art, out_dir, args, config))
    return 0


def cmd_aseprite(args, config: Config) -> int:
    from .aseprite import art_to_ase, export_sheet, read_ase, read_sheet_json

    if args.action == "export":
        art = _load_art(args.file)
        out_dir = args.out or config.output_dir / art.name
        png, js = export_sheet(art, out_dir, layout=args.layout, scale=args.scale)
        print(f"{art.name}: folha + JSON do Aseprite")
        print(f"  {png}\n  {js}")
        if args.ase:
            print(f"  {art_to_ase(art, Path(out_dir) / f'{art.name}.aseprite')}")
        return 0
    suffix = args.file.suffix.lower()
    if suffix in (".ase", ".aseprite"):
        art = read_ase(args.file)
    elif suffix == ".json":
        art = read_sheet_json(args.file)
    else:
        raise ValueError(f"{args.file}: use .ase, .aseprite ou o .json exportado pelo Aseprite")
    out_dir = args.out or config.output_dir / art.name
    from .export import ExportOptions, export

    out = config.data["output"]
    paths = export(art, out_dir, ExportOptions(formats=["png"], scales=list(out["scales"]), preview=True))
    if args.to_spec:
        art.meta.pop("aseprite", None)
        paths.append(save_spec(art, args.to_spec))
    _report(art, paths)
    if "animations" in art.meta:
        print(f"  animações: {', '.join(art.meta['animations'])}")
    return 0
