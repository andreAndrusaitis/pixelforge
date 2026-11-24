"""Subcomando `ia`: rascunho por IA local → pixel art de verdade.

  ia gerar "<descrição>" --preset retrato [--ref img] [--init img]
  ia pixelizar <imagem> --tamanho 128 --cores 24 [--paleta nome|arquivo]
  ia variar <spec|png>
  ia modelos [--baixar padrao|<chave>]

Saída em out/ia/<nome>/: <nome>_bruta.png (rascunho da IA), <nome>.png e
<nome>@8x.png (pixel art), <nome>.json (spec editável), <nome>_preview.png,
<nome>_comparar.png (rascunho × pixel) e <nome>_ia.json (tudo para reproduzir).
"""

from __future__ import annotations

import json
import random
import re
import time
import unicodedata
from pathlib import Path

import numpy as np
from PIL import Image, PngImagePlugin

from ..config import Config
from ..export import ExportOptions, export
from ..convert import portable_path
from ..pixelize import PixelizeOptions, comparison, pixelize
from ..sprite import SPEC_KEYS, SpecError, save_spec
from . import AIImageError
from . import models as catalog
from . import presets, style

SIDE = "_ia.json"


def add_ai_commands(sub) -> None:
    ia = sub.add_parser("ia", help="IA de imagem local: rascunho por IA → pixel art (gerar, pixelizar, variar)")
    ia.set_defaults(handler=lambda args, config: (ia.print_help(), 1)[1])
    cmds = ia.add_subparsers(title="comandos de IA de imagem")

    p = cmds.add_parser("gerar", help="gera o rascunho por IA e pixeliza")
    p.add_argument("descricao", help="o que desenhar (em inglês a IA entende melhor)")
    p.add_argument("--preset", help="preset de [ia.presets] (padrão: [ia] preset)")
    p.add_argument("--ref", type=Path, help="imagem de referência de personagem (IP-Adapter)")
    p.add_argument("--ref-tipo", choices=["plus", "face"], help="plus = corpo e roupa; face = rosto")
    p.add_argument("--ref-peso", type=float, help="força da referência (0–1; ~0,5)")
    p.add_argument("--init", type=Path, help="imagem → imagem: esboço por código, quadro ou foto")
    p.add_argument("--forca", type=float, help="imagem → imagem: 0 = igual à entrada, 1 = ignora (~0,55)")
    p.add_argument("--negativo", help="acrescenta termos ao negativo do preset")
    p.add_argument("--semente", type=int, default=-1, help="semente (padrão: sorteada e gravada)")
    p.add_argument("--quantas", type=int, default=1, help="nº de imagens (sementes seguidas)")
    p.add_argument("--passos", type=int)
    p.add_argument("--guia", type=float, help="CFG (Lightning: ~2)")
    p.add_argument("--lora-peso", type=float, help="peso do LoRA de pixel art (~0,8)")
    p.add_argument("--resolucao", help="resolução de geração LxA (múltiplos de 8)")
    p.add_argument("--sem-pixelizar", action="store_true", help="só o rascunho")
    _style_args(p)
    p.add_argument("--ciclo", action="store_true",
                   help="ciclo por notas: variações → pixeliza → `estilo comparar` → img2img nas piores métricas")
    p.add_argument("--ciclo-nota", type=float, default=90.0, help="nota técnica alvo do ciclo (padrão 90)")
    p.add_argument("--ciclo-voltas", type=int, default=4, help="voltas de img2img depois das variações (padrão 4)")
    p.add_argument("--ciclo-variacoes", type=int, default=4, help="sementes na 1ª volta (padrão 4)")
    _pixel_args(p)
    p.set_defaults(handler=cmd_generate)

    p = cmds.add_parser("pixelizar", help="imagem (de IA ou não) → pixel art: grade, paleta, limpeza")
    p.add_argument("imagem", type=Path)
    p.add_argument("--preset", help="preset de [ia.presets] (usa só a parte de pixelização)")
    _pixel_args(p)
    p.set_defaults(handler=cmd_pixelize)

    p = cmds.add_parser("variar", help="nova versão de uma geração (lê o <nome>_ia.json ao lado)")
    p.add_argument("arte", type=Path, help="spec .json, .png ou _ia.json de out/ia/<nome>/")
    p.add_argument("--semente", type=int, default=-1, help="padrão: sorteada")
    p.add_argument("--forca", type=float, default=0.45,
                   help="parte do rascunho que muda (0–1; padrão 0,45). 1 = nova composição")
    p.add_argument("--quantas", type=int, default=1)
    p.add_argument("--extra", default="", help="termos acrescentados ao prompt")
    p.add_argument("--nome", help="nome da saída (padrão: <nome>-v2, -v3...)")
    p.add_argument("--out", type=Path, help="pasta de saída (padrão: out/ia/<nome>/)")
    p.set_defaults(handler=cmd_vary)

    p = cmds.add_parser("folha", help="folha de revisão: arte + 3 referências do mesmo tipo + nota técnica")
    p.add_argument("arte", type=Path, help="spec .json ou .png em resolução nativa (saída de ia gerar/pixelizar)")
    p.add_argument("--preset", help="preset de [ia.presets] (tipo e referências dele)")
    p.add_argument("--tipo", choices=["retrato", "personagem", "cenario", "cena"])
    p.add_argument("--refs-estilo", help="referências a mostrar, ex.: 21,11,10 (padrão: as do preset ou as mais próximas)")
    p.add_argument("--out", type=Path, help="arquivo da folha (padrão: <arte>_folha.png ao lado)")
    p.set_defaults(handler=cmd_sheet)

    p = cmds.add_parser("retocar", help="retoque por código de uma spec (lista de operações em JSON)")
    p.add_argument("arte", type=Path, help="spec .json (saída de ia gerar/pixelizar)")
    p.add_argument("ops", type=Path, help='JSON: lista de operações ou {"retoque": [...]} (veja pixelforge/retouch.py)')
    p.add_argument("--nome", help="nome da saída (padrão: <arte>-r)")
    p.add_argument("--tipo", choices=["retrato", "personagem", "cenario", "cena"],
                   help="tipo para a nota técnica (padrão: o do _ia.json, se houver)")
    p.add_argument("--out", type=Path, help="pasta de saída (padrão: out/ia/<nome>/)")
    p.set_defaults(handler=cmd_retouch)

    p = cmds.add_parser("treinar", help="treina o LoRA de estilo local com as referências do autor")
    p.add_argument("--passos", type=int, default=1500, help="passos de treino (padrão 1500)")
    p.add_argument("--rank", type=int, default=16, help="rank do LoRA (padrão 16)")
    p.add_argument("--lr", type=float, default=1e-4, help="taxa de aprendizado (padrão 1e-4)")
    p.add_argument("--resolucao", type=int, default=768, help="lado de referência dos baldes (padrão 768)")
    p.add_argument("--com-ruidosas", action="store_true",
                   help="inclui as refs com ruído de IA (17, 24, 25, 31) com metade das repetições")
    p.add_argument("--so-dataset", action="store_true", help="só monta o dataset (imagens + legendas)")
    p.add_argument("--semente", type=int, default=0)
    p.add_argument("--out", type=Path, help="pasta do LoRA (padrão: models/pixelforge-estilo/)")
    p.set_defaults(handler=cmd_train)

    p = cmds.add_parser("modelos", help="lista os pesos (baixados ou não) e baixa os que faltam")
    p.add_argument("--baixar", nargs="+", metavar="CHAVE", help='"padrao" ou chaves do catálogo')
    p.set_defaults(handler=cmd_models)


def _style_args(p) -> None:
    p.add_argument("--refs-estilo", help="referências de estilo (IP-Adapter), ex.: 14,1,22 (padrão: as do preset)")
    p.add_argument("--sem-refs-estilo", action="store_true", help="não usa imagens de estilo")
    p.add_argument("--estilo-peso", type=float, help="força das imagens de estilo (0–1; ~0,6)")
    p.add_argument("--sem-lora-estilo", action="store_true", help="não usa o LoRA de estilo treinado")


def _pixel_args(p) -> None:
    p.add_argument("--tamanho", help='lado, LxA ou "auto" (= grade detectada)')
    p.add_argument("--cores", type=int, help="nº de cores do k-means OKLab")
    p.add_argument("--paleta", help="nome de paleta, .hex, ou .png/.json de uma arte (paleta da cena)")
    p.add_argument("--metodo", choices=["moda", "mediana"], help="redução por célula")
    p.add_argument("--grade", help='"auto", "none" ou a escala do pseudo-pixel em px')
    p.add_argument("--fundo", help='remover fundo: "auto" (cor dos cantos), #rrggbb, ou "" para manter')
    p.add_argument("--fundo-tolerancia", dest="fundo_tolerancia", type=int,
                   help="quanto uma cor pode diferir do fundo e ainda sair (0–255; ~20)")
    p.add_argument("--contorno", help='"seletivo", "auto", #rrggbb ou "" (sem)')
    p.add_argument("--limpeza", type=int, help="passadas de remoção de pixels órfãos")
    p.add_argument("--fundir", type=float, help="funde tons quase iguais (ΔE OKLab, ~0,04)")
    p.add_argument("--contraste", type=float)
    p.add_argument("--saturacao", type=float)
    p.add_argument("--nome", help="nome da saída")
    p.add_argument("--out", type=Path, help="pasta de saída (padrão: out/ia/<nome>/)")


# --------------------------------------------------------------------------
# Comum
# --------------------------------------------------------------------------


def slug(text: str, words: int = 5) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    parts = re.findall(r"[a-z0-9]+", plain)
    return "-".join(parts[:words]) or "ia"


def _pixel_values(args, values: dict) -> dict:
    """Preset + opções da linha de comando → dicionário de PixelizeOptions."""
    merged = dict(values)
    for key in ("tamanho", "cores", "paleta", "metodo", "grade", "fundo", "fundo_tolerancia", "contorno", "limpeza", "fundir",
                "contraste", "saturacao"):
        value = getattr(args, key, None)
        if value is not None:
            merged[key] = value
    return presets.pixel_options(merged)


def _out_dir(args, config: Config, name: str) -> Path:
    return Path(args.out) if getattr(args, "out", None) else config.output_dir / "ia" / name


def _export_options() -> ExportOptions:
    return ExportOptions(formats=["png"], scales=[1, 8], preview=True)


def pixelize_and_save(raw: Image.Image | Path, pixel: dict, name: str, out_dir: Path, config: Config,
                      record: dict | None = None, tipo: str = "", chosen: list[int] | None = None
                      ) -> tuple[list[Path], dict]:
    """Pixeliza, exporta PNG/preview/comparação/spec, dá a nota técnica (com `tipo`) e grava
    o _ia.json. Retorna (arquivos, registro)."""
    options = PixelizeOptions.from_dict(pixel)
    started = time.perf_counter()
    art = pixelize(raw, options, name=name, palette_dirs=config.palette_dirs)
    seconds = time.perf_counter() - started
    if record:
        art.meta["ia"] = {k: record[k] for k in ("descricao", "preset", "pedido") if k in record}
    written = export(art, out_dir, _export_options())
    source = raw if isinstance(raw, Image.Image) else Image.open(raw)
    path = out_dir / f"{name}_comparar.png"
    comparison(source, art).save(path)
    written.append(path)
    if len(art.colors()) <= len(SPEC_KEYS):
        written.append(save_spec(art, out_dir / f"{name}.json"))
    else:
        print(f"  aviso: {len(art.colors())} cores não cabem numa spec; só PNG", flush=True)
    record = dict(record or {})
    record.update({
        "nome": name,
        "pixelizacao": options.to_dict(),
        "grade": art.meta.get("grid"),
        "tamanho_final": list(art.size),
        "cores_finais": len(art.colors()),
    })
    record.setdefault("tempo", {})["pixelizacao_s"] = round(seconds, 2)
    if tipo:
        sheet, summary = review(art.frames[0].pixels, tipo, config, name, chosen)
        if sheet is not None:
            path = out_dir / f"{name}_folha.png"
            sheet.save(path)
            written.append(path)
            record["estilo"] = summary
    side = out_dir / f"{name}{SIDE}"
    side.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    written.append(side)
    return written, record


def review(rgba, tipo: str, config: Config, title: str, chosen: list[int] | None = None):
    """(folha arte + 3 refs, resumo da nota técnica). Sem as decomposições, (None, {})."""
    try:
        sheet, result = style.review_sheet(rgba, tipo, config, title, chosen)
    except (ValueError, FileNotFoundError) as exc:
        print(f"  aviso: sem nota técnica ({exc})", flush=True)
        return None, {}
    return sheet, summarize(result)


def summarize(result) -> dict:
    return {"tipo": result.tipo, "nota_tecnica": result.nota, "refs_folha": [r.n for r in result.nearest],
            "fora_da_faixa": [{"metrica": m.label, "chave": m.path, "valor": m.value, "faixa": [m.low, m.high],
                               "nota": round(m.score, 3), "peso": m.weight} for m in result.fora_da_faixa()]}


def _save_raw(image: Image.Image, path: Path, record: dict) -> Path:
    info = PngImagePlugin.PngInfo()
    info.add_text("pixelforge-ia", json.dumps(record.get("pedido", {}), ensure_ascii=False))
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, pnginfo=info)
    return path


def _report(name: str, written: list[Path], record: dict) -> None:
    size = record.get("tamanho_final")
    grid = record.get("grade")
    line = f"{name}:"
    if size:
        line += f" {size[0]}x{size[1]}, {record.get('cores_finais')} cores"
    if grid:
        line += f", grade {grid['scale']} px (confiança {grid['confidence']})"
    pedido = record.get("pedido")
    if pedido:
        line += f", semente {pedido['seed']}"
    tempo = record.get("tempo", {})
    if "geracao_s" in tempo:
        line += f", geração {tempo['geracao_s']} s"
    nota = record.get("estilo", {}).get("nota_tecnica")
    if nota is not None:
        line += f", nota técnica {nota}"
    print(line, flush=True)
    for path in written:
        print(f"  {path}", flush=True)


# --------------------------------------------------------------------------
# gerar / variar
# --------------------------------------------------------------------------


def style_inputs(args, config: Config, preset_name: str, values: dict) -> dict:
    """Imagens de estilo (refs do preset, nativas e reampliadas) e o LoRA de estilo, se treinado."""
    data = presets.settings(config)
    out: dict = {"style_refs": [], "style_numbers": [], "style_lora": "", "trigger": ""}
    numbers = (style.parse_numbers(args.refs_estilo) if getattr(args, "refs_estilo", None)
               else list(values.get("refs", [])))
    if numbers and not getattr(args, "sem_refs_estilo", False):
        cache = config.output_dir / "ia" / "_refs"
        cache.mkdir(parents=True, exist_ok=True)
        for ref in style.pick(config, numbers):
            path = cache / f"{ref.n}.png"
            if not path.is_file():
                style.native_image(ref.path).save(path)
            out["style_refs"].append(str(path))
        out["style_numbers"] = numbers
    lora = presets.style_lora_path(config)
    if lora and not getattr(args, "sem_lora_estilo", False):
        out["style_lora"], out["trigger"] = str(lora), data["gatilho"]
    return out


def _request_from(args, config: Config, values: dict, styling: dict | None = None) -> "object":
    from .generate import Request

    data = presets.settings(config)
    styling = styling or {"style_refs": [], "style_lora": "", "trigger": ""}
    negative = values.get("negativo", "")
    if getattr(args, "negativo", None):
        negative = ", ".join(p for p in (negative, args.negativo) if p)
    resolution = presets.resolution({"resolucao": args.resolucao} if getattr(args, "resolucao", None) else values)
    ref_kind = args.ref_tipo or values.get("ref_tipo") or data["ref_tipo"]
    return Request(
        prompt=presets.join_prompt(args.descricao, values.get("prompt", ""), styling["trigger"]),
        negative=negative,
        width=resolution[0], height=resolution[1],
        seed=args.semente,
        steps=args.passos or values.get("passos") or data["passos"],
        guidance=args.guia or values.get("guia") or data["guia"],
        model=data["modelo"], lora=data["lora"],
        lora_weight=args.lora_peso if args.lora_peso is not None else values.get("lora_peso", data["lora_peso"]),
        init=str(args.init) if args.init else "",
        strength=args.forca if args.forca is not None else values.get("forca", data["forca"]),
        ref=str(args.ref) if args.ref else "",
        ref_weight=args.ref_peso if args.ref_peso is not None else values.get("ref_peso", data["ref_peso"]),
        ref_kind=ref_kind, offload=data["offload"], precision=data.get("precisao", "fp8"),
        style_refs=styling["style_refs"],
        style_weight=(args.estilo_peso if getattr(args, "estilo_peso", None) is not None
                      else values.get("estilo_peso", data["estilo_peso"])),
        style_lora=styling["style_lora"], style_lora_weight=data["estilo_lora_peso"],
    )


def _run_generations(requests: list, names: list[str], out_dirs: list[Path], config: Config, base: Path,
                     pixel: dict | None, extra: dict, tipo: str = "", chosen: list[int] | None = None) -> int:
    from .generate import Engine

    engine = None
    for request, name, out_dir in zip(requests, names, out_dirs):
        if engine is None or not engine.accepts(request):
            engine = Engine.for_request(request, base)
            print(f"modelo carregado em {engine.load_seconds:.1f} s", flush=True)
        result = engine.run(request)
        record = {
            **extra,
            "pedido": result.request.to_dict(),
            "tempo": {"carregar_modelo_s": round(result.load_seconds, 1), "geracao_s": round(result.seconds, 1)},
            "ambiente": result.info,
        }
        raw_path = _save_raw(result.image, out_dir / f"{name}_bruta.png", record)
        if pixel is None:
            side = out_dir / f"{name}{SIDE}"
            side.write_text(json.dumps({"nome": name, **record}, ensure_ascii=False, indent=2), encoding="utf-8")
            _report(name, [raw_path, side], record)
            continue
        written, record = pixelize_and_save(result.image, pixel, name, out_dir, config, record, tipo, chosen)
        _report(name, [raw_path, *written], record)
    return 0


def _models_base(config: Config) -> Path:
    return catalog.models_dir(presets.settings(config)["modelos"], config.root)


def cmd_generate(args, config: Config) -> int:
    values = presets.preset(config, args.preset)
    preset_name = args.preset or presets.settings(config)["preset"]
    for path in (args.ref, args.init):
        if path and not Path(path).is_file():
            raise FileNotFoundError(f"imagem não encontrada: {path}")
    styling = style_inputs(args, config, preset_name, values)
    base_request = _request_from(args, config, values, styling)
    pixel = None if args.sem_pixelizar else _pixel_values(args, values)
    name = args.nome or slug(args.descricao)
    tipo = style.tipo_for(preset_name, values)
    extra = {"descricao": args.descricao, "preset": preset_name, "tipo": tipo,
             "refs_estilo": styling["style_numbers"], "lora_estilo": styling["style_lora"]}
    if args.ciclo:
        from .cycle import CycleOptions, run_cycle

        options = CycleOptions(target=args.ciclo_nota, rounds=args.ciclo_voltas, variations=args.ciclo_variacoes)
        return run_cycle(base_request, pixel or _pixel_values(args, values), name, _out_dir(args, config, name),
                         config, _models_base(config), tipo, styling["style_numbers"], extra, options)
    count = max(1, args.quantas)
    if count > 1 and base_request.seed < 0:
        base_request.seed = random.randrange(2 ** 31)
    requests, names, dirs = [], [], []
    for i in range(count):
        request = type(base_request)(**base_request.to_dict())
        if count > 1:
            request.seed = base_request.seed + i
        n = name if count == 1 else f"{name}-{i + 1}"
        requests.append(request)
        names.append(n)
        dirs.append(Path(args.out) / n if args.out and count > 1 else _out_dir(args, config, n))
    return _run_generations(requests, names, dirs, config, _models_base(config), pixel, extra, tipo,
                            styling["style_numbers"])


def find_record(path: Path) -> tuple[Path, dict]:
    """Acha o <nome>_ia.json de uma saída (spec, png, bruta, preview ou o próprio _ia.json)."""
    path = Path(path)
    if path.name.endswith(SIDE):
        side = path
    else:
        stem = re.sub(r"(_bruta|_preview|_comparar|@\d+x)$", "", path.stem)
        side = path.with_name(f"{stem}{SIDE}")
    if not side.is_file():
        raise FileNotFoundError(f"não achei {side.name} ao lado de {path} (variar precisa de uma saída de `ia gerar`)")
    return side, json.loads(side.read_text(encoding="utf-8"))


def _next_name(folder_root: Path, name: str) -> str:
    base = re.sub(r"-v\d+$", "", name)
    k = 2
    while (folder_root / f"{base}-v{k}").exists():
        k += 1
    return f"{base}-v{k}"


def cmd_vary(args, config: Config) -> int:
    from .generate import Request

    side, record = find_record(args.arte)
    if "pedido" not in record:
        raise ValueError(f"{side.name} não tem o pedido de geração (veio de `ia pixelizar`?)")
    raw = side.with_name(f"{record['nome']}_bruta.png")
    original = Request.from_dict(record["pedido"])
    pixel = record.get("pixelizacao")
    if pixel and pixel.get("size"):
        pixel = {**pixel, "size": list(pixel["size"])}
    root = args.out or config.output_dir / "ia"
    requests, names, dirs = [], [], []
    seed = args.semente if args.semente >= 0 else random.randrange(2 ** 31)
    for i in range(max(1, args.quantas)):
        request = Request.from_dict(original.to_dict())
        request.seed = seed + i
        if args.extra:
            request.prompt = presets.join_prompt(args.extra, request.prompt)
        if args.forca < 1:
            if not raw.is_file():
                raise FileNotFoundError(f"rascunho original não encontrado: {raw}")
            request.init, request.strength = str(raw), args.forca
        name = args.nome if args.nome and args.quantas == 1 else (
            f"{args.nome}-{i + 1}" if args.nome else _next_name(root, record["nome"]))
        names.append(name)
        dirs.append(Path(root) / name)
        dirs[-1].mkdir(parents=True, exist_ok=True)  # reserva o nome para o próximo _next_name
        requests.append(request)
    extra = {k: record[k] for k in ("descricao", "preset", "tipo", "refs_estilo", "lora_estilo") if k in record}
    extra["variacao_de"] = record["nome"]
    return _run_generations(requests, names, dirs, config, _models_base(config), pixel, extra,
                            record.get("tipo", ""), record.get("refs_estilo"))


# --------------------------------------------------------------------------
# pixelizar / modelos
# --------------------------------------------------------------------------


def cmd_pixelize(args, config: Config) -> int:
    values = presets.preset(config, args.preset) if args.preset else {}
    pixel = _pixel_values(args, values)
    if not args.imagem.is_file():
        raise FileNotFoundError(f"imagem não encontrada: {args.imagem}")
    name = args.nome or re.sub(r"_bruta$", "", args.imagem.stem)
    out_dir = _out_dir(args, config, name)
    record = {"origem": str(args.imagem), "preset": args.preset or ""}
    side = out_dir / f"{name}{SIDE}"
    if side.is_file():  # repixelizar uma geração: mantém o pedido e os tempos de geração
        previous = json.loads(side.read_text(encoding="utf-8"))
        record = {**previous, **({"preset": args.preset} if args.preset else {})}
    tipo = record.get("tipo") or (style.tipo_for(args.preset, values) if args.preset else "")
    written, record = pixelize_and_save(args.imagem, pixel, name, out_dir, config, record, tipo,
                                        record.get("refs_estilo") or values.get("refs"))
    _report(name, written, record)
    return 0


def cmd_sheet(args, config: Config) -> int:
    from ..artfile import load_art

    values = presets.preset(config, args.preset) if args.preset else {}
    tipo = args.tipo or (style.tipo_for(args.preset, values) if args.preset else "")
    if not tipo:
        raise ValueError("informe --tipo ou --preset")
    if args.arte.suffix.lower() in (".json", ".py"):
        rgba = load_art(args.arte).frames[0].pixels
    else:
        with Image.open(args.arte) as opened:
            rgba = np.array(opened.convert("RGBA"))
    chosen = style.parse_numbers(args.refs_estilo) if args.refs_estilo else values.get("refs")
    sheet, result = style.review_sheet(rgba, tipo, config, args.arte.stem, chosen)
    out = args.out or args.arte.with_name(f"{args.arte.stem}_folha.png")
    sheet.save(out)
    print(f"{args.arte.stem} ({tipo}): nota técnica {result.nota}/100, refs {', '.join(str(r.n) for r in result.nearest)}")
    for m in result.fora_da_faixa()[:6]:
        print(f"  fora da faixa: {m.label} = {m.value} (refs {m.low}–{m.high})")
    print(f"  {out}")
    return 0


def cmd_retouch(args, config: Config) -> int:
    from ..retouch import apply_ops
    from ..sprite import Art, load_spec

    art = load_spec(args.arte)
    data = json.loads(args.ops.read_text(encoding="utf-8"))
    ops = data["retoque"] if isinstance(data, dict) else data
    sprite = apply_ops(art.frames[0], ops)
    name = args.nome or f"{art.name}-r"
    out_dir = _out_dir(args, config, name)
    meta = dict(art.meta)
    meta["retoque"] = {"de": portable_path(args.arte), "operacoes": len(ops)}
    new = Art(name, [sprite], meta=meta)
    written = export(new, out_dir, _export_options())
    written.append(save_spec(new, out_dir / f"{name}.json"))
    tipo = args.tipo
    record: dict = {}
    try:
        _, record = find_record(args.arte)
    except FileNotFoundError:
        pass
    tipo = tipo or record.get("tipo", "")
    record = {**record, "nome": name, "retoque": {"de": str(args.arte), "ops": ops}}
    if tipo:
        sheet, summary = review(sprite.pixels, tipo, config, name, record.get("refs_estilo"))
        if sheet is not None:
            path = out_dir / f"{name}_folha.png"
            sheet.save(path)
            written.append(path)
            record["estilo"] = summary
    side = out_dir / f"{name}{SIDE}"
    side.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    written.append(side)
    record.update({"tamanho_final": list(new.size), "cores_finais": len(new.colors())})
    _report(name, written, record)
    return 0


def cmd_train(args, config: Config) -> int:
    from .train import TrainOptions, build_dataset, train

    options = TrainOptions(steps=args.passos, rank=args.rank, lr=args.lr, resolution=args.resolucao,
                           include_noisy=args.com_ruidosas, seed=args.semente)
    out = Path(args.out) if args.out else presets.style_lora_dir(config)
    dataset = build_dataset(config, out / "dataset", options)
    print(f"dataset: {len(dataset)} imagens em {out / 'dataset'}", flush=True)
    if args.so_dataset:
        return 0
    path, report = train(config, _models_base(config), dataset, out, options)
    print(f"LoRA de estilo: {path}")
    print(f"  {report['passos']} passos em {report['tempo_min']} min, VRAM pico {report['vram_pico_gb']} GB, "
          f"perda final {report['perda_final']}")
    return 0


def cmd_models(args, config: Config) -> int:
    base = _models_base(config)
    if args.baixar:
        keys = list(catalog.DEFAULT_SET) if args.baixar == ["padrao"] else args.baixar
        for key in keys:
            started = time.perf_counter()
            catalog.download(key, base)
            weights = catalog.get(key)
            print(f"{key}: {catalog.size_on_disk(weights, base) / 1e9:.2f} GB em "
                  f"{time.perf_counter() - started:.0f} s → {catalog.local_path(weights, base)}", flush=True)
        return 0
    print(f"pasta: {base}")
    total = 0
    for key, weights in catalog.CATALOG.items():
        size = catalog.size_on_disk(weights, base)
        total += size
        mark = "baixado" if catalog.is_downloaded(weights, base) else "—"
        default = " (padrão)" if key in catalog.DEFAULT_SET else ""
        print(f"{key:<26} {weights.kind:<10} {mark:<8} {size / 1e9:5.2f} GB  {weights.repo}{default}")
        print(f"    {weights.note}")
    print(f"total em disco: {total / 1e9:.2f} GB")
    return 0


__all__ = ["add_ai_commands", "AIImageError", "SpecError"]
