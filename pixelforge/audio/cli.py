"""Subcomandos `som`: efeito, musica, voz, ambiente, mix, info, instalar."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from . import music, sfx
from .mix import make_loop, render_plan_to_files
from .sfx import plain
from .wavio import DEFAULT_RATE, describe, write_wav


def add_audio_commands(sub) -> None:
    som = sub.add_parser("som", help="efeitos chiptune, música, voz, ambientes e mixagem")
    som.set_defaults(handler=lambda args, config: (som.print_help(), 1)[1])
    cmds = som.add_subparsers(title="comandos de som")

    p = cmds.add_parser("efeito", help="efeito chiptune por preset ou JSON de parâmetros")
    p.add_argument("fonte", nargs="?", help=f"preset ({', '.join(sfx.preset_names())}) ou arquivo .json")
    p.add_argument("--lista", action="store_true", help="lista os presets")
    p.add_argument("--todos", action="store_true", help="gera todos os presets")
    p.add_argument("--semente", type=int, default=0)
    p.add_argument("--variar", type=float, default=0.0, help="variação aleatória dos parâmetros (ex.: 0.15)")
    p.add_argument("--json", action="store_true", help="também grava os parâmetros usados (<nome>.json)")
    _common(p)
    p.set_defaults(handler=cmd_effect)

    p = cmds.add_parser("musica", help="trilha: .json do sequenciador ou descrição (IA, ACE-Step)")
    p.add_argument("fonte", help="arquivo .json (chiptune por código) ou descrição em texto")
    p.add_argument("--duracao", type=float, default=30.0, help="segundos (IA)")
    p.add_argument("--bpm", type=int, help="andamento sugerido (IA)")
    p.add_argument("--letra", default="", help="letra cantada (IA); vazio = instrumental")
    p.add_argument("--sem-lm", dest="lm", action="store_false", help="não usa o modelo de linguagem do ACE-Step")
    p.add_argument("--semente", type=int, default=0)
    p.add_argument("--loop", type=float, nargs="?", const=1.0, help="funde fim e começo (segundos de crossfade)")
    _common(p)
    p.set_defaults(handler=cmd_music)

    p = cmds.add_parser("voz", help="fala por IA (Kokoro, português do Brasil)")
    p.add_argument("texto")
    p.add_argument("--voz", help="pf_dora (padrão), pm_alex, pm_santa")
    p.add_argument("--velocidade", type=float, default=1.0)
    _common(p)
    p.set_defaults(handler=cmd_voice)

    p = cmds.add_parser("ambiente", help="ambiente/efeito por descrição (IA: AudioLDM2 ou Stable Audio Open)")
    p.add_argument("descricao", help='de preferência em inglês, ex.: "gentle rain on leaves, distant thunder"')
    p.add_argument("--duracao", type=float, default=8.0)
    p.add_argument("--modelo", choices=["audioldm2", "stable-audio"])
    p.add_argument("--passos", type=int, help="passos de difusão (padrão 100)")
    p.add_argument("--semente", type=int, default=0)
    p.add_argument("--loop", type=float, nargs="?", const=1.0, help="funde fim e começo (segundos de crossfade)")
    _common(p)
    p.set_defaults(handler=cmd_ambient)

    p = cmds.add_parser("mix", help="monta a faixa de um roteiro de áudio (.json) e junta ao MP4")
    p.add_argument("roteiro", type=Path)
    p.add_argument("--video", type=Path, help="MP4 que recebe o som (sobrepõe o do roteiro)")
    _common(p)
    p.set_defaults(handler=cmd_mix)

    p = cmds.add_parser("info", help="duração e nível de um WAV")
    p.add_argument("arquivos", nargs="+", type=Path)
    p.set_defaults(handler=cmd_info)

    p = cmds.add_parser("instalar", help="prepara um backend de IA (baixa código/ambiente)")
    p.add_argument("backend", choices=["musica"])
    p.set_defaults(handler=cmd_install)


def _common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--nome", help="nome do arquivo (sem extensão)")
    p.add_argument("--out", type=Path, help="pasta de saída (padrão: out/som/)")


def _settings(config) -> dict:
    defaults = {"taxa": DEFAULT_RATE, "modelos": "", "voz": "pf_dora", "ambiente_modelo": "audioldm2"}
    return {**defaults, **config.data.get("som", {})}


def _out_dir(args, config) -> Path:
    return args.out or config.output_dir / "som"


def _models(config) -> Path | None:
    value = _settings(config)["modelos"]
    return (config.root / value) if value else None


def slug(text: str, limit: int = 32) -> str:
    words = re.sub(r"[^a-z0-9]+", "-", plain(text)).strip("-")
    return (words[:limit].rstrip("-")) or "som"


def _done(path: Path, started: float | None = None) -> None:
    took = f" — gerado em {time.perf_counter() - started:.1f} s" if started is not None else ""
    print(f"{path}: {describe(path)}{took}")


def _guard(fn):
    """Erros de backend de IA viram mensagem curta (código 3), sem traceback."""
    def run(args, config):
        from .ai.common import BackendError
        try:
            return fn(args, config)
        except (BackendError, RuntimeError) as exc:
            print(f"erro: {exc}", file=sys.stderr)
            return 3
    return run


# --------------------------------------------------------------------------


def cmd_effect(args, config) -> int:
    if args.lista:
        for name in sfx.preset_names():
            effect = sfx.load_effect(name)
            waves = "+".join(plain(layer.onda) for layer in effect.layers)
            print(f"{name:<10} {effect.duration:.2f} s  {waves}")
        return 0
    sources = sfx.preset_names() if args.todos else [args.fonte]
    if sources == [None]:
        raise ValueError("informe um preset ou .json (ou --lista / --todos)")
    rate = int(_settings(config)["taxa"])
    for source in sources:
        effect = sfx.vary(sfx.load_effect(source), args.variar, args.semente)
        name = (args.nome if not args.todos and args.nome else effect.name)
        if args.variar and not args.nome:
            name = f"{name}_{args.semente}"
        started = time.perf_counter()
        path = write_wav(_out_dir(args, config) / f"{name}.wav", sfx.synth(effect, args.semente, rate), rate)
        _done(path, started)
        if args.json:
            spec = path.with_suffix(".json")
            spec.write_text(json.dumps(effect.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  parâmetros: {spec}")
    return 0


@_guard
def cmd_music(args, config) -> int:
    source = Path(args.fonte)
    out_dir = _out_dir(args, config)
    started = time.perf_counter()
    if source.suffix.lower() == ".json":
        song = music.load_song(source)
        rate = int(_settings(config)["taxa"])
        samples = music.render_song(song, rate, args.semente)
        if args.loop:
            samples = make_loop(samples, rate, args.loop)
        path = write_wav(out_dir / f"{args.nome or song.get('name', source.stem)}.wav", samples, rate)
        _done(path, started)
        return 0
    from .ai import music as ai_music
    from .wavio import read_wav
    path = out_dir / f"{args.nome or slug(args.fonte)}.wav"
    print(f"ACE-Step: gerando {args.duracao:.0f} s (a primeira vez baixa os modelos)…", flush=True)
    info = ai_music.generate(args.fonte, args.duracao, path, args.semente, args.bpm, args.letra, args.lm,
                             _models(config))
    samples, rate = read_wav(path)          # ACE-Step grava float; padroniza em PCM 16 bits
    write_wav(path, make_loop(samples, rate, args.loop) if args.loop else samples, rate)
    _done(path, started)
    print(f"  carga {info.get('load_seconds')} s, geração {info.get('seconds')} s, LM: {info.get('lm') or 'não'}")
    return 0


@_guard
def cmd_voice(args, config) -> int:
    from .ai import voice
    started = time.perf_counter()
    samples, rate = voice.speak(args.texto, args.voz or _settings(config)["voz"], args.velocidade, _models(config))
    path = write_wav(_out_dir(args, config) / f"{args.nome or slug(args.texto)}.wav", samples, rate)
    _done(path, started)
    return 0


@_guard
def cmd_ambient(args, config) -> int:
    from .ai import ambient
    started = time.perf_counter()
    model = args.modelo or _settings(config)["ambiente_modelo"]
    samples, rate = ambient.generate(args.descricao, args.duracao, model, args.semente, args.passos, _models(config))
    if args.loop:
        samples = make_loop(samples, rate, args.loop)
    path = write_wav(_out_dir(args, config) / f"{args.nome or slug(args.descricao)}.wav", samples, rate)
    _done(path, started)
    return 0


@_guard
def cmd_mix(args, config) -> int:
    if not args.roteiro.is_file():
        raise FileNotFoundError(f"arquivo não encontrado: {args.roteiro}")
    plan = json.loads(args.roteiro.read_text(encoding="utf-8"))
    plan.setdefault("name", args.roteiro.stem)
    if args.nome:
        plan["name"] = args.nome
    if args.video:
        plan["video"] = str(args.video.resolve())
    started = time.perf_counter()
    paths = render_plan_to_files(plan, _out_dir(args, config), args.roteiro.parent)
    _done(paths[0], started)
    for extra in paths[1:]:
        print(f"  vídeo: {extra}")
    return 0


def cmd_info(args, config) -> int:
    for path in args.arquivos:
        print(f"{path}: {describe(path)}")
    return 0


@_guard
def cmd_install(args, config) -> int:
    from .ai import music as ai_music
    root = ai_music.install(_models(config))
    print(f"ACE-Step pronto em {root} (os pesos baixam na primeira geração)")
    return 0
