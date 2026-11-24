"""Folha de personagem: um modelo JSON → retrato, sprite de corpo e animações.

O modelo guarda o que não pode mudar entre artes (cores, proporções, estilo de
cabelo, roupa, acessórios). Tudo é desenhado chapado por material, em camadas,
e depois sombreado (`shading.shade_regions`) e contornado — então o rosto e o
corpo saem sempre iguais, em qualquer pose, vista ou expressão.

Formato (chaves em português; só `tipo` e `name` são obrigatórias):

    {
      "tipo": "personagem",
      "name": "lia",
      "tamanho": [32, 32],              sprite de corpo (pé na última linha)
      "retrato": 48,                    lado do retrato (40–96)
      "idade": "adulto",                crianca | adulto | idoso
      "proporcoes": {"altura": 30, "cabeca": 13, "tronco": 9, "ombros": 10},
      "cores": {"pele": "#e8b796", "cabelo": "#5a3a29", "olhos": "#3b5dc9",
                "roupa": "#b13e53", "roupa2": "#f4f4f4", "calca": "#333c57",
                "sapato": "#4a2f2a", "acessorio": "#ffcd75", "boca": "#a8484f"},
                (opcionais: "capa", "chapeu", "oculos"; sem elas, usam "acessorio"/tinta escura)
      "rampas": {"pele": ["#luz", "#base", "#sombra", "#escuro"]},
      "contorno": "selout",             selout | #rrggbb | nenhum
      "luz": "cima-esquerda",
      "camadas": {
        "cabelo": {"estilo": "rabo", "franja": "lado", "volume": 1},
        "roupa": {"estilo": "casaco", "mangas": "longas"},
        "pernas": {"estilo": "calca"},
        "acessorios": ["cachecol", "oculos"],
        "marcas": ["cicatriz"],
        "barba": "nenhuma"
      },
      "expressoes": ["neutro", "feliz", "bravo", "triste", "surpreso"],
      "andar": 4,
      "paletas": {"casa_azul": {"roupa": "#3b5dc9"}},
      "variantes": {"inverno": {"camadas": {"acessorios": ["cachecol"]}}},
      "extras": [{"nome": "broche", "vistas": ["frente", "retrato"], "presa_a": "tronco",
                  "pos": [2, 1], "grade": ["y"], "paleta": {"y": "#ffcd75"}}]
    }
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .animate import Builder
from .palettes import RGBA, parse_color
from .recolor import from_lch, merge_close, shade, to_lch
from .shading import parse_light, selout, shade_regions
from .process import outline as solid_outline
from .sprite import Art, Sprite

HAIR_STYLES = ("curto", "longo", "rabo", "coque", "espetado", "cacheado", "careca")
FRINGES = ("reta", "lado", "repartida", "nenhuma")
OUTFITS = ("camisa", "casaco", "vestido", "manto")
SLEEVES = ("longas", "curtas", "sem")
LEGWEAR = ("calca", "short", "saia")
ACCESSORIES = ("oculos", "chapeu", "cachecol", "capa", "cinto")
MARKS = ("cicatriz", "sardas", "rugas")
BEARDS = ("nenhuma", "cheia", "bigode", "cavanhaque")
EXPRESSIONS = ("neutro", "feliz", "bravo", "triste", "surpreso")
AGES = ("crianca", "adulto", "idoso")
STYLES = ("simples", "pintado")   # pintado: nível das referências (docs/estilo/guia-visual.md)
VIEWS = ("direita", "frente", "costas")
SHADOW = 0.68  # limiar de sombra (0–1): maior = menos área sombreada
LAYERS = ("capa", "cabelo_tras", "corpo", "roupa", "rosto", "cabelo", "acessorio", "contorno")

DEFAULT_COLORS = {
    "pele": "#e8b796", "cabelo": "#5a3a29", "olhos": "#3b5dc9", "roupa": "#b13e53",
    "roupa2": "#f4f4f4", "calca": "#333c57", "sapato": "#4a2f2a", "acessorio": "#ffcd75",
    "boca": "#a8484f",
}

# parte do desenho → camada (para exportar em camadas e trocar partes)
PART_LAYER = {
    "capa": "capa", "cabelo_tras": "cabelo_tras",
    "cabeca": "corpo", "orelha": "corpo", "pescoco": "corpo", "braco": "corpo", "mao": "corpo",
    "perna": "corpo",
    "tronco": "roupa", "manga": "roupa", "calca": "roupa", "saia": "roupa", "sapato": "roupa",
    "gola": "roupa", "cinto": "roupa",
    "cabelo": "cabelo", "barba": "cabelo",
    "chapeu": "acessorio", "cachecol": "acessorio",
}
# quem projeta sombra em quem (pixel logo abaixo / ao lado, do lado da luz)
CASTS = {
    "cabeca": {"cabelo", "chapeu"}, "orelha": {"cabelo"}, "pescoco": {"cabeca", "barba", "cabelo"},
    "tronco": {"cachecol", "braco", "manga", "cabelo"}, "cabelo": {"chapeu"},
    "perna": {"tronco", "saia"}, "calca": {"tronco"},
}


class ModelError(ValueError):
    pass


# --------------------------------------------------------------------------
# Modelo
# --------------------------------------------------------------------------


def deep_merge(base: dict, override: dict) -> dict:
    """Mescla dicionários; listas e valores simples são substituídos."""
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


@dataclass
class Model:
    name: str
    size: tuple[int, int] = (32, 32)
    portrait: int = 48
    age: str = "adulto"
    proportions: dict = field(default_factory=dict)
    colors: dict[str, RGBA] = field(default_factory=dict)
    ramps: dict[str, list[RGBA]] = field(default_factory=dict)
    outline: str = "selout"
    style: str = "simples"
    light: tuple[int, int] = (-1, -1)
    hair: dict = field(default_factory=lambda: {"estilo": "curto", "franja": "reta", "volume": 0})
    outfit: dict = field(default_factory=lambda: {"estilo": "camisa", "mangas": "curtas"})
    legs: dict = field(default_factory=lambda: {"estilo": "calca"})
    accessories: list[str] = field(default_factory=list)
    marks: list[str] = field(default_factory=list)
    beard: str = "nenhuma"
    expressions: list[str] = field(default_factory=lambda: list(EXPRESSIONS))
    walk_frames: int = 4
    extras: list[dict] = field(default_factory=list)
    data: dict = field(default_factory=dict)

    # -- cores --------------------------------------------------------------

    def color(self, material: str) -> RGBA:
        if material not in self.colors:
            fallback = {"capa": "acessorio", "chapeu": "acessorio", "gola": "roupa2"}.get(material)
            if fallback and fallback in self.colors:
                return self.colors[fallback]
            raise ModelError(f"cor '{material}' não definida em 'cores'")
        return self.colors[material]

    def ramp(self, material: str) -> list[RGBA]:
        """[luz, base, sombra, escuro]."""
        if material in self.ramps:
            r = list(self.ramps[material])
            while len(r) < 4:
                r.append(shade(r[-1], -1))
            return r[:4]
        base = self.color(material)
        return [shade(base, 1), base, shade(base, -1), shade(base, -2)]

    def edge(self, material: str) -> RGBA:
        """Tom do contorno seletivo para o material. Tons muito escuros e parecidos
        viram um só (evita "cores quase iguais" no contorno)."""
        tone = shade(self.ramp(material)[-1], -1.5)
        L, C, h = to_lch(tone)
        if L < 0.3:
            return from_lch(0.2, min(C, 0.04), h if C > 0.02 else 300.0)
        return tone

    @property
    def ink(self) -> RGBA:
        """Tinta escura do rosto (cílios, olhos do sprite), derivada do cabelo."""
        L, C, h = to_lch(self.color("cabelo"))
        return from_lch(min(L - 0.22, 0.24), C * 0.7, h)


def parse_model(data: dict, default_name: str = "personagem") -> Model:
    if data.get("tipo") not in (None, "personagem"):
        raise ModelError("'tipo' deve ser \"personagem\"")
    name = data.get("name") or default_name
    style = data.get("estilo", "simples")
    if style not in STYLES:
        raise ModelError(f"'estilo' deve ser um de: {', '.join(STYLES)}")
    painted = style == "pintado"
    size = data.get("tamanho", [64, 104] if painted else [32, 32])
    if isinstance(size, int):
        size = [size, size]
    if len(size) != 2 or min(size) < 16:
        raise ModelError("'tamanho' deve ser [largura, altura] com lados >= 16")
    portrait = int(data.get("retrato", 112 if painted else 48))
    if not 40 <= portrait <= 128:
        raise ModelError("'retrato' deve ficar entre 40 e 128")
    age = data.get("idade", "adulto")
    if age not in AGES:
        raise ModelError(f"'idade' deve ser uma de: {', '.join(AGES)}")

    colors = {k: parse_color(v) for k, v in DEFAULT_COLORS.items()}
    for key, value in (data.get("cores") or {}).items():
        try:
            colors[key] = parse_color(value)
        except ValueError as exc:
            raise ModelError(f"cores['{key}']: {exc}") from None
    if age == "idoso" and not data.get("cabelo_original"):
        L, C, h = to_lch(colors["cabelo"])
        colors["cabelo"] = from_lch(max(L, 0.72), C * 0.25, h)
    ramps = {}
    for key, values in (data.get("rampas") or {}).items():
        if not isinstance(values, list) or len(values) < 2:
            raise ModelError(f"rampas['{key}']: lista de 2–4 cores, da clara para a escura")
        ramps[key] = [parse_color(v) for v in values]

    layers = data.get("camadas") or {}
    hair = {"estilo": "curto", "franja": "reta", "volume": 0, **(layers.get("cabelo") or {})}
    outfit = {"estilo": "camisa", "mangas": "curtas", **(layers.get("roupa") or {})}
    legs = {"estilo": "calca", **(layers.get("pernas") or {})}
    checks = [
        ("camadas.cabelo.estilo", hair["estilo"], HAIR_STYLES),
        ("camadas.cabelo.franja", hair["franja"], FRINGES),
        ("camadas.roupa.estilo", outfit["estilo"], OUTFITS),
        ("camadas.roupa.mangas", outfit["mangas"], SLEEVES),
        ("camadas.pernas.estilo", legs["estilo"], LEGWEAR),
        ("camadas.barba", layers.get("barba", "nenhuma"), BEARDS),
    ]
    for where, value, allowed in checks:
        if value not in allowed:
            raise ModelError(f"{where} = {value!r}; use: {', '.join(allowed)}")
    accessories = list(layers.get("acessorios") or [])
    marks = list(layers.get("marcas") or [])
    for where, items, allowed in (("acessorios", accessories, ACCESSORIES), ("marcas", marks, MARKS)):
        bad = [i for i in items if i not in allowed]
        if bad:
            raise ModelError(f"camadas.{where}: {', '.join(bad)} desconhecido(s); use: {', '.join(allowed)}")
    if age == "idoso" and "rugas" not in marks:
        marks.append("rugas")

    expressions = list(data.get("expressoes") or EXPRESSIONS)
    bad = [e for e in expressions if e not in EXPRESSIONS]
    if bad:
        raise ModelError(f"expressoes: {', '.join(bad)} desconhecida(s); use: {', '.join(EXPRESSIONS)}")
    walk = int(data.get("andar", 4))
    if walk not in (4, 6):
        raise ModelError("'andar' deve ser 4 ou 6 quadros")
    try:
        light = parse_light(data.get("luz", "cima-esquerda"))
    except ValueError as exc:
        raise ModelError(str(exc)) from None
    for i, extra in enumerate(data.get("extras") or []):
        if "grade" not in extra or "paleta" not in extra:
            raise ModelError(f"extras[{i}]: precisa de 'grade' e 'paleta'")

    return Model(
        name=name, size=(int(size[0]), int(size[1])), portrait=portrait, age=age,
        proportions=dict(data.get("proporcoes") or {}), colors=colors, ramps=ramps,
        outline=str(data.get("contorno", "selout")), style=style, light=light, hair=hair, outfit=outfit,
        legs=legs, accessories=accessories, marks=marks, beard=layers.get("barba", "nenhuma"),
        expressions=expressions, walk_frames=walk, extras=list(data.get("extras") or []), data=data,
    )


def load_model_data(path: str | Path) -> dict:
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModelError(f"{path}: JSON inválido ({exc})") from None
    if not isinstance(data, dict):
        raise ModelError(f"{path}: o modelo deve ser um objeto JSON")
    return data


def model_name(path: str | Path) -> str:
    """'lia.personagem.json' → 'lia'."""
    name = Path(path).name
    for suffix in (".json", ".personagem"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name


def resolve(data: dict, variants: list[str] = (), palette: str | None = None) -> dict:
    """Aplica variantes (na ordem) e uma paleta nomeada do modelo."""
    out = copy.deepcopy(data)
    for name in variants:
        table = data.get("variantes") or {}
        if name not in table:
            raise ModelError(f"variante '{name}' não existe. Disponíveis: {', '.join(table) or '(nenhuma)'}")
        out = deep_merge(out, table[name])
    if palette:
        table = data.get("paletas") or {}
        if palette not in table:
            raise ModelError(f"paleta '{palette}' não existe no modelo. Disponíveis: {', '.join(table) or '(nenhuma)'}")
        out = deep_merge(out, {"cores": table[palette]})
    return out


def load_model(path: str | Path, variants: list[str] = (), palette: str | None = None) -> Model:
    data = load_model_data(path)
    try:
        return parse_model(resolve(data, variants, palette), default_name=model_name(path))
    except ModelError as exc:
        raise ModelError(f"{path}: {exc}") from None


# --------------------------------------------------------------------------
# Figura: materiais chapados por parte, depois sombreados
# --------------------------------------------------------------------------


class Figure:
    def __init__(self, model: Model, width: int, height: int):
        self.model = model
        self.w, self.h = width, height
        self.ys, self.xs = np.mgrid[0:height, 0:width]
        self.mat = np.full((height, width), -1, dtype=np.int32)
        self.part = np.full((height, width), -1, dtype=np.int32)
        self.far = np.zeros((height, width), dtype=bool)
        self.ink = np.zeros((height, width, 4), dtype=np.uint8)
        self.ink_layer = np.full((height, width), -1, dtype=np.int32)
        self.materials: list[str] = []
        self.parts: list[str] = []
        self.origins: dict[str, tuple[int, int]] = {}

    def _id(self, table: list[str], name: str) -> int:
        if name not in table:
            table.append(name)
        return table.index(name)

    # -- máscaras -----------------------------------------------------------

    def ellipse(self, cx, cy, rx, ry) -> np.ndarray:
        return ((self.xs - cx) / max(rx, 0.5)) ** 2 + ((self.ys - cy) / max(ry, 0.5)) ** 2 <= 1.0 + 1e-9

    def rect(self, x0, y0, x1, y1) -> np.ndarray:
        """Retângulo inclusivo [x0, x1] × [y0, y1]."""
        return (self.xs >= x0) & (self.xs <= x1) & (self.ys >= y0) & (self.ys <= y1)

    def polygon(self, points) -> np.ndarray:
        px, py = self.xs + 0.5, self.ys + 0.5
        inside = np.zeros((self.h, self.w), dtype=bool)
        n = len(points)
        for i in range(n):
            (x0, y0), (x1, y1) = points[i], points[(i + 1) % n]
            x0, y0, x1, y1 = x0 + 0.5, y0 + 0.5, x1 + 0.5, y1 + 0.5
            crosses = (y0 > py) != (y1 > py)
            with np.errstate(divide="ignore", invalid="ignore"):
                x_at = (x1 - x0) * (py - y0) / (y1 - y0) + x0
            inside ^= crosses & (px < x_at)
        return inside

    # -- pintura --------------------------------------------------------------

    def paint(self, mask: np.ndarray, material: str, part: str, far: bool = False) -> None:
        self.mat[mask] = self._id(self.materials, material)
        self.part[mask] = self._id(self.parts, part)
        self.far[mask] = far

    def erase(self, mask: np.ndarray) -> None:
        self.mat[mask] = -1
        self.part[mask] = -1

    def has(self, part: str) -> np.ndarray:
        if part not in self.parts:
            return np.zeros((self.h, self.w), dtype=bool)
        return self.part == self.parts.index(part)

    def opaque(self) -> np.ndarray:
        return self.mat >= 0

    def dot(self, x: int, y: int, color: RGBA, layer: str = "rosto", over_empty: bool = True) -> None:
        if 0 <= x < self.w and 0 <= y < self.h and (over_empty or self.mat[y, x] >= 0):
            self.ink[y, x] = color
            self.ink_layer[y, x] = LAYERS.index(layer)

    def glyph(self, x: int, y: int, rows: list[str], colors: dict[str, RGBA], mirror: bool = False,
              layer: str = "rosto") -> None:
        for j, row in enumerate(rows):
            row = row[::-1] if mirror else row
            for i, key in enumerate(row):
                if key != "." and key in colors:
                    self.dot(x + i, y + j, colors[key], layer)

    def line(self, x0, y0, x1, y1, color: RGBA, layer: str = "rosto", skip_ink: bool = False) -> None:
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            if not (skip_ink and 0 <= x0 < self.w and 0 <= y0 < self.h and self.ink[y0, x0, 3]):
                self.dot(x0, y0, color, layer, over_empty=False)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def extras(self, view: str) -> None:
        for extra in self.model.extras:
            if view not in extra.get("vistas", ["frente", "direita", "costas", "retrato"]):
                continue
            ox, oy = self.origins.get(extra.get("presa_a", "tela"), (0, 0))
            px, py = extra.get("pos", [0, 0])
            colors = {k: parse_color(v) for k, v in extra["paleta"].items()}
            layer = extra.get("camada", "acessorio")
            if layer not in LAYERS:
                raise ModelError(f"extra '{extra.get('nome', '?')}': camada {layer!r}; use: {', '.join(LAYERS)}")
            self.glyph(ox + int(px), oy + int(py), extra["grade"], {k: c for k, c in colors.items() if c[3]},
                       layer=layer)

    # -- acabamento -----------------------------------------------------------

    def finish_painted(self) -> tuple[Sprite, np.ndarray]:
        """Estilo "pintado" (nível das referências): rampas de 6 tons com hue shifting,
        sombra em blocos recortados por parte (sem degradê), pincelada nos tecidos,
        luz de borda dupla (quente do lado da luz, fria do outro) e contorno seletivo."""
        from .paint import Paint, mix

        model = self.model
        warm, cool = (parse_color(c) for c in model.data.get("luz_borda", ["#ec9c5e", "#8a96cc"]))
        p = Paint(self.w, self.h, light=(model.light[0] * 0.55, model.light[1] * 0.75, 0.62))
        for mat in self.materials:
            ramp = model.ramp(mat)
            base = model.color(mat)
            edge = from_lch(*(lambda L, C, h: (max(0.1, L - 0.32), min(C, 0.05), h))(*to_lch(ramp[-1])))
            if mat in model.ramps:
                p.custom_ramp(mat, ramp[::-1], 2, rim=mix(ramp[0], warm, 0.6), outline=edge, rim2=mix(ramp[1], cool, 0.5))
            else:
                p.hue_ramp(mat, base, 3, 2, hue=16, rim=mix(shade(base, 1), warm, 0.6), outline=edge,
                           rim2=mix(base, cool, 0.55))
        lx, ly = model.light
        regions: dict[tuple[int, int, bool], np.ndarray] = {}
        for key in {(int(a), int(b), bool(c)) for a, b, c in zip(self.part[self.mat >= 0], self.mat[self.mat >= 0],
                                                                 self.far[self.mat >= 0])}:
            part, mat, far = key
            regions[key] = (self.part == part) & (self.mat == mat) & (self.far == far)
        for (part, mat, far), mask in sorted(regions.items()):
            name = self.materials[mat]
            p.set(mask, name, 0)
            ys, xs = np.nonzero(mask)
            size = min(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1)
            s = max(1, round(size * 0.28))
            shadow = p.crescent(mask, lx * s, ly * s)
            p.shift(shadow, -1)
            if size >= 6:
                core = p.crescent(mask, lx * max(1, s // 2), ly * max(1, s // 2)) & shadow
                p.shift(core, -1)
                light = p.crescent(mask, -lx * s, -ly * s) & ~p.crescent(mask, -lx, -ly)
                p.shift(light, 1)
            if far:
                p.shift(mask, -1)
        for (part, mat, far), mask in regions.items():                 # sombra projetada (cabelo na testa…)
            casters = np.zeros_like(mask)
            for other in CASTS.get(self.parts[part], ()):
                casters |= self.has(other)
            if casters.any():
                p.shift(mask & p.moved(casters, 0, -ly if ly else 1) & ~casters, -1)
        has_ink = self.ink[..., 3] > 0
        inks: dict[tuple, str] = {}
        for y, x in zip(*np.nonzero(has_ink)):
            c = tuple(int(v) for v in self.ink[y, x])
            if c not in inks:
                inks[c] = p.custom_ramp(f"tinta{len(inks)}", [c], 0, rim=c,
                                        outline=from_lch(*(lambda L, C, h: (max(0.08, L - 0.3), C, h))(*to_lch(c))))
            p.px(int(x), int(y), inks[c], 0, lock=True)
        skin = (self.mat == self.materials.index("pele")) if "pele" in self.materials else np.zeros_like(has_ink)
        cloth = (self.mat >= 0) & ~skin & ~has_ink
        p.texture(cloth, -1, 0.03, seed=3, stroke=(max(2, self.w // 24), 1))
        p.painterly(cloth, edge=0.45, speck=0.0, dither=0.004, seed=11)
        p.painterly(skin & ~has_ink, edge=0.2, speck=0.0, seed=12)
        p.rim_light(dirs=((-lx, 0),), width=1, second=True) if lx else None
        p.rim_light(dirs=tuple(d for d in ((lx, 0), (0, ly)) if d != (0, 0)), width=1)
        sprite = p.render(outline="seletivo")

        layer_map = np.full((self.h, self.w), -1, dtype=np.int32)
        for name in self.parts:
            layer_map[self.has(name)] = LAYERS.index(PART_LAYER.get(name, "corpo"))
        layer_map[has_ink] = self.ink_layer[has_ink]
        new = (sprite.pixels[..., 3] > 0) & (self.mat < 0) & ~has_ink
        layer_map[new] = LAYERS.index("contorno")
        return sprite, layer_map

    def finish(self) -> tuple[Sprite, np.ndarray]:
        """Sombreia, aplica a tinta e o contorno. Devolve o sprite e o mapa de camadas."""
        model = self.model
        if model.style == "pintado":
            return self.finish_painted()
        keys: dict[tuple[int, int, bool], int] = {}
        regions = np.full((self.h, self.w), -1, dtype=np.int32)
        for y, x in zip(*np.nonzero(self.mat >= 0)):
            key = (int(self.part[y, x]), int(self.mat[y, x]), bool(self.far[y, x]))
            regions[y, x] = keys.setdefault(key, len(keys))
        ramps = {}
        part_regions: dict[str, set[int]] = {}
        for (part, mat, far), rid in keys.items():
            ramps[rid] = (model.ramp(self.materials[mat]), 2 if far else 1)
            part_regions.setdefault(self.parts[part], set()).add(rid)
        casts = {}
        for (part, mat, far), rid in keys.items():
            casters = set()
            for name in CASTS.get(self.parts[part], ()):
                casters |= part_regions.get(name, set())
            if casters:
                casts[rid] = casters
        pixels = shade_regions(regions, ramps, model.light, shadow=SHADOW, casts=casts)

        layer_map = np.full((self.h, self.w), -1, dtype=np.int32)
        for name in self.parts:
            layer_map[self.has(name)] = LAYERS.index(PART_LAYER.get(name, "corpo"))
        has_ink = self.ink[..., 3] > 0
        pixels[has_ink] = self.ink[has_ink]
        layer_map[has_ink] = self.ink_layer[has_ink]

        sprite = Sprite(pixels)
        mode = (model.outline or "nenhum").lower()
        if mode not in ("nenhum", "none", ""):
            if mode == "selout":
                dark_of = {}
                for material in self.materials:
                    for c in model.ramp(material):
                        dark_of[tuple(c)] = model.edge(material)
                outlined = selout(sprite, dark_of)
            else:
                outlined = solid_outline(sprite, parse_color(mode))
            new = (outlined.pixels[..., 3] > 0) & (pixels[..., 3] == 0)
            layer_map[new] = LAYERS.index("contorno")
            sprite = outlined
        return sprite, layer_map


# --------------------------------------------------------------------------
# Cabelo, chapéu e barba (coordenadas normalizadas da cabeça)
# --------------------------------------------------------------------------


def _norm(fig: Figure, cx, cy, rx, ry):
    return (fig.xs - cx) / rx, (fig.ys - cy) / ry


def hair_masks(fig: Figure, model: Model, view: str, cx, cy, rx, ry) -> tuple[np.ndarray, np.ndarray]:
    """(atrás do corpo, na frente) para o estilo de cabelo, na vista dada."""
    style, fringe = model.hair["estilo"], model.hair["franja"]
    empty = np.zeros((fig.h, fig.w), dtype=bool)
    if style == "careca":
        return empty, empty
    vol = float(model.hair.get("volume", 0)) + 0.6
    u, v = _norm(fig, cx, cy, rx, ry)
    ex, ey = 1 + vol / rx, 1 + vol / ry
    if style == "cacheado":
        ex, ey = ex + 0.22, ey + 0.16
        ang = np.arctan2(v, u)
        cap = (u / ex) ** 2 + (v / ey) ** 2 <= (1 + 0.07 * np.cos(ang * 11)) ** 2
    elif style == "espetado":
        spike = ((fig.xs - int(round(cx))) % 3 == 0) & (v < -0.2)
        cap = (u / ex) ** 2 + (v / (ey + spike * (2.2 / ry))) ** 2 <= 1
    else:
        cap = (u / ex) ** 2 + (v / ey) ** 2 <= 1
    strand = (fig.xs % 3 == 1)
    back = empty.copy()

    if view in ("frente", "retrato"):
        line = {
            "reta": -0.25 + 0.14 * strand,
            "lado": -0.58 + 0.5 * np.clip((u + 1) / 2, 0, 1),
            "repartida": -0.66 + 0.48 * np.abs(u),
            "nenhuma": np.full(u.shape, -0.6),
        }[fringe]
        side_drop = 0.62 if style == "cacheado" else 0.28
        line = np.where(np.abs(u) > 0.8, side_drop, line)
        front = cap & (v < line)
        if style == "longo":
            falls = (np.abs(u) > 0.7) & (np.abs(u) < ex + 0.08) & (v > 0) & (v < 1.75)
            front |= falls
            back = cap | ((np.abs(u) < ex) & (v > 0) & (v < 1.75))
        elif style == "coque":
            front |= ((u / 0.42) ** 2 + ((v + 1.08) / 0.34) ** 2 <= 1)
        elif style == "rabo":
            back = (np.abs(u) < 1.05) & (v > 0.2) & (v < 0.5) & ~cap
    elif view == "costas":
        drop = 0.75 if style == "cacheado" else 0.55
        front = cap & (v < drop)
        if style == "longo":
            front |= (np.abs(u) < ex - 0.05) & (v < 1.75) & (v > -0.2)
        elif style == "rabo":
            front |= (np.abs(u) < 0.3) & (v > 0.2) & (v < 1.45)
        elif style == "coque":
            front |= ((u / 0.42) ** 2 + ((v + 1.08) / 0.34) ** 2 <= 1)
    else:  # direita
        bangs = {"reta": -0.32, "lado": -0.24, "repartida": -0.42, "nenhuma": -0.55}[fringe]
        nape = 0.75 if style == "cacheado" else 0.5
        line = np.where(u < 0.0, nape, bangs - 0.25 * np.clip(u, 0, 1))
        front = cap & (v < line)
        if style == "longo":
            front |= (u < 0.05) & (u > -ex) & (v > 0) & (v < 1.75)
        elif style == "rabo":
            front |= ((u + 1.18) / 0.3) ** 2 + ((v - 0.28) / 0.62) ** 2 <= 1
        elif style == "coque":
            front |= ((u + 0.78) / 0.38) ** 2 + ((v + 0.78) / 0.34) ** 2 <= 1
    return back, front


def hat_mask(fig: Figure, view: str, cx, cy, rx, ry) -> tuple[np.ndarray, np.ndarray]:
    """(aba, copa) do chapéu."""
    u, v = _norm(fig, cx, cy, rx, ry)
    reach = 1.42 if view == "direita" else 1.3
    brim = (np.abs(u + (0.08 if view == "direita" else 0)) < reach) & (v > -0.66) & (v <= -0.66 + 2.2 / ry)
    crown = ((u / 0.8) ** 2 + ((v + 0.62) / 0.72) ** 2 <= 1) & (v <= -0.5)
    return brim, crown


def beard_mask(fig: Figure, style: str, view: str, head: np.ndarray, cx, cy, rx, ry) -> np.ndarray:
    u, v = _norm(fig, cx, cy, rx, ry)
    if style == "cheia":
        m = head & ((v > 0.42) | ((np.abs(u) > 0.72) & (v > 0.05)))
        if view == "direita":
            m = head & (v > 0.38) & (u > -0.25)
        return m
    if style == "bigode":
        return head & (v > 0.45) & (v < 0.45 + 1.6 / ry) & (np.abs(u if view != "direita" else u - 0.7) < 0.36)
    if style == "cavanhaque":
        return head & (v > 0.7) & (np.abs(u if view != "direita" else u - 0.6) < 0.3)
    return np.zeros_like(head)


# --------------------------------------------------------------------------
# Corpo (sprite)
# --------------------------------------------------------------------------


@dataclass
class Pose:
    breath: int = 0       # 1 = parte de cima desce 1 px (respirar)
    down: int = 0         # 1 = corpo todo desce 1 px (contato do passo)
    near: float = 0       # deslocamento do pé da frente (vista lateral) / perna direita
    far: float = 0        # deslocamento do pé de trás / perna esquerda
    lift_near: int = 0    # pé levantado (px)
    lift_far: int = 0
    blink: bool = False
    mouth: bool = False


@dataclass
class BodyGeometry:
    W: int
    H: int
    cx: float
    head_top: int
    hh: int
    hw: int
    th: int
    tw: int
    torso_top: int
    hip: int


def _parity(value: int, width: int) -> int:
    value = max(2, int(round(value)))
    return value if value % 2 == width % 2 else value + 1


def body_geometry(model: Model) -> BodyGeometry:
    W, H = model.size
    p = model.proportions
    if model.style == "pintado":   # ~4,4 cabeças (faixa medida nas referências), ombros > cabeça
        head_ratio, torso_ratio, alt_ratio = {"crianca": (0.24, 0.32, 0.88), "adulto": (0.22, 0.31, 0.95),
                                              "idoso": (0.22, 0.31, 0.93)}[model.age]
        width_ratio, shoulder_ratio = 0.82, 1.35
    else:
        head_ratio, torso_ratio, alt_ratio = {"crianca": (0.5, 0.25, 0.8), "adulto": (0.42, 0.29, 0.94),
                                              "idoso": (0.42, 0.29, 0.92)}[model.age]
        width_ratio, shoulder_ratio = None, 0.8
    alt = int(p.get("altura", round(H * alt_ratio)))
    hh = int(p.get("cabeca", round(alt * head_ratio)))
    hw = _parity(p.get("largura_cabeca", hh * width_ratio if width_ratio else hh - 1), W)
    th = int(p.get("tronco", round(alt * torso_ratio)))
    tw = _parity(p.get("ombros", hw * shoulder_ratio), W)
    head_top = H - alt
    torso_top = head_top + hh - 1
    hip = torso_top + th
    if alt > H or head_top < 0 or H - hip < 3:
        raise ModelError(f"proporções não cabem em {W}x{H}: altura {alt}, cabeça {hh}, tronco {th} "
                         f"(sobram {H - hip} px para as pernas; mínimo 3)")
    if hw + 8 > W:
        raise ModelError(f"cabeça larga demais ({hw}) para a largura {W}")
    return BodyGeometry(W, H, (W - 1) / 2, head_top, hh, hw, th, tw, torso_top, hip)


def render_body(model: Model, view: str = "direita", pose: Pose | None = None) -> tuple[Sprite, np.ndarray]:
    if view not in VIEWS:
        raise ModelError(f"vista '{view}' inválida; use: {', '.join(VIEWS)}")
    pose = pose or Pose()
    g = body_geometry(model)
    fig = Figure(model, g.W, g.H)
    lift = pose.breath + pose.down
    side = view == "direita"
    acc = set(model.accessories)

    # cabeça
    hrx, hry = g.hw / 2 - 0.2, g.hh / 2 - 0.25
    hcx, hcy = g.cx, g.head_top + (g.hh - 1) / 2 + lift
    # tronco
    tw = max(4, _parity(g.tw * 0.62, g.W)) if side else g.tw
    tx0 = int(round(g.cx - tw / 2 + 0.5))
    tx1 = tx0 + tw - 1
    ttop = g.torso_top + lift
    hip = g.hip + pose.down
    bottom = g.H - 1
    legs_len = bottom - hip + 1
    fig.origins = {"cabeca": (int(round(hcx - hrx)), g.head_top + lift), "tronco": (tx0, ttop), "tela": (0, 0)}
    outfit = model.outfit["estilo"]
    sleeves = model.outfit["mangas"]
    legwear = model.legs["estilo"]

    unit = max(1, round(g.hh / 11)) if model.style == "pintado" else 1    # espessura em px de braço/perna
    LW = max(3, round(g.tw * 0.36)) if model.style == "pintado" else (3 if g.tw >= 8 else 2)
    AW = 2 * unit

    # capa (atrás de tudo, exceto nas costas)
    if "capa" in acc and view != "costas":
        if side:
            cape = fig.polygon([(tx0 - 1, ttop + 1), (tx0 + 1, ttop + 1), (tx0 + 1, hip + legs_len // 2),
                                (tx0 - 3, hip + legs_len // 2 + 1), (tx0 - 3, ttop + 4)])
        else:
            cape = fig.rect(tx0 - 2, ttop + 1, tx1 + 2, hip + legs_len // 2)
        fig.paint(cape, "capa", "capa")

    # cabelo de trás
    back_hair, front_hair = hair_masks(fig, model, view, hcx, hcy, hrx, hry)
    if back_hair.any():
        fig.paint(back_hair, "cabelo", "cabelo_tras", far=True)

    def leg(xc: float, foot_dx: float, lift_px: int, far: bool) -> None:
        """Perna da cintura ao pé; pé deslocado foot_dx (lateral) e levantado lift_px."""
        foot_y = bottom - lift_px
        lw = LW
        shoe_rows = max(2, round(legs_len * 0.14)) if legs_len >= 6 else 1
        for y in range(hip, foot_y + 1):
            t = (y - hip) / max(foot_y - hip, 1)
            x = int(round(xc + foot_dx * t))
            if model.style == "pintado":                                   # coxa larga afinando no tornozelo
                lw = max(3, round(LW * (1.15 - 0.4 * t)))
            x0 = x - lw // 2
            row = fig.rect(x0, y, x0 + lw - 1, y)
            if y > foot_y - shoe_rows:
                ext = fig.rect(x0, y, x0 + lw, y) if side else fig.rect(x0 - (1 if xc < g.cx else 0), y,
                                                                         x0 + lw - 1 + (1 if xc > g.cx else 0), y)
                fig.paint(ext, "sapato", "sapato", far)
                continue
            frac = (y - hip) / max(legs_len, 1)
            covered = legwear == "calca" and outfit != "vestido" or (legwear == "short" and frac < 0.45) \
                or (legwear == "saia" and frac < 0.5)
            if outfit in ("vestido",) and frac < 0.55:
                covered = False
            fig.paint(row, "calca" if covered else "pele", "calca" if covered else "perna", far)

    # pernas
    if side:
        leg(g.cx - 0.5, pose.far, pose.lift_far, far=True)
    else:
        lw = LW
        left_c = tx0 + 1 + (lw - 1) / 2
        right_c = tx1 - 1 - (lw - 1) / 2
        # vista de frente/costas: "near" = perna da direita da tela
        splay = 2 * unit if model.style == "pintado" else 0                 # postura em A
        leg(left_c, -splay, pose.lift_far, far=False)
        leg(right_c, splay, pose.lift_near, far=False)
        if legwear == "calca" and outfit != "vestido":
            fig.paint(fig.rect(tx0 + 1, hip, tx1 - 1, hip), "calca", "calca")

    def arm(shoulder_x: float, swing: float, far: bool, outer: int = 0) -> None:
        top = ttop + 1
        hand_y = hip + 1
        sleeve_end = {"longas": hand_y - 2, "curtas": top + (hand_y - top) // 2 - 1, "sem": top - 1}[sleeves]
        if outfit == "manto":
            sleeve_end = hand_y - 2
        for y in range(top, hand_y + 1):
            t = (y - top) / max(hand_y - top, 1)
            x = int(round(shoulder_x + swing * t))
            seg = fig.rect(x, y, x + AW - 1, y)
            if y >= hand_y - 1:
                fig.paint(seg, "pele", "mao", far)
            elif y <= sleeve_end:
                fig.paint(seg, "roupa", "manga", far)
            else:
                fig.paint(seg, "pele", "braco", far)

    # braço de trás (lateral)
    if side:
        arm(g.cx - 1.5, -pose.near * 0.6, far=True)
        leg(g.cx + 0.5, pose.near, pose.lift_near, far=False)

    # tronco + roupa
    torso = fig.rect(tx0, ttop, tx1, hip - 1)
    torso &= ~(fig.rect(tx0, ttop, tx0, ttop) | fig.rect(tx1, ttop, tx1, ttop))
    fig.paint(torso, "roupa", "tronco")
    if outfit == "casaco":
        fig.paint(fig.rect(tx0, hip, tx1, hip + 1), "roupa", "tronco")
        if view == "frente":
            mid = int(round(g.cx))
            fig.paint(fig.rect(mid - 1, ttop + 1, mid, hip - 1), "roupa2", "gola")
        elif side:
            fig.paint(fig.rect(tx1 - 1, ttop + 1, tx1, hip - 1), "roupa2", "gola")
    elif outfit == "vestido":
        skirt_end = hip + int(legs_len * 0.55)
        fig.paint(fig.polygon([(tx0, hip - 2), (tx1, hip - 2), (tx1 + 1, skirt_end), (tx0 - 1, skirt_end)]),
                  "roupa", "saia")
    elif outfit == "manto":
        fig.paint(fig.polygon([(tx0, hip - 1), (tx1, hip - 1), (tx1 + 1, bottom - 1), (tx0 - 1, bottom - 1)]),
                  "roupa", "saia")
        fig.paint(fig.rect(tx0 - 1, bottom - 1, tx1 + 1, bottom - 1), "roupa2", "cinto")
    if legwear == "saia" and outfit not in ("vestido", "manto"):
        fig.paint(fig.polygon([(tx0, hip), (tx1, hip), (tx1 + 1, hip + legs_len // 2 - 1),
                               (tx0 - 1, hip + legs_len // 2 - 1)]), "calca", "saia")
    if view == "frente" and outfit == "camisa":
        mid = int(round(g.cx))
        fig.paint(fig.rect(mid - 1, ttop, mid, ttop), "roupa2", "gola")
    if "cinto" in acc:
        fig.paint(fig.rect(tx0, hip - 1, tx1, hip - 1), "roupa2", "cinto")

    # braços
    if side:
        arm(g.cx - 0.5, -pose.far * 0.6, far=False)
    else:
        out = -unit if model.style == "pintado" else 0                     # braços levemente afastados
        arm(tx0 - AW - 1, out, far=False)
        arm(tx1 + 2, -out, far=False)
        # ombro liga o braço ao tronco; o resto fica separado por 1 px (vira contorno)
        fig.paint(fig.rect(tx0 - 1, ttop + 1, tx0 - 1, ttop + 1) | fig.rect(tx1 + 1, ttop + 1, tx1 + 1, ttop + 1),
                  "roupa" if sleeves != "sem" else "pele", "manga" if sleeves != "sem" else "braco")

    # capa nas costas cobre o corpo
    if "capa" in acc and view == "costas":
        fig.paint(fig.rect(tx0 - 2, ttop + 1, tx1 + 2, hip + legs_len // 2), "capa", "capa")

    # cabeça
    head = fig.ellipse(hcx, hcy, hrx, hry)
    fig.paint(head, "pele", "cabeca")
    if side:
        right = np.nonzero(head.any(axis=0))[0].max()
        ey_nose = int(round(hcy + hry * 0.35))
        fig.paint(fig.rect(right + 1, ey_nose, right + 1, ey_nose), "pele", "cabeca")

    # barba
    beard = beard_mask(fig, model.beard, view, head, hcx, hcy, hrx, hry) if view != "costas" else None
    if beard is not None and beard.any():
        fig.paint(beard, "cabelo", "barba")

    # cabelo da frente e chapéu
    if "chapeu" in acc:
        brim, crown = hat_mask(fig, view, hcx, hcy, hrx, hry)
        u, v = _norm(fig, hcx, hcy, hrx, hry)
        front_hair &= ~(v < -0.62)
    fig.paint(front_hair, "cabelo", "cabelo")
    if "chapeu" in acc:
        fig.paint(crown, "chapeu", "chapeu")
        fig.paint(brim, "chapeu", "chapeu")
    if "cachecol" in acc:
        fig.paint(fig.rect(tx0 - (0 if side else 1), ttop, tx1 + (0 if side else 1), ttop + 1), "acessorio", "cachecol")
        tail_x = tx0 - 1 if side else tx0 + 1
        fig.paint(fig.rect(tail_x, ttop + 2, tail_x + 1, ttop + 3), "acessorio", "cachecol")

    # rosto
    if view != "costas":
        eh = max(1, round(g.hh / 7))
        if model.style == "pintado":
            eh = min(eh, 2)                                                   # olho de 1–2 px, nada de anime
        ey = int(round(hcy + hry * 0.12))
        eye_color = shade(model.color("olhos"), -3)
        lid = shade(model.color("pele"), -2)
        if side:
            eyes = [int(round(hcx + hrx * 0.52))]
        else:
            ex = int(round(hcx - hrx * 0.45))
            eyes = [ex, g.W - 1 - ex]
        for x in eyes:
            if pose.blink:
                fig.dot(x, ey + eh - 1, lid)
            else:
                for j in range(eh):
                    fig.dot(x, ey + j, eye_color)
        if "oculos" in acc:
            frame = model.colors.get("oculos") or model.ink
            if side:
                fig.line(eyes[0] - 3, ey, eyes[0] + 1, ey, frame, "acessorio", skip_ink=True)
            else:
                fig.line(eyes[0] - 1, ey - 1, eyes[1] + 1, ey - 1, frame, "acessorio")
        if "cicatriz" in model.marks:
            scar = from_lch(*_scar_lch(model))
            x = eyes[-1] + (1 if not side else -1)
            fig.dot(x, ey + eh, scar, over_empty=False)
            fig.dot(x + (1 if not side else -1), ey + eh + 1, scar, over_empty=False)
        if pose.mouth:
            my = ey + eh + max(1, round(g.hh / 8))
            mouth = shade(model.color("boca"), -2)
            if side:
                fig.dot(eyes[0] + 1, my, mouth)
            else:
                fig.dot(int(np.floor(g.cx)), my, mouth)
                fig.dot(int(np.ceil(g.cx)), my, mouth)
    fig.extras(view)
    return fig.finish()


def _scar_lch(model: Model) -> tuple[float, float, float]:
    L, C, h = to_lch(model.color("pele"))
    return max(L - 0.2, 0.2), C + 0.05, 25.0


# --------------------------------------------------------------------------
# Retrato
# --------------------------------------------------------------------------

# Glifos do retrato (olho esquerdo da tela; o direito é espelhado). Chaves:
# k cílio · w branco · i íris · p pupila · h brilho · c sobrancelha · b lábio · d boca aberta · t dente
EYES = {
    "neutro": ["kkkk", "wphw", "wiiw"],
    "feliz": [".kk.", "k..k", "...."],
    "bravo": ["k...", "kkkk", "wphw"],
    "triste": ["....", "kkkk", "wphw"],
    "surpreso": ["kkkk", "wiiw", "wphw", "wwww"],
}
# estilo pintado: olho discreto (fenda escura + pálpebra), sem íris grande, brilho nem cílios
EYES_PINTADO = {
    "neutro": ["kkkk", ".pp."],
    "feliz": [".kk.", "k..k"],
    "bravo": ["kk..", ".kkk"],
    "triste": ["..kk", "kpp."],
    "surpreso": ["kkkk", "p..p"],
}
EYES_CLOSED = {"feliz": EYES["feliz"]}
EYES_CLOSED_DEFAULT = ["....", "....", "kkkk"]
BROWS = {  # topo em (olho - 4)
    "neutro": ["....", "....", "cccc"],
    "feliz": ["....", "cccc", "...."],
    "bravo": ["....", "cc..", "..cc"],
    "triste": ["....", "..cc", "cc.."],
    "surpreso": ["cccc", "....", "...."],
}
MOUTHS = {  # (fechada, aberta), centradas
    "neutro": (["bbbb"], ["bbbb", "bddb", ".bb."]),
    "feliz": (["b....b", ".bbbb."], ["bbbbbb", "bttttb", ".bddb."]),
    "bravo": ([".bbbb.", "b....b"], ["bbbbbb", "bddddb", "b....b"]),
    "triste": ([".bb.", "b..b"], [".bb.", "bddb", "b..b"]),
    "surpreso": ([".bb.", "b..b", ".bb."], [".bb.", "bddb", "bddb", ".bb."]),
}


def render_portrait(model: Model, expression: str = "neutro", mouth_open: bool = False,
                    blink: bool = False) -> tuple[Sprite, np.ndarray]:
    if expression not in EXPRESSIONS:
        raise ModelError(f"expressão '{expression}' inválida; use: {', '.join(EXPRESSIONS)}")
    S = model.portrait
    fig = Figure(model, S, S)
    cx = (S - 1) / 2
    hh = int(round(S * 0.58))
    hw = _parity(S * 0.5, S)
    top = int(round(S * 0.14))
    rx, ry = hw / 2 - 0.2, hh / 2 - 0.2
    cy = top + (hh - 1) / 2
    acc = set(model.accessories)
    fig.origins = {"cabeca": (int(round(cx - rx)), top), "tela": (0, 0)}

    back_hair, front_hair = hair_masks(fig, model, "retrato", cx, cy, rx, ry)
    if back_hair.any():
        fig.paint(back_hair, "cabelo", "cabelo_tras", far=True)

    # ombros e pescoço
    sy = top + hh - 1 + int(round(S * 0.03))
    neck_w = _parity(hw * 0.36, S)
    nx0 = int(round(cx - neck_w / 2 + 0.5))
    fig.paint(fig.rect(nx0, int(cy + ry * 0.55), nx0 + neck_w - 1, sy + 2), "pele", "pescoco")
    sw = _parity(S * 0.84, S)
    sx0 = int(round(cx - sw / 2 + 0.5))
    corner = max(3, S // 10)
    shoulders = fig.rect(sx0, sy + corner, sx0 + sw - 1, S - 1) | fig.rect(sx0 + corner, sy, sx0 + sw - 1 - corner, S - 1)
    shoulders |= fig.ellipse(sx0 + corner, sy + corner, corner, corner) | fig.ellipse(sx0 + sw - 1 - corner, sy + corner,
                                                                                       corner, corner)
    fig.origins["tronco"] = (sx0, sy)
    outfit = model.outfit["estilo"]
    fig.paint(shoulders, "roupa", "tronco")
    mid_l, mid_r = int(np.floor(cx)), int(np.ceil(cx))
    if outfit == "camisa":
        fig.paint(fig.polygon([(nx0 - 2, sy), (mid_l, sy + 4), (mid_r, sy + 4), (nx0 + neck_w + 1, sy)]),
                  "roupa2", "gola")
        fig.paint(fig.polygon([(nx0, sy), (mid_l, sy + 2), (mid_r, sy + 2), (nx0 + neck_w - 1, sy)]), "pele", "pescoco")
    elif outfit == "casaco":
        fig.paint(fig.polygon([(nx0 - 1, sy), (nx0 + neck_w, sy), (mid_r + 1, S - 1), (mid_l - 1, S - 1)]),
                  "roupa2", "gola")
        fig.paint(fig.polygon([(nx0, sy), (nx0 + neck_w - 1, sy), (mid_r, sy + 3), (mid_l, sy + 3)]), "pele", "pescoco")
    elif outfit == "vestido":
        fig.paint(fig.ellipse(cx, sy, neck_w / 2 + 2.5, 3.5) & (fig.ys >= sy), "pele", "pescoco")
    elif outfit == "manto":
        fig.paint(fig.polygon([(nx0 - 3, sy - 1), (nx0 + neck_w + 2, sy - 1), (mid_r + 1, sy + 5), (mid_l - 1, sy + 5)])
                  & shoulders, "roupa2", "gola")
        fig.paint(fig.polygon([(nx0 - 1, sy - 1), (nx0 + neck_w, sy - 1), (mid_r, sy + 3), (mid_l, sy + 3)]),
                  "pele", "pescoco")
    if "capa" in acc:
        fig.paint(shoulders & (np.abs(fig.xs - cx) > neck_w / 2 + S * 0.16), "capa", "capa")
    if "cachecol" in acc:
        fig.paint(fig.rect(nx0 - 3, sy - 2, nx0 + neck_w + 2, sy + 1) & ~fig.ellipse(cx, sy - 3, neck_w / 2 + 3.5, 1.2),
                  "acessorio", "cachecol")
        fig.paint(fig.rect(nx0 + neck_w - 1, sy + 2, nx0 + neck_w + 2, sy + 7), "acessorio", "cachecol")

    # orelhas, cabeça (queixo afinado)
    for ox in (cx - rx, cx + rx):
        fig.paint(fig.ellipse(ox + (0.5 if ox > cx else -0.5), cy + ry * 0.12, max(1.5, S / 26), max(2.5, S / 13)), "pele", "orelha")
    u, v = _norm(fig, cx, cy, rx, ry)
    taper = 1 - 0.28 * np.clip(v - 0.3, 0, 1)
    head = (u / taper) ** 2 + v ** 2 <= 1
    fig.paint(head, "pele", "cabeca")
    beard = beard_mask(fig, model.beard, "frente", head, cx, cy, rx, ry)
    if beard.any():
        fig.paint(beard, "cabelo", "barba")
    if "chapeu" in acc:
        brim, crown = hat_mask(fig, "frente", cx, cy, rx, ry)
        front_hair &= ~(v < -0.62)
    fig.paint(front_hair, "cabelo", "cabelo")
    if "chapeu" in acc:
        fig.paint(crown, "chapeu", "chapeu")
        fig.paint(brim, "chapeu", "chapeu")

    # rosto
    k = max(1, S // 96 + 1) if S >= 96 else 1
    pele = model.color("pele")
    colors = {
        "k": model.ink, "w": from_lch(0.95, 0.01, 90), "i": model.color("olhos"),
        "p": shade(model.color("olhos"), -3), "h": (255, 255, 255, 255), "c": shade(model.color("cabelo"), -1),
        "b": shade(model.color("boca"), -1), "d": shade(model.color("boca"), -3), "t": from_lch(0.93, 0.01, 90),
        "s": shade(pele, -1),
    }
    ey = int(round(cy + ry * 0.04))
    ex = int(round(cx - rx * 0.64))
    ex_r = S - 1 - ex - 3 * k

    def put(x, y, rows, mirror=False):
        rows = [r[::-1] for r in rows] if mirror else rows
        scaled = ["".join(ch * k for ch in r) for r in rows for _ in range(k)]
        fig.glyph(x, y, scaled, colors)

    put(ex, ey - 4 * k, BROWS[expression])
    put(ex_r, ey - 4 * k, BROWS[expression], mirror=True)
    if "cicatriz" in model.marks:
        scar = from_lch(*_scar_lch(model))
        fig.line(ex_r + 3 * k, ey - 4 * k, ex_r + 1, ey + 6 * k, scar)
    eyes = (EYES_CLOSED.get(expression, EYES_CLOSED_DEFAULT) if blink else EYES[expression])
    if model.style == "pintado":
        eyes = ["....", "kkkk"] if blink and expression != "feliz" else EYES_PINTADO[expression]
        eyes = ["....", "....", *eyes]                                       # olho baixo, na sombra da sobrancelha
    put(ex, ey, eyes)
    put(ex_r, ey, eyes, mirror=True)
    if "oculos" in acc:
        frame = model.colors.get("oculos") or model.ink
        for x0 in (ex, ex_r):
            for x in range(x0 - 1, x0 + 4 * k + 1):
                fig.dot(x, ey - 1, frame, "acessorio")
                fig.dot(x, ey + 3 * k + 1, frame, "acessorio")
            for y in range(ey - 1, ey + 3 * k + 2):
                fig.dot(x0 - 1, y, frame, "acessorio")
                fig.dot(x0 + 4 * k, y, frame, "acessorio")
        for x in range(ex + 4 * k + 1, ex_r - 1):
            fig.dot(x, ey, frame, "acessorio")
    ny = int(round(cy + ry * 0.36))
    fig.dot(mid_r, ny, colors["s"])
    fig.dot(mid_r, ny + 1, colors["s"]) if k > 1 else None
    if "sardas" in model.marks:
        for dx, dy in ((0, 5), (2, 6), (1, 7), (3, 5)):
            fig.dot(ex + dx, ey + dy * k, colors["s"])
            fig.dot(S - 1 - ex - dx, ey + dy * k, colors["s"])
    if "rugas" in model.marks:
        for x0, mirror in ((ex, False), (ex_r, True)):
            fig.glyph(x0, ey + 4 * k, ["s.s."], colors, mirror=mirror)
        fig.dot(mid_l - 4, int(round(cy + ry * 0.5)), colors["s"])
        fig.dot(mid_r + 4, int(round(cy + ry * 0.5)), colors["s"])
    if expression == "feliz":
        blush = from_lch(*(lambda L, C, h: (L - 0.04, C + 0.06, 20.0))(*to_lch(pele)))
        for x in (ex - 1, ex, S - 1 - ex, S - 1 - ex + 1):
            fig.dot(x, ey + 4 * k, blush)
    closed, opened = MOUTHS[expression]
    rows = opened if mouth_open else closed
    my = int(round(cy + ry * 0.6))
    width = len(rows[0]) * k
    put(int(round(cx - width / 2 + 0.5)), my, rows)
    fig.extras("retrato")
    return fig.finish()


# --------------------------------------------------------------------------
# Montagem das artes
# --------------------------------------------------------------------------


def walk_poses(frames: int, view: str) -> list[Pose]:
    if view == "direita":
        if frames == 4:
            return [Pose(near=3, far=-3, down=1), Pose(near=0, far=0, lift_far=1),
                    Pose(near=-3, far=3, down=1), Pose(near=0, far=0, lift_near=1)]
        return [Pose(near=3, far=-3, down=1), Pose(near=1, far=-1), Pose(near=-1, far=1, lift_far=1),
                Pose(near=-3, far=3, down=1), Pose(near=-1, far=1), Pose(near=1, far=-1, lift_near=1)]
    if frames == 4:
        return [Pose(lift_near=1, down=1), Pose(), Pose(lift_far=1, down=1), Pose()]
    return [Pose(lift_near=1, down=1), Pose(lift_near=1), Pose(), Pose(lift_far=1, down=1), Pose(lift_far=1), Pose()]


def build_sprite(model: Model) -> tuple[Art, list[np.ndarray]]:
    """Sprite de corpo com animações (direita; frente e costas com sufixo)."""
    b = Builder()
    layers: dict[int, np.ndarray] = {}

    def frames(view: str, poses: list[Pose]) -> list[Sprite]:
        out = []
        for pose in poses:
            sprite, layer_map = render_body(model, view, pose)
            idx = b.add_frame(sprite)
            layers.setdefault(idx, layer_map)
            out.append(sprite)
        return out

    still, breath, closed = Pose(), Pose(breath=1), Pose(blink=True)
    walk_fps = 8 if model.walk_frames == 4 else 10
    for view, suffix in (("direita", ""), ("frente", "_frente"), ("costas", "_costas")):
        a, bb = frames(view, [still, breath])
        c = frames(view, [closed])[0] if view != "costas" else bb
        b.add(f"parado{suffix}", [a, a, bb, bb, a, a, bb, c], 4)
        if view != "costas":
            if view == "direita":
                b.add("respirar", [a, bb], 2)
                b.add("piscar", [a, c, a], 8)
            b.add(f"falar{suffix}", frames(view, [still, Pose(mouth=True)]), 8)
        b.add(f"andar{suffix}", frames(view, walk_poses(model.walk_frames, view)), walk_fps)
    b.frames = merge_close(b.frames)
    g = body_geometry(model)
    art = b.art(model.name, anchor=[int(g.W // 2), g.H - 1], meta={"personagem": model.name}, fps=4)
    return art, [layers[i] for i in range(len(art.frames))]


def build_portrait(model: Model) -> tuple[Art, list[np.ndarray]]:
    """Retrato com uma animação por expressão (+ _falar e _piscar)."""
    b = Builder()
    layers: dict[int, np.ndarray] = {}

    def frame(expression: str, **kw) -> Sprite:
        sprite, layer_map = render_portrait(model, expression, **kw)
        layers.setdefault(b.add_frame(sprite), layer_map)
        return sprite

    for expr in model.expressions:
        base = frame(expr)
        b.add(expr, [base], 1)
        b.add(f"{expr}_falar", [base, frame(expr, mouth_open=True)], 8)
        b.add(f"{expr}_piscar", [base, frame(expr, blink=True), base], 8)
    first = model.expressions[0]
    base = b.frames[b.animations[first]["frames"][0]]
    closed = b.frames[b.animations[f"{first}_piscar"]["frames"][1]]
    b.add("parado", [base] * 7 + [closed], 4)
    b.animations["falar"] = dict(b.animations[f"{first}_falar"])
    b.frames = merge_close(b.frames)
    art = b.art(f"{model.name}_retrato", anchor=[model.portrait // 2, model.portrait - 1],
                meta={"personagem": model.name}, fps=4)
    return art, [layers[i] for i in range(len(art.frames))]


def split_layers(sprite: Sprite, layer_map: np.ndarray) -> dict[str, Sprite]:
    """Separa um quadro nas camadas (corpo, roupa, cabelo, ...)."""
    out = {}
    for i, name in enumerate(LAYERS):
        mask = layer_map == i
        if mask.any():
            px = np.zeros_like(sprite.pixels)
            px[mask] = sprite.pixels[mask]
            out[name] = Sprite(px)
    return out


def model_sheet(model: Model, sprite: Art, portrait: Art, gap: int = 4) -> Sprite:
    """Folha do personagem: expressões, 4 direções, ciclo de andar e rampas."""
    anims = sprite.meta["animations"]
    p_anims = portrait.meta["animations"]
    exprs = [portrait.frames[p_anims[e]["frames"][0]] for e in model.expressions]
    right = sprite.frames[anims["parado"]["frames"][0]]
    poses = [right, Sprite(right.pixels[:, ::-1].copy()),
             sprite.frames[anims["parado_frente"]["frames"][0]], sprite.frames[anims["parado_costas"]["frames"][0]]]
    walk = [sprite.frames[i] for i in anims["andar"]["frames"]]
    materials = [m for m in ("pele", "cabelo", "olhos", "roupa", "roupa2", "calca", "sapato", "acessorio", "boca")
                 if m in model.colors]
    S, (W, H) = model.portrait, model.size
    row1 = len(exprs) * (S + gap) - gap
    row2 = len(poses) * (W + gap) + gap + len(walk) * (W + gap) - gap
    sw = 4
    width = max(row1, row2, len(materials) * (sw + 1)) + 2 * gap
    height = gap + S + gap + H + gap + 4 * sw + gap
    canvas = np.zeros((height, width, 4), dtype=np.uint8)

    def paste(img: Sprite, x: int, y: int) -> None:
        m = img.pixels[..., 3] > 0
        canvas[y:y + img.height, x:x + img.width][m] = img.pixels[m]

    for i, e in enumerate(exprs):
        paste(e, gap + i * (S + gap), gap)
    y2 = gap + S + gap
    x = gap
    for img in poses:
        paste(img, x, y2)
        x += W + gap
    x += gap
    for img in walk:
        paste(img, x, y2)
        x += W + gap
    y3 = y2 + H + gap
    for i, m in enumerate(materials):
        for j, c in enumerate(model.ramp(m)):
            canvas[y3 + j * sw:y3 + (j + 1) * sw, gap + i * (sw + 1):gap + i * (sw + 1) + sw] = c
    return Sprite(canvas)
