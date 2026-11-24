"""Lint de pixel art: aponta problemas comuns com coordenadas.

Verificações (cada uma devolve `Issue`s):
  orfao       pixel isolado de tom quase igual ao redor (sujeira, não detalhe)
  contorno    falha no contorno da silhueta (quando a arte tem contorno)
  cores       cores demais para o tamanho, ou tons quase idênticos
  banding     faixas de tons paralelas acompanhando a borda (degrau de 1 px repetido)
  jaggies     degraus irregulares em curvas/diagonais (ex.: 3-1-3)
  contraste   silhueta que some contra fundo claro ou escuro
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass

import numpy as np

from .color import srgb_to_oklab
from .palettes import RGBA, to_hex
from .process import _N4, _N8, _shifted
from .sprite import Art, Sprite

CHECKS = ("orfao", "contorno", "cores", "banding", "jaggies", "contraste")
# fundo padrão do teste de contraste: cinza médio (cenário típico); use --bg para outros
BACKGROUNDS = {"médio": (128, 128, 128, 255)}


@dataclass
class Issue:
    check: str
    message: str
    x: int | None = None
    y: int | None = None
    frame: int = 0
    severity: str = "aviso"  # aviso | erro

    def __str__(self) -> str:
        where = f" ({self.x}, {self.y})" if self.x is not None else ""
        frame = f" frame {self.frame}" if self.frame else ""
        return f"[{self.severity}] {self.check}{frame}{where}: {self.message}"

    def to_dict(self) -> dict:
        return asdict(self)


def _lab(color) -> np.ndarray:
    return srgb_to_oklab(np.array(color[:3]))


def _delta(a, b) -> float:
    return float(np.sqrt(((_lab(a) - _lab(b)) ** 2).sum()))


def _px(sprite: Sprite, x: int, y: int) -> RGBA:
    return tuple(int(v) for v in sprite.pixels[y, x])  # type: ignore[return-value]


# --------------------------------------------------------------------------


def check_orphans(sprite: Sprite, max_delta: float = 0.12) -> list[Issue]:
    """Órfão = sem vizinho ortogonal igual, cercado (>= 6 de 8) por um tom parecido.

    Pixels de alto contraste (olho, brilho) são considerados intencionais.
    """
    issues = []
    h, w = sprite.height, sprite.width
    for y in range(h):
        for x in range(w):
            here = _px(sprite, x, y)
            if here[3] == 0:
                continue
            neigh = [_px(sprite, x + dx, y + dy) if 0 <= x + dx < w and 0 <= y + dy < h else (0, 0, 0, 0)
                     for dx, dy in _N8]
            if any(n == here for n in neigh[:4]):
                continue
            color, count = Counter(neigh).most_common(1)[0]
            if count >= 6 and color[3] > 0 and _delta(here, color) < max_delta:
                issues.append(Issue("orfao", f"pixel {to_hex(here)} isolado em {to_hex(color)}", x, y))
    return issues


def outline_color(sprite: Sprite) -> RGBA | None:
    """Cor do contorno: a mais comum na borda da silhueta, se for escura e dominante."""
    opaque = sprite.pixels[..., 3] > 0
    edge = opaque & ~(_shifted(opaque, 0, -1) & _shifted(opaque, 0, 1) & _shifted(opaque, -1, 0) & _shifted(opaque, 1, 0))
    colors = [tuple(int(v) for v in sprite.pixels[y, x]) for y, x in zip(*np.nonzero(edge))]
    if len(colors) < 8:
        return None
    color, count = Counter(colors).most_common(1)[0]
    if count / len(colors) < 0.6 or _lab(color)[0] > 0.5:
        return None
    return color


def check_outline(sprite: Sprite) -> list[Issue]:
    color = outline_color(sprite)
    if color is None:
        return []
    opaque = sprite.pixels[..., 3] > 0
    edge = opaque & ~(_shifted(opaque, 0, -1) & _shifted(opaque, 0, 1) & _shifted(opaque, -1, 0) & _shifted(opaque, 1, 0))
    issues = []
    target = np.array(color, dtype=np.uint8)
    for y, x in zip(*np.nonzero(edge)):
        if not np.array_equal(sprite.pixels[y, x], target):
            # aceita tons escuros parecidos (selout) — só acusa cor clara/média na borda
            if _lab(sprite.pixels[y, x])[0] > _lab(color)[0] + 0.25:
                issues.append(Issue("contorno", f"falha no contorno ({to_hex(_px(sprite, x, y))} na borda; "
                                                f"contorno é {to_hex(color)})", int(x), int(y)))
    return issues


def max_colors_for(sprite: Sprite) -> int:
    side = max(sprite.width, sprite.height)
    return 16 if side <= 32 else 32 if side <= 64 else 64


def check_colors(sprite: Sprite, limit: int | None = None, min_delta: float = 0.025) -> list[Issue]:
    colors = sprite.colors()
    limit = limit or max_colors_for(sprite)
    issues = []
    if len(colors) > limit:
        issues.append(Issue("cores", f"{len(colors)} cores (recomendado até {limit} neste tamanho)"))
    labs = [_lab(c) for c in colors]
    for i in range(len(colors)):
        for j in range(i + 1, len(colors)):
            if np.sqrt(((labs[i] - labs[j]) ** 2).sum()) < min_delta:
                issues.append(Issue("cores", f"{to_hex(colors[i])} e {to_hex(colors[j])} são quase iguais; funda as duas"))
    return issues


def check_banding(sprite: Sprite, min_length: int = 4) -> list[Issue]:
    """Faixa de 1 px de um tom intermediário entre dois outros, repetida na mesma
    posição relativa por `min_length` linhas/colunas seguidas (degraus paralelos)."""
    issues = []
    for transposed in (False, True):
        pixels = sprite.pixels.transpose(1, 0, 2) if transposed else sprite.pixels
        h, w = pixels.shape[:2]
        found: list[tuple[int, int, tuple]] = []  # (linha, coluna, (a, b, c))
        for y in range(h):
            row = pixels[y]
            for x in range(1, w - 1):
                a, b, c = (tuple(int(v) for v in row[x + d]) for d in (-1, 0, 1))
                if a[3] == 0 or b[3] == 0 or c[3] == 0 or len({a, b, c}) < 3:
                    continue
                la, lb, lc = (_lab(v)[0] for v in (a, b, c))
                if (la > lb > lc) or (la < lb < lc):
                    found.append((y, x, (a, b, c)))
        by_key: dict[tuple, list[tuple[int, int]]] = {}
        for y, x, key in found:
            by_key.setdefault(key, []).append((y, x))
        for key, cells in by_key.items():
            cells.sort()
            # sequência de linhas consecutivas onde a faixa se desloca de 1 px a cada linha
            # (diagonal: min_length; reta: min_length + 2, pois listras retas às vezes são intencionais)
            best: list[tuple[int, int]] = []
            cell_set = set(cells)
            for start in cells:
                for step in (-1, 0, 1):
                    chain = [start]
                    while (chain[-1][0] + 1, chain[-1][1] + step) in cell_set:
                        chain.append((chain[-1][0] + 1, chain[-1][1] + step))
                    need = min_length + (2 if step == 0 else 0)
                    if len(chain) >= need and len(chain) > len(best):
                        best = chain
            if best:
                y, x = best[0]
                px, py = (y, x) if transposed else (x, y)
                issues.append(Issue("banding", f"faixa de {to_hex(key[1])} acompanhando a borda por {len(best)} "
                                               f"{'colunas' if transposed else 'linhas'} (degraus paralelos)", px, py))
    return _dedupe(issues)


def _edge_profile(opaque: np.ndarray, side: str) -> list[int | None]:
    """x da borda esquerda/direita por linha (ou y de cima/baixo por coluna)."""
    out: list[int | None] = []
    for line in opaque:
        idx = np.nonzero(line)[0]
        if not len(idx):
            out.append(None)
        else:
            out.append(int(idx[0] if side == "start" else idx[-1]))
    return out


def check_jaggies(sprite: Sprite) -> list[Issue]:
    """Analisa os degraus das bordas da silhueta: num trecho que sobe/desce sempre
    1 px por degrau, um degrau bem menor que os vizinhos (3-1-3) é um jaggy."""
    opaque = sprite.pixels[..., 3] > 0
    issues = []
    for transposed in (False, True):
        grid = opaque.T if transposed else opaque
        for side in ("start", "end"):
            prof = _edge_profile(grid, side)
            # runs: (valor, início, comprimento) em sequências contíguas
            runs: list[tuple[int, int, int]] = []
            for i, v in enumerate(prof):
                if v is None:
                    runs.append((-999, i, 0))
                elif runs and runs[-1][0] == v and runs[-1][1] + runs[-1][2] == i:
                    runs[-1] = (v, runs[-1][1], runs[-1][2] + 1)
                else:
                    runs.append((v, i, 1))
            for a, b, c in zip(runs, runs[1:], runs[2:]):
                if min(a[2], b[2], c[2]) == 0:
                    continue
                step1, step2 = b[0] - a[0], c[0] - b[0]
                if abs(step1) != 1 or step1 != step2:
                    continue
                if b[2] == 1 and min(a[2], c[2]) >= 3:
                    line = b[1]
                    x, y = (line, b[0]) if transposed else (b[0], line)
                    issues.append(Issue("jaggies", f"degrau irregular {a[2]}-{b[2]}-{c[2]} na borda", x, y))
    return _dedupe(issues)


def check_contrast(sprite: Sprite, backgrounds: dict[str, RGBA] | None = None, min_delta: float = 0.12,
                   max_fraction: float = 0.5) -> list[Issue]:
    opaque = sprite.pixels[..., 3] > 0
    edge = opaque & ~(_shifted(opaque, 0, -1) & _shifted(opaque, 0, 1) & _shifted(opaque, -1, 0) & _shifted(opaque, 1, 0))
    if not edge.any() or opaque.all():
        return []
    lum = srgb_to_oklab(sprite.pixels[edge][:, :3].astype(float))[:, 0]
    issues = []
    for name, bg in (backgrounds or BACKGROUNDS).items():
        bl = _lab(bg)[0]
        weak = np.abs(lum - bl) < min_delta
        if weak.mean() > max_fraction:
            ys, xs = np.nonzero(edge)
            i = int(np.argmax(weak))
            issues.append(Issue("contraste", f"{weak.mean():.0%} da silhueta quase some sobre fundo {name} "
                                             f"({to_hex(bg)}); escureça/clareie o contorno",
                                int(xs[i]), int(ys[i])))
    return issues


def _dedupe(issues: list[Issue]) -> list[Issue]:
    seen, out = set(), []
    for issue in issues:
        key = (issue.check, issue.x, issue.y)
        if key not in seen:
            seen.add(key)
            out.append(issue)
    return out


def lint_sprite(sprite: Sprite, checks=CHECKS, max_colors: int | None = None,
                backgrounds: dict[str, RGBA] | None = None) -> list[Issue]:
    unknown = [c for c in checks if c not in CHECKS]
    if unknown:
        raise ValueError(f"verificação desconhecida: {', '.join(unknown)}. Use: {', '.join(CHECKS)}")
    runners = {
        "orfao": lambda: check_orphans(sprite),
        "contorno": lambda: check_outline(sprite),
        "cores": lambda: check_colors(sprite, max_colors),
        "banding": lambda: check_banding(sprite),
        "jaggies": lambda: check_jaggies(sprite),
        "contraste": lambda: check_contrast(sprite, backgrounds),
    }
    out: list[Issue] = []
    for name in checks:
        out.extend(runners[name]())
    return out


def lint_art(art: Art, checks=CHECKS, max_colors: int | None = None,
             backgrounds: dict[str, RGBA] | None = None) -> list[Issue]:
    issues: list[Issue] = []
    if "cores" in checks:
        merged = Sprite(np.concatenate([f.pixels for f in art.frames], axis=1))
        issues.extend(check_colors(merged, max_colors or max_colors_for(art.frames[0])))
    per_frame = [c for c in checks if c != "cores"]
    seen: set[tuple] = set()
    for i, frame in enumerate(art.frames):
        for issue in lint_sprite(frame, per_frame, max_colors, backgrounds):
            key = (issue.check, issue.x, issue.y)
            if key in seen:  # mesmo problema no mesmo lugar em outro quadro: reporta uma vez
                continue
            seen.add(key)
            issue.frame = i
            issues.append(issue)
    return issues


def lint_report(issues: list[Issue], limit: int = 12) -> str:
    """Texto legível: agrupado por verificação, no máximo `limit` linhas cada."""
    if not issues:
        return "nenhum problema encontrado"
    lines = []
    for check in CHECKS:
        group = [i for i in issues if i.check == check]
        if not group:
            continue
        lines.append(f"{check}: {len(group)}")
        for issue in group[:limit]:
            lines.append(f"  {issue}")
        if len(group) > limit:
            lines.append(f"  ... e mais {len(group) - limit}")
    return "\n".join(lines)
