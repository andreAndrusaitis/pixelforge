"""Subcomandos `estilo`: analisar (decomposição técnica) e comparar (nota técnica)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

IMAGE_EXT = {".png", ".webp", ".jpg", ".jpeg", ".gif"}


def refs_dir(config) -> Path:
    env = os.environ.get("PIXELFORGE_REFS")
    return Path(env) if env else config.root / "refs" / "estilo-referencias"


def style_dir(config) -> Path:
    return config.root / "docs" / "estilo"


def add_style_commands(sub) -> None:
    estilo = sub.add_parser("estilo", help="decomposição técnica de referências e nota de uma arte contra elas")
    estilo.set_defaults(handler=lambda args, config: (estilo.print_help(), 1)[1])
    cmds = estilo.add_subparsers(title="comandos de estilo")

    p = cmds.add_parser("analisar", help="decompõe imagem(ns): grade, paleta, valor, clusters, contorno, luz, composição")
    p.add_argument("alvos", nargs="*", type=Path, help="imagens ou pastas (vazio com --refs)")
    p.add_argument("--refs", action="store_true", help="analisa todas as referências do índice e grava em docs/estilo/analises/")
    p.add_argument("--nativa", action="store_true", help="a imagem já está em resolução nativa (não detecta grade)")
    p.add_argument("--out", type=Path, help="pasta das folhas de decomposição (padrão: out/estilo/)")
    p.set_defaults(handler=cmd_analisar)

    p = cmds.add_parser("comparar", help="nota técnica 0–100 de uma arte contra as referências do mesmo tipo")
    p.add_argument("arte", type=Path, help="spec .json, script .py ou imagem")
    p.add_argument("--tipo", required=True, choices=["retrato", "personagem", "cenario", "cena"])
    p.add_argument("--nativa", action="store_true", help="imagem já em resolução nativa (specs e scripts sempre são)")
    p.add_argument("--quadro", type=int, default=0, help="quadro da animação a avaliar")
    p.add_argument("--out", type=Path, help="pasta da folha lado a lado (padrão: out/estilo/comparar/)")
    p.add_argument("--json", action="store_true", help="imprime o resultado em JSON")
    p.set_defaults(handler=cmd_comparar)


def _targets(args, config) -> list[tuple[Path, Path | None]]:
    """(imagem, json de saída ou None)."""
    if args.refs:
        index = json.loads((style_dir(config) / "referencias.json").read_text(encoding="utf-8"))
        rd = refs_dir(config)
        out = []
        for item in index["itens"]:
            img = rd / item["arquivo"]
            if not img.is_file():
                print(f"aviso: referência {item['n']} não encontrada em {rd}")
                continue
            out.append((img, style_dir(config) / "analises" / f"{item['n']}.json"))
        return out
    files: list[Path] = []
    for t in args.alvos:
        if t.is_dir():
            files += sorted(f for f in t.iterdir() if f.suffix.lower() in IMAGE_EXT)
        else:
            files.append(t)
    if not files:
        raise ValueError("informe imagens/pastas ou use --refs")
    return [(f, None) for f in files]


def cmd_analisar(args, config) -> int:
    from .analyze import analyze_file
    from .sheet import build_sheet

    out_dir = args.out or config.output_dir / "estilo"
    out_dir.mkdir(parents=True, exist_ok=True)
    for img, json_out in _targets(args, config):
        metrics, extras = analyze_file(img, native=args.nativa)
        sheet = out_dir / f"{img.stem}_decomposicao.png"
        build_sheet(metrics, extras).save(sheet)
        if json_out:
            json_out.parent.mkdir(parents=True, exist_ok=True)
            json_out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        p, c = metrics["paleta"], metrics["clusters"]
        w, h = metrics["tamanho_nativo"]
        print(f"{img.name}: nativa {w}x{h} (x{metrics['grade']['escala']}), {p['cores_efetivas']} cores, "
              f"blocos {c['tamanho_medio']} px, contraste {metrics['valor']['contraste']}, luz {metrics['luz']['de_onde']}")
        print(f"  {sheet}" + (f"\n  {json_out}" if json_out else ""))
    return 0


def _art_native(path: Path, frame: int, native_flag: bool) -> tuple[np.ndarray, bool]:
    if path.suffix.lower() in (".json", ".py"):
        from ..artfile import load_art

        art = load_art(path)
        return art.frames[min(frame, len(art.frames) - 1)].pixels, True
    from PIL import Image

    with Image.open(path) as im:
        return np.array(im.convert("RGBA")), native_flag


def cmd_comparar(args, config) -> int:
    from .analyze import analyze_array, to_native
    from .compare import comparison_sheet, load_references, score

    refs = load_references(style_dir(config) / "referencias.json", style_dir(config) / "analises")
    if len(refs) < 5:
        raise ValueError("faltam as decomposições das referências: rode `estilo analisar --refs` antes")
    rgba, native = _art_native(args.arte, args.quadro, args.nativa)
    metrics, extras = analyze_array(rgba, native=native)
    same = args.arte.name if args.arte.resolve().parent == refs_dir(config).resolve() else None
    result = score(metrics, refs, args.tipo, exclude=same)
    out_dir = args.out or config.output_dir / "estilo" / "comparar"
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet = out_dir / f"{args.arte.stem}_comparar.png"
    comparison_sheet(extras["native"], result, refs_dir(config), args.arte.stem).save(sheet)
    if args.json:
        print(json.dumps({**result.as_dict(), "folha": str(sheet)}, ensure_ascii=False, indent=2))
        return 0
    print(f"{args.arte.name} ({args.tipo}): nota técnica {result.nota}/100")
    print(f"  referências mais próximas: {', '.join(str(r.n) for r in result.nearest)}")
    for s in result.fora_da_faixa()[:8]:
        print(f"  fora da faixa: {s.label} = {s.value} (refs {s.low}–{s.high})")
    print(f"  {sheet}")
    return 0
