"""`ia gerar --ciclo`: gera, pixeliza, dá nota (`estilo comparar`) e corrige até a nota técnica alvo.

Volta 0: N sementes (texto → imagem). Cada rascunho é pixelizado com as opções do
preset e com variações delas guiadas pelas métricas fora da faixa (cores,
contraste, limpeza — ajustes baratos, sem GPU); fica a melhor nota.
Voltas 1..R: as K melhores viram imagem → imagem (força ~0,4, semente nova) com
o prompt e o negativo corrigidos pelas métricas fora da faixa; a pixelização
corrige o que é dela. Para quando a nota técnica chega ao alvo (padrão 90).
A nota final ≥ 95 é do agente `critico-de-arte` (rubrica visual + nota técnica).

Saída: a melhor em out/ia/<nome>/ (como `ia gerar`), as tentativas em
out/ia/<nome>/ciclo/, a evolução das notas em <nome>_ciclo.json e <nome>_ciclo.png.
"""

from __future__ import annotations

import gc
import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

from ..config import Config
from ..pixelize import PixelizeOptions, pixelize
from . import presets, style


@dataclass
class CycleOptions:
    target: float = 90.0
    rounds: int = 4
    variations: int = 4
    keep: int = 2
    strength: float = 0.4


# métrica (chave de pixelforge.style.compare) → correções quando está abaixo / acima da faixa.
# Cada correção: ("prompt", termos) | ("negativo", termos) | ("pixel", campo, delta)
FIXES: dict[str, dict[str, list[tuple]]] = {
    "paleta.cores_efetivas": {"baixo": [("pixel", "colors", +6)],
                              "alto": [("pixel", "colors", -4), ("prompt", "limited palette")]},
    "paleta.croma_media": {"baixo": [("pixel", "saturation", +0.15), ("prompt", "one saturated accent color")],
                           "alto": [("pixel", "saturation", -0.15), ("prompt", "desaturated muted colors")]},
    "paleta.variacao_media_graus": {"baixo": [("prompt", "hue shifted shading, violet shadows, warm highlights")],
                                    "alto": [("prompt", "coherent color ramps")]},
    "paleta.tons_por_rampa": {"baixo": [("pixel", "colors", +4)], "alto": [("pixel", "colors", -4)]},
    "valor.niveis": {"baixo": [("pixel", "colors", +4)], "alto": [("pixel", "colors", -3)]},
    "valor.contraste": {"baixo": [("pixel", "contrast", +0.12), ("prompt", "strong value contrast, deep shadows")],
                        "alto": [("pixel", "contrast", -0.1), ("prompt", "soft value range")]},
    "valor.desvio": {"baixo": [("pixel", "contrast", +0.08)], "alto": [("pixel", "contrast", -0.08)]},
    "clusters.tamanho_medio": {"baixo": [("pixel", "merge", +0.02), ("pixel", "cleanup", +1),
                                         ("prompt", "large flat pixel clusters, simple shapes")],
                               "alto": [("pixel", "merge", -0.015), ("prompt", "more small details")]},
    "clusters.orfaos": {"alto": [("pixel", "cleanup", +1), ("pixel", "merge", +0.02),
                                 ("negativo", "noisy pixels, pixel noise")],
                        "baixo": [("pixel", "cleanup", -1)]},
    "clusters.densidade_detalhe": {"baixo": [("prompt", "detailed clothing folds")],
                                   "alto": [("prompt", "simple shapes"), ("pixel", "merge", +0.01)]},
    "clusters.dithering": {"alto": [("negativo", "dithering, checkerboard pattern"), ("pixel", "merge", +0.02)]},
    "contorno.escuro": {"alto": [("negativo", "black outline")], "baixo": [("prompt", "dark selective outline")]},
    "contorno.ausente": {"baixo": [("negativo", "thick black outline")]},
    "luz_de_borda.fracao": {"baixo": [("prompt", "1px rim light")], "alto": [("negativo", "glowing edges")]},
    "luz.forca": {"baixo": [("prompt", "strong directional side light")], "alto": [("prompt", "soft ambient light")]},
    "composicao.espaco_negativo": {"alto": [("prompt", "subject fills the frame")],
                                   "baixo": [("prompt", "empty space around the subject")]},
    "composicao.dist_tercos": {"baixo": [("prompt", "off-center composition, rule of thirds")],
                               "alto": [("prompt", "centered subject")]},
    "figura.proporcao_cabecas": {"baixo": [("prompt", "realistic proportions, small head")],
                                 "alto": [("prompt", "bigger head")]},
    "figura.altura_px": {"baixo": [("prompt", "tall figure filling the frame height")],
                         "alto": [("prompt", "full figure with margin")]},
}

PIXEL_FIELDS = {"colors": (2, 64), "saturation": (0.5, 1.6), "contrast": (0.7, 1.6), "merge": (0.0, 0.12),
                "cleanup": (0, 4)}


def corrections(result, limit: int = 4) -> list[tuple]:
    """Correções das piores métricas fora da faixa (ponderadas pelo peso)."""
    out = []
    for m in result.fora_da_faixa()[:limit]:
        side = "baixo" if m.value < m.low else "alto"
        out += [(m.path, side, fix) for fix in FIXES.get(m.path, {}).get(side, [])]
    return out


def tweak_pixel(pixel: dict, fixes: list[tuple]) -> dict:
    out = dict(pixel)
    defaults = PixelizeOptions()
    for _, _, fix in fixes:
        if fix[0] != "pixel":
            continue
        _, key, delta = fix
        lo, hi = PIXEL_FIELDS[key]
        value = out.get(key, getattr(defaults, key)) + delta
        out[key] = type(getattr(defaults, key))(min(hi, max(lo, value)))
    return out


def tweak_prompt(prompt: str, negative: str, fixes: list[tuple]) -> tuple[str, str, list[str]]:
    adds, negs = [], []
    for _, _, fix in fixes:
        if fix[0] == "prompt":
            adds.append(fix[1])
        elif fix[0] == "negativo":
            negs.append(fix[1])
    adds = list(dict.fromkeys(adds))
    negs = list(dict.fromkeys(negs))
    new_prompt = ", ".join([prompt, *adds]) if adds else prompt
    new_negative = ", ".join([n for n in (*negs, negative) if n])
    return new_prompt, new_negative, adds + [f"-{n}" for n in negs]


@dataclass
class Attempt:
    label: str
    raw: str
    seed: int
    strength: float
    nota: float
    pixel: dict
    request: dict
    fixes: list[str] = field(default_factory=list)
    result: object = None
    art: object = None


def evaluate(raw: Image.Image | Path, pixel: dict, tipo: str, config: Config, refs) -> tuple[float, dict, object, object]:
    """Melhor pixelização entre as opções do preset e as corrigidas pelas métricas (sem GPU)."""
    def attempt(opts: dict):
        art = pixelize(raw, PixelizeOptions.from_dict(opts), palette_dirs=config.palette_dirs)
        result, _ = style.score_pixels(art.frames[0].pixels, tipo, config, refs)
        return result.nota, opts, result, art

    best = attempt(pixel)
    for _ in range(3):  # corrige enquanto a nota sobe
        opts = tweak_pixel(best[1], corrections(best[2]))
        if opts == best[1]:
            break
        candidate = attempt(opts)
        if candidate[0] <= best[0]:
            break
        best = candidate
    return best


def run_cycle(request, pixel: dict, name: str, out_dir: Path, config: Config, base: Path, tipo: str,
              chosen: list[int] | None, extra: dict, options: CycleOptions) -> int:
    from . import cli
    from .generate import Engine, Request

    refs = style.references(config)
    work = out_dir / "ciclo"
    work.mkdir(parents=True, exist_ok=True)
    engine = None
    attempts: list[Attempt] = []
    history: list[dict] = []

    def run(req: Request, label: str) -> Attempt:
        nonlocal engine
        if engine is None or not engine.accepts(req):
            engine = None
            gc.collect()
            engine = Engine.for_request(req, base)
            print(f"modelo carregado em {engine.load_seconds:.1f} s", flush=True)
        res = engine.run(req)
        raw = work / f"{label}_bruta.png"
        res.image.save(raw)
        nota, opts, result, art = evaluate(res.image, pixel, tipo, config, refs)
        attempt = Attempt(label, str(raw), res.request.seed, req.strength if req.init else 1.0, nota, opts,
                          res.request.to_dict(), [], result, art)
        art.frames[0].to_image().resize((art.size[0] * 4, art.size[1] * 4), Image.Resampling.NEAREST).save(
            work / f"{label}.png")
        print(f"  {label}: nota técnica {nota} (semente {res.request.seed}, geração {res.seconds:.0f} s)", flush=True)
        history.append({"tentativa": label, "nota": nota, "semente": res.request.seed,
                        "forca": attempt.strength, "geracao_s": round(res.seconds, 1),
                        "pixelizacao": {k: opts[k] for k in ("colors", "saturation", "contrast", "merge", "cleanup")
                                        if k in opts},
                        "fora_da_faixa": [m.label for m in result.fora_da_faixa()[:5]]})
        return attempt

    seed0 = request.seed if request.seed >= 0 else random.randrange(2 ** 31)
    for i in range(max(1, options.variations)):
        req = Request.from_dict({**request.to_dict(), "seed": seed0 + i})
        attempts.append(run(req, f"v0-{i + 1}"))
    best = sorted(attempts, key=lambda a: -a.nota)[:options.keep]

    for r in range(1, options.rounds + 1):
        if best[0].nota >= options.target:
            break
        new = []
        for k, parent in enumerate(best):
            fixes = corrections(parent.result)
            prompt, negative, notes = tweak_prompt(request.prompt, request.negative, fixes)
            req = Request.from_dict({**request.to_dict(), "prompt": prompt, "negative": negative,
                                     "init": parent.raw, "strength": options.strength,
                                     "seed": seed0 + 100 * r + k})
            attempt = run(req, f"v{r}-{k + 1}")
            attempt.fixes = notes
            history[-1]["de"] = parent.label
            history[-1]["correcoes"] = notes
            new.append(attempt)
        attempts += new
        best = sorted(best + new, key=lambda a: -a.nota)[:options.keep]

    winner = best[0]
    engine = None
    gc.collect()
    record = {**extra, "pedido": winner.request, "ciclo": {
        "alvo": options.target, "melhor": winner.label, "nota_final": winner.nota,
        "evolucao": history, "opcoes": asdict(options),
        "observacao": "nota técnica de `estilo comparar`; a aprovação (≥ 95) é do critico-de-arte"}}
    with Image.open(winner.raw) as opened:
        raw = opened.convert("RGB")
    written, record = cli.pixelize_and_save(raw, winner.pixel, name, out_dir, config, record, tipo, chosen)
    raw.save(out_dir / f"{name}_bruta.png")
    path = out_dir / f"{name}_ciclo.json"
    path.write_text(json.dumps(record["ciclo"], ensure_ascii=False, indent=2), encoding="utf-8")
    sheet = evolution_sheet(attempts, winner, options.target)
    sheet.save(out_dir / f"{name}_ciclo.png")
    cli._report(name, [out_dir / f"{name}_bruta.png", *written, path, out_dir / f"{name}_ciclo.png"], record)
    print(f"  ciclo: {len(attempts)} tentativas, melhor {winner.label} com nota técnica {winner.nota}"
          f" (alvo {options.target}{', atingido' if winner.nota >= options.target else ', não atingido'})")
    return 0


def evolution_sheet(attempts: list[Attempt], winner: Attempt, target: float, cell: int = 200) -> Image.Image:
    """Todas as tentativas lado a lado por volta, com a nota (a vencedora marcada)."""
    rounds: dict[str, list[Attempt]] = {}
    for a in attempts:
        rounds.setdefault(a.label.split("-")[0], []).append(a)
    cols = max(len(v) for v in rounds.values())
    sheet = Image.new("RGB", (cols * (cell + 10) + 70, len(rounds) * (cell + 30) + 10), (24, 20, 37))
    d = ImageDraw.Draw(sheet)
    for row, (key, items) in enumerate(rounds.items()):
        y = 10 + row * (cell + 30)
        d.text((8, y + cell // 2), key, fill=(234, 228, 214))
        for col, a in enumerate(items):
            img = a.art.frames[0].to_image()
            s = max(1, min(cell // img.width, cell // img.height))
            img = img.resize((img.width * s, img.height * s), Image.Resampling.NEAREST)
            x = 60 + col * (cell + 10)
            sheet.paste(img, (x + (cell - img.width) // 2, y + 18), img)
            color = (120, 220, 140) if a is winner else ((255, 205, 117) if a.nota >= target else (200, 190, 200))
            d.text((x, y + 2), f"{a.label}  nota {a.nota}" + ("  *" if a is winner else ""), fill=color)
    return sheet
