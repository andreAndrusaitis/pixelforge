"""Pintura com volume para pixel art detalhada (chibi, retratos grandes).

Cada pixel guarda (rampa, tom) em vez de uma cor: assim dá para escurecer,
clarear, contornar e fazer anti-alias depois, sempre dentro da rampa do material.

    p = Paint(64, 64)
    pele = p.ramp("pele", "#b47a52")                 # 6 tons com hue shifting + luz de borda
    p.fill(p.ellipse(32, 20, 12, 13), pele)           # sombreado pelo relevo da forma
    p.shift(p.ellipse(28, 24, 3, 2), -1)              # sombra local
    p.line(25, 18, 29, 18, "cabelo", 0)              # traço com tom fixo
    sprite = p.render()                               # selout colorido + anti-alias

Tons: 0 = mais escuro … n-1 = mais claro; `base` é o tom da cor informada.
Luz padrão: de cima à esquerda, de frente.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .palettes import RGBA, parse_color
from .recolor import from_lch, shade, to_lch
from .sprite import Sprite

LIGHT = np.array([-0.55, -0.75, 0.62])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


@dataclass
class Ramp:
    name: str
    colors: list[RGBA]  # escuro → claro
    base: int
    rim: RGBA
    outline: RGBA
    rim2: RGBA | None = None   # luz de borda secundária (de cor oposta, ex.: azul do céu)

    def __len__(self) -> int:
        return len(self.colors)


def make_ramp(name: str, color, down: int = 3, up: int = 2, step: float = 1.0,
              rim: str | None = None, outline: str | None = None) -> Ramp:
    base = parse_color(color) if isinstance(color, str) else tuple(color)
    colors = [shade(base, -(down - i) * step) for i in range(down)] + [base] + \
             [shade(base, (i + 1) * step) for i in range(up)]
    L, C, h = to_lch(colors[0])
    edge = parse_color(outline) if outline else from_lch(max(0.12, L - 0.1), min(C * 1.1, 0.12), h)
    if rim:
        rim_c = parse_color(rim)
    else:  # luz refletida fria: clara, puxando para ciano
        Lb, Cb, hb = to_lch(base)
        rim_c = from_lch(min(0.92, Lb + 0.12), max(0.03, Cb * 0.6), (hb + (200 - hb) * 0.45) % 360)
    return Ramp(name, colors, down, rim_c, edge)


def _erode(mask: np.ndarray, square: bool) -> np.ndarray:
    m = mask.copy()
    m[1:] &= mask[:-1]
    m[:-1] &= mask[1:]
    m[:, 1:] &= mask[:, :-1]
    m[:, :-1] &= mask[:, 1:]
    if square:
        m[1:, 1:] &= mask[:-1, :-1]
        m[1:, :-1] &= mask[:-1, 1:]
        m[:-1, 1:] &= mask[1:, :-1]
        m[:-1, :-1] &= mask[1:, 1:]
    return m


def distance_inside(mask: np.ndarray) -> np.ndarray:
    """Distância (aprox. euclidiana) de cada pixel até fora da máscara."""
    d = np.zeros(mask.shape)
    m = mask.copy()
    i = 0
    while m.any():
        d[m] += 1
        m = _erode(m, square=i % 2 == 1)
        i += 1
    return d


def _blur(a: np.ndarray, mask: np.ndarray, passes: int = 1) -> np.ndarray:
    out = a.copy()
    for _ in range(passes):
        acc = np.zeros_like(out)
        cnt = np.zeros_like(out)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                acc += np.roll(np.roll(out * mask, dy, 0), dx, 1)
                cnt += np.roll(np.roll(mask.astype(float), dy, 0), dx, 1)
        out = np.where(mask, acc / np.maximum(cnt, 1), 0)
    return out


def _cool(r: Ramp) -> RGBA:
    """Luz de borda fria padrão: tom médio da rampa puxado para azul."""
    L, C, h = to_lch(r.colors[min(len(r.colors) - 1, r.base)])
    return from_lch(min(0.85, L + 0.08), max(0.05, C * 0.8), 250)


def retone(px: np.ndarray, mask: np.ndarray, ramp: list, hue: tuple[float, float] = (0, 360),
           min_chroma: float = 0.02) -> np.ndarray:
    """Recolore um material numa arte pronta: pixels dentro de `mask`, com matiz OKLCh em
    `hue` (graus) e croma ≥ `min_chroma`, trocam de cor pela posição de luminosidade numa
    nova rampa (escuro → claro). Ex.: pele clara da base → pele parda da ficha, sem tocar
    numa camisa bege de matiz vizinha (use a máscara de região para separar)."""
    from .color import srgb_to_oklab

    out = px.copy()
    cols = [parse_color(c) if isinstance(c, str) else tuple(c) for c in ramp]
    target_L = np.array([float(srgb_to_oklab(np.array(c[:3]))[0]) for c in cols])
    sel = mask & (px[..., 3] > 0)
    if not sel.any():
        return out
    lab = srgb_to_oklab(px[sel][:, :3].astype(float))
    h = (np.degrees(np.arctan2(lab[:, 2], lab[:, 1])) + 360) % 360
    c = np.hypot(lab[:, 1], lab[:, 2])
    lo, hi = hue
    ok = ((h >= lo) & (h <= hi) if lo <= hi else (h >= lo) | (h <= hi)) & (c >= min_chroma)
    L = lab[:, 0]
    Ls = L[ok]
    if not len(Ls):
        return out
    # posição relativa na faixa de luminosidade do material → tom da nova rampa
    lmin, lmax = float(Ls.min()), float(Ls.max())
    rel = (L - lmin) / max(lmax - lmin, 1e-6)
    idx = np.clip(np.round(rel * (len(cols) - 1)), 0, len(cols) - 1).astype(int)
    new = np.array([cols[i][:3] for i in idx], dtype=np.uint8)
    vals = px[sel].copy()
    vals[ok, :3] = new[ok]
    out[sel] = vals
    return out


PARDO = ["#4e2a22", "#6e4030", "#8a5a40", "#a8724e", "#c48a64", "#d6a57e", "#e4bf98"]   # pele parda (escuro → claro)


class Paint:
    @classmethod
    def from_sprite(cls, sprite: Sprite, light=LIGHT, prefix: str = "base", warm: str = "#ec9c5e",
                    cool: str = "#8a96cc") -> "Paint":
        """Carrega uma arte pronta (ex.: base da via de IA) para repintar por código.

        As cores são agrupadas em famílias (mesma faixa de matiz; neutros à parte) e cada
        família vira uma rampa do escuro ao claro — `shift`, `set`, luz de borda e contorno
        seletivo passam a funcionar sobre a arte. Rampas: "<prefix>0", "<prefix>1", …;
        `family_of(cor)` diz a rampa de uma cor."""
        from .color import srgb_to_oklab

        h, w = sprite.pixels.shape[:2]
        p = cls(w, h, light)
        px = sprite.pixels
        opaque = px[..., 3] > 0
        colors, inverse = np.unique(px[opaque][:, :3], axis=0, return_inverse=True)
        lab = srgb_to_oklab(colors.astype(float))
        chroma = np.hypot(lab[:, 1], lab[:, 2])
        hue = (np.degrees(np.arctan2(lab[:, 2], lab[:, 1])) + 360) % 360
        key = np.where(chroma < 0.03, -1, ((hue + 15) % 360 // 30).astype(int))
        p._family = {}
        tone_of = np.zeros(len(colors), int)
        rid_of = np.zeros(len(colors), int)
        for k in sorted(set(key.tolist())):
            idx = [i for i in np.nonzero(key == k)[0]]
            idx.sort(key=lambda i: lab[i, 0])
            ramp_colors = [tuple(int(v) for v in colors[i]) + (255,) for i in idx]
            name = f"{prefix}{len(p.ramps)}"
            base = len(ramp_colors) // 2
            dark = from_lch(*(lambda L, C, hh: (max(0.08, L - 0.12), C, hh))(*to_lch(ramp_colors[0])))
            p.custom_ramp(name, ramp_colors, base, rim=mix(ramp_colors[-1], warm, 0.55), outline=dark,
                          rim2=mix(ramp_colors[len(ramp_colors) // 2], cool, 0.55))
            r = len(p.ramps) - 1
            for t, i in enumerate(idx):
                tone_of[i], rid_of[i] = t, r
                p._family[tuple(int(v) for v in colors[i])] = name
        p.rid[opaque] = rid_of[inverse.reshape(-1)]
        p.tone[opaque] = tone_of[inverse.reshape(-1)]
        return p

    def family_of(self, color) -> str:
        c = parse_color(color) if isinstance(color, str) else tuple(color)
        return self._family[tuple(c[:3])]

    def __init__(self, width: int, height: int, light=LIGHT):
        self.w, self.h = width, height
        self.ys, self.xs = np.mgrid[0:height, 0:width]
        self.rid = np.full((height, width), -1, dtype=np.int32)   # rampa por pixel
        self.tone = np.zeros((height, width), dtype=np.int32)
        self.lock = np.zeros((height, width), dtype=bool)          # sem contorno/AA (ex.: brilho do olho)
        self.ramps: list[Ramp] = []
        self.light = np.asarray(light, dtype=float) / np.linalg.norm(light)

    # -- rampas ---------------------------------------------------------------

    def ramp(self, name: str, color, **kw) -> str:
        r = make_ramp(name, color, **kw)
        for i, old in enumerate(self.ramps):
            if old.name == name:
                self.ramps[i] = r
                return name
        self.ramps.append(r)
        return name

    def custom_ramp(self, name: str, colors: list, base: int, rim=None, outline=None, rim2=None) -> str:
        cs = [parse_color(c) for c in colors]
        r = make_ramp(name, cs[base])
        r.colors, r.base = cs, base
        if rim:
            r.rim = parse_color(rim)
        if outline:
            r.outline = parse_color(outline)
        if rim2:
            r.rim2 = parse_color(rim2)
        self.ramps.append(r)
        return name

    def _r(self, name: str) -> int:
        for i, r in enumerate(self.ramps):
            if r.name == name:
                return i
        raise KeyError(f"rampa '{name}' não existe")

    # -- máscaras ---------------------------------------------------------------

    def ellipse(self, cx, cy, rx, ry) -> np.ndarray:
        return ((self.xs - cx) / max(rx, 0.5)) ** 2 + ((self.ys - cy) / max(ry, 0.5)) ** 2 <= 1.0 + 1e-9

    def rect(self, x0, y0, x1, y1) -> np.ndarray:
        """Inclusivo."""
        return (self.xs >= x0) & (self.xs <= x1) & (self.ys >= y0) & (self.ys <= y1)

    def poly(self, points) -> np.ndarray:
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

    def capsule(self, x0, y0, x1, y1, r0, r1=None) -> np.ndarray:
        """Traço grosso de (x0,y0) a (x1,y1), raio r0 → r1 (membros, mechas)."""
        r1 = r0 if r1 is None else r1
        vx, vy = x1 - x0, y1 - y0
        ll = vx * vx + vy * vy or 1e-9
        t = np.clip(((self.xs - x0) * vx + (self.ys - y0) * vy) / ll, 0, 1)
        dx, dy = self.xs - (x0 + t * vx), self.ys - (y0 + t * vy)
        return dx * dx + dy * dy <= (r0 + (r1 - r0) * t) ** 2 + 1e-9

    def curve(self, points, r0, r1=None, samples=24) -> np.ndarray:
        """Mecha/dobra: capsulas ao longo de uma curva de Bézier quadrática/cúbica."""
        pts = np.array(points, dtype=float)
        n = len(pts) - 1
        ts = np.linspace(0, 1, samples)
        from math import comb
        path = sum(comb(n, i) * ((1 - ts) ** (n - i) * ts ** i)[:, None] * pts[i] for i in range(n + 1))
        r1 = r0 if r1 is None else r1
        m = np.zeros((self.h, self.w), dtype=bool)
        for i in range(samples - 1):
            ra = r0 + (r1 - r0) * i / (samples - 1)
            rb = r0 + (r1 - r0) * (i + 1) / (samples - 1)
            m |= self.capsule(*path[i], *path[i + 1], ra, rb)
        return m

    def moved(self, mask: np.ndarray, dx: int, dy: int) -> np.ndarray:
        """Máscara deslocada (fora = vazio)."""
        out = np.zeros_like(mask)
        h, w = mask.shape
        ys = slice(max(dy, 0), h + min(dy, 0))
        xs = slice(max(dx, 0), w + min(dx, 0))
        yd = slice(max(-dy, 0), h + min(-dy, 0))
        xd = slice(max(-dx, 0), w + min(-dx, 0))
        out[ys, xs] = mask[yd, xd]
        return out

    def crescent(self, mask: np.ndarray, dx: int, dy: int) -> np.ndarray:
        """Faixa da forma que sai de baixo dela mesma deslocada (dx, dy): sombra em
        meia-lua do lado oposto ao deslocamento (cel shading)."""
        return mask & ~self.moved(mask, dx, dy)

    def cel(self, mask: np.ndarray, ramp: str, shadow=(4, 3), core=(2, 2), light=(3, 3), rim: bool = False) -> None:
        """Pinta chapado e recorta sombra, sombra de núcleo e luz em meias-luas.
        Luz de cima à esquerda: sombra vem da direita/baixo."""
        self.set(mask, ramp, 0)
        if shadow:
            self.shift(self.crescent(mask, -shadow[0], -shadow[1]), -1)
        if core:
            self.shift(self.crescent(mask, -core[0], -core[1]) & self.crescent(mask, -shadow[0], -shadow[1]), -1)
        if light:
            self.shift(self.crescent(mask, light[0], light[1]) & ~self.crescent(mask, 1, 1), 1)
        if rim:
            self.rim(mask, self._r(ramp))

    def mask_of(self, ramp: str | None = None) -> np.ndarray:
        return self.rid >= 0 if ramp is None else self.rid == self._r(ramp)

    # -- pintura ------------------------------------------------------------------

    def shading(self, mask: np.ndarray, roundness: float = 1.0, flat: float = 0.0, tilt=(0.0, 0.0)) -> np.ndarray:
        """Luz (−1…1) de uma forma inflada: relevo pela distância até a borda."""
        d = distance_inside(mask)
        if not d.any():
            return np.zeros(mask.shape)
        R = max(2.0, d.max() * 0.85 / max(roundness, 0.1))
        hgt = np.sqrt(np.clip(d, 0, R) / R) * R
        hgt = _blur(hgt, mask, 2)
        gy, gx = np.gradient(hgt)
        nx, ny = -gx + tilt[0], -gy + tilt[1]
        nz = np.full(mask.shape, 1.0 + flat * 3)
        norm = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
        return (nx * self.light[0] + ny * self.light[1] + nz * self.light[2]) / norm

    def fill(self, mask: np.ndarray, ramp: str, tone: int | None = None, roundness: float = 1.0,
             bias: float = 0.0, contrast: float = 1.0, rim: bool = True, flat: float = 0.0,
             levels: tuple = (0.82, 0.6, 0.3, 0.0, -0.3), tilt=(0.0, 0.0), lo: int = -2) -> np.ndarray:
        """Pinta a máscara. Sem `tone`: sombreada pelo relevo (tons base-2 … base+2)."""
        r = self._r(ramp)
        R = self.ramps[r]
        mask = mask & ~self.lock
        self.rid[mask] = r
        if tone is not None:
            self.tone[mask] = R.base + tone
            return mask
        v = self.shading(mask, roundness, flat, tilt) * contrast + bias
        t = np.full(mask.shape, R.base + lo, dtype=np.int32)
        a, b, c, e, f = levels
        t = np.where(v > f, R.base - 1, t)
        t = np.where(v > e, R.base, t)
        t = np.where(v > c, R.base, t)
        t = np.where(v > b, R.base + 1, t)
        t = np.where(v > a, R.base + 2, t)
        self.tone[mask] = np.clip(t[mask], 0, len(R) - 1)
        if rim:
            self.rim(mask, r)
        return mask

    def rim(self, mask: np.ndarray, r: int | None = None, width: int = 1) -> None:
        """Luz de borda fria no lado oposto à luz (baixo/direita da forma)."""
        edge = mask & ~_erode(mask, False)
        if width > 1:
            edge = mask & ~_erode(_erode(mask, False), True)
        away = np.zeros_like(mask)
        ax, ay = -int(np.sign(self.light[0])), -int(np.sign(self.light[1]))
        if ax:
            away |= ~np.roll(mask, -ax, axis=1)
        if ay:
            away |= ~np.roll(mask, -ay, axis=0)
        pick = edge & away & (self.tone <= self.base_of(mask) - 1)
        self.tone[pick] = -1  # marcador: luz de borda

    def rim_light(self, dirs=((-1, 0), (0, -1)), width: int = 1, only: np.ndarray | None = None,
                  reach: int = 6, second: bool = False) -> np.ndarray:
        """Luz de borda na figura inteira: pixel cujo vizinho na direção da luz está
        vazio vira a cor de borda (`rim`) da rampa dele. dirs = de onde vem a luz.
        `reach`: quantos pixels vazios precisa haver naquela direção (fendas estreitas,
        como entre as pernas, não recebem luz)."""
        fig = self.rid >= 0
        edge = np.zeros_like(fig)
        for dx, dy in dirs:
            open_ = np.ones_like(fig)
            for k in range(1, reach + 1):
                open_ &= ~self.moved(fig, -dx * k, -dy * k)
            for k in range(width):
                edge |= self.moved(fig & open_, -dx * k, -dy * k) & fig if k else fig & open_
        if only is not None:
            edge &= only
        edge &= ~self.lock
        self.tone[edge] = -2 if second else -1
        return edge

    def hue_ramp(self, name: str, color, down: int = 3, up: int = 2, hue: float = 18.0,
                 rim=None, outline=None, rim2=None) -> str:
        """Rampa de down+1+up tons com hue shifting forte (`hue` graus por tom):
        sombra puxa para violeta/azul, luz para amarelo."""
        base = parse_color(color) if isinstance(color, str) else tuple(color)
        colors = [shade(base, -(down - i), hue_shift=hue) for i in range(down)] + [base] + \
                 [shade(base, i + 1, hue_shift=hue) for i in range(up)]
        return self.custom_ramp(name, colors, down, rim=rim, outline=outline, rim2=rim2)

    def push_values(self, mask: np.ndarray | None = None, amount: int = 1) -> None:
        """Separa os valores: o que está abaixo da base desce `amount` tons e o que está
        acima sobe — mais contraste sem trocar o desenho."""
        area = (self.rid >= 0) & (self.tone >= 0) & ~self.lock
        if mask is not None:
            area &= mask
        base = self.base_of(area)
        for i, r in enumerate(self.ramps):
            sel = area & (self.rid == i)
            lo = sel & (self.tone < base)
            hi = sel & (self.tone > base)
            self.tone[lo] = np.maximum(self.tone[lo] - amount, 0)
            self.tone[hi] = np.minimum(self.tone[hi] + amount, len(r) - 1)

    def painterly(self, mask: np.ndarray | None = None, edge: float = 0.35, speck: float = 0.06,
                  dither: float = 0.0, seed: int = 0) -> None:
        """Pincelada: mistura pintada nas fronteiras de tom (pixels soltos do tom vizinho
        atravessando a borda) e manchinhas de ±1 tom no miolo. Quebra blocos grandes,
        cria os pixels "órfãos" das referências, sem degradê liso.
        `dither`: fração das fronteiras que ganha um xadrez curto de 2–3 px."""
        rng = np.random.default_rng(seed)
        area = (self.rid >= 0) & (self.tone >= 0) & ~self.lock
        if mask is not None:
            area &= mask
        tone, rid = self.tone.copy(), self.rid
        h, w = area.shape
        out = tone.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nt = np.roll(np.roll(tone, dy, 0), dx, 1)
            nr = np.roll(np.roll(rid, dy, 0), dx, 1)
            border = area & (nr == rid) & (nt >= 0) & (nt != tone)
            pick = border & (rng.random((h, w)) < edge / 4)
            out[pick] = nt[pick]
        interior = area & (out == tone)
        r = rng.random((h, w))
        up = interior & (r < speck / 2)
        dn = interior & (r >= speck / 2) & (r < speck)
        maxt = np.zeros_like(tone)
        for i, ramp in enumerate(self.ramps):
            maxt[rid == i] = len(ramp) - 1
        out[up] = np.minimum(out[up] + 1, maxt[up])
        out[dn] = np.maximum(out[dn] - 1, 0)
        if dither > 0:
            for dy, dx in ((0, 1), (1, 0)):
                nt = np.roll(np.roll(tone, dy, 0), dx, 1)
                nr = np.roll(np.roll(rid, dy, 0), dx, 1)
                border = area & (nr == rid) & (nt >= 0) & (nt != tone)
                ys, xs = np.nonzero(border & (rng.random((h, w)) < dither))
                for y, x in zip(ys, xs):
                    for k in (2, 4):                       # xadrez curto atravessando a borda
                        yy, xx = y - dy * k + dx * (k // 2), x - dx * k + dy * (k // 2)
                        if 0 <= yy < h and 0 <= xx < w and area[yy, xx] and rid[yy, xx] == rid[y, x]:
                            out[yy, xx] = nt[y, x]
        self.tone[area] = out[area]

    def rim_spots(self, zones: list, second: bool = False, dirs=((-1, 0), (0, -1)), width: int = 1) -> np.ndarray:
        """Luz de borda pontual: só dentro das zonas dadas (máscaras ou retângulos
        (x0, y0, x1, y1)) — 3–4 pontos do lado da luz vendem a fonte melhor que uma linha."""
        only = np.zeros((self.h, self.w), dtype=bool)
        for z in zones:
            only |= self.rect(*z) if isinstance(z, tuple) else z
        return self.rim_light(dirs=dirs, width=width, only=only, second=second)

    def texture(self, mask: np.ndarray, delta: int = -1, density: float = 0.25, seed: int = 0,
                stroke: tuple = (2, 1)) -> None:
        """Textura de pincel: traços curtos (stroke = largura, altura) de um tom acima/abaixo."""
        rng = np.random.default_rng(seed)
        sw, sh = stroke
        for y in range(0, self.h, sh + 1):
            for x in range((y // (sh + 1)) % 2, self.w, sw + 1):
                if mask[y, x] and rng.random() < density:
                    self.shift(self.rect(x, y, x + sw - 1, y + sh - 1) & mask, delta)

    def base_of(self, mask: np.ndarray) -> np.ndarray:
        out = np.zeros(mask.shape, dtype=np.int32)
        for i, r in enumerate(self.ramps):
            out[self.rid == i] = r.base
        return out

    def set(self, mask: np.ndarray, ramp: str, tone: int) -> None:
        """Tom fixo relativo à base (0 = cor informada)."""
        mask = mask & ~self.lock
        r = self._r(ramp)
        self.rid[mask] = r
        self.tone[mask] = np.clip(self.ramps[r].base + tone, 0, len(self.ramps[r]) - 1)

    def shift(self, mask: np.ndarray, delta: int, ramp: str | None = None) -> None:
        """Escurece (delta < 0) ou clareia os pixels já pintados, dentro da rampa deles."""
        m = mask & (self.rid >= 0) & ~self.lock
        if ramp is not None:
            m &= self.rid == self._r(ramp)
        rim = m & (self.tone < 0)
        self.tone[rim] = self.base_of(rim)[rim]
        for i, r in enumerate(self.ramps):
            sel = m & (self.rid == i)
            self.tone[sel] = np.clip(self.tone[sel] + delta, 0, len(r) - 1)

    def erase(self, mask: np.ndarray) -> None:
        self.rid[mask & ~self.lock] = -1

    def px(self, x: int, y: int, ramp: str, tone: int, lock: bool = False) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            r = self._r(ramp)
            self.rid[y, x] = r
            self.tone[y, x] = np.clip(self.ramps[r].base + tone, 0, len(self.ramps[r]) - 1)
            if lock:
                self.lock[y, x] = True

    def pixels(self, points, ramp: str, tone: int, lock: bool = False) -> None:
        for x, y in points:
            self.px(int(x), int(y), ramp, tone, lock)

    def line(self, x0, y0, x1, y1, ramp: str, tone: int, only: np.ndarray | None = None) -> None:
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            if only is None or (0 <= x0 < self.w and 0 <= y0 < self.h and only[y0, x0]):
                self.px(x0, y0, ramp, tone)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def glyph(self, x: int, y: int, rows: list[str], keys: dict[str, tuple[str, int]], mirror: bool = False,
              lock: bool = False) -> None:
        """Desenho pixel a pixel: keys = {'k': ('olho', -3), ...}; '.' = não pinta."""
        for j, row in enumerate(rows):
            row = row[::-1] if mirror else row
            for i, ch in enumerate(row):
                if ch in keys:
                    ramp, tone = keys[ch]
                    self.px(x + i, y + j, ramp, tone, lock)

    def separate(self, front: np.ndarray, back_ramp: str | None = None, delta: int = -2) -> None:
        """Linha de separação: pixels de trás encostados na forma da frente escurecem."""
        near = np.zeros_like(front)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            near |= np.roll(np.roll(front, dy, 0), dx, 1)
        self.shift(near & ~front, delta, back_ramp)

    # -- acabamento ------------------------------------------------------------------

    def colors(self) -> np.ndarray:
        out = np.zeros((self.h, self.w, 4), dtype=np.uint8)
        for i, r in enumerate(self.ramps):
            sel = self.rid == i
            if not sel.any():
                continue
            pal = np.array(r.colors + [r.rim, r.rim2 or _cool(r)], dtype=np.uint8)
            t = self.tone[sel].copy()
            t[t == -2] = len(r.colors) + 1
            t[t < 0] = len(r.colors)
            out[sel] = pal[np.clip(t, 0, len(pal) - 1)]
        return out

    def render(self, outline: bool | str = True, aa: bool = True, outline_override: dict | None = None,
               dark_open: bool = False) -> Sprite:
        """outline: True (selout em toda a silhueta), "seletivo" (escuro só no lado da
        sombra; nada encostado na luz de borda) ou False.
        `dark_open`: no seletivo, pixel abaixo do tom base (lado da sombra) encostado no
        fundo fica sem contorno — o próprio material escuro já é a borda (ref 21)."""
        px = self.colors()
        opaque = self.rid >= 0
        if outline == "seletivo":
            out = px.copy()
            h, w = opaque.shape
            for y, x in zip(*np.nonzero(~opaque)):
                best = None
                for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h and opaque[ny, nx]):
                        continue
                    r = self.ramps[self.rid[ny, nx]]
                    t = self.tone[ny, nx]
                    if t == -1 or (dark_open and 0 <= t < r.base):   # luz quente ou lado escuro: sem contorno
                        best = None
                        break
                    col = (outline_override or {}).get(r.name, r.outline)
                    if best is None or sum(col[:3]) < sum(best[:3]):
                        best = col
                if best is not None:
                    out[y, x] = best
            if dark_open:                                   # contorno solto (1 px sem vizinho de contorno) some
                line = (out[..., 3] > 0) & ~opaque
                n = sum(np.roll(np.roll(line, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                        if (dy, dx) != (0, 0))
                out[line & (n == 0)] = 0
            return Sprite(out)
        if outline:
            out = px.copy()
            h, w = opaque.shape
            for y, x in zip(*np.nonzero(~opaque)):
                best = None
                for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and opaque[ny, nx]:
                        r = self.ramps[self.rid[ny, nx]]
                        c = (outline_override or {}).get(r.name, r.outline)
                        # lado da luz (contorno acima/à esquerda da forma): tom um pouco mais claro
                        lit = dy > 0 or dx > 0
                        col = c if not lit else r.colors[0]
                        if best is None or sum(col[:3]) < sum(best[:3]):
                            best = col
                if best is not None:
                    out[y, x] = best
            px = out
            if aa:
                px = self._aa(px, opaque)
        return Sprite(px)

    def _aa(self, px: np.ndarray, opaque: np.ndarray) -> np.ndarray:
        """Anti-alias manual: no degrau do contorno, o pixel de dentro que encosta em
        dois pixels de contorno (um em cima/baixo, outro ao lado) desce um tom."""
        line = (px[..., 3] > 0) & ~opaque
        out = px.copy()
        h, w = opaque.shape
        for y, x in zip(*np.nonzero(opaque & ~self.lock)):
            v = any(0 <= y + d < h and line[y + d, x] for d in (-1, 1))
            hz = any(0 <= x + d < w and line[y, x + d] for d in (-1, 1))
            if v and hz and self.tone[y, x] > 0:
                r = self.ramps[self.rid[y, x]]
                t = self.tone[y, x] if self.tone[y, x] >= 0 else r.base
                out[y, x] = r.colors[max(0, t - 1)]
        return out


# ==========================================================================
# Cenário: pintura direta em RGBA (céu, nuvens, folhagem, reflexo, brilho)
# ==========================================================================


def mix(a, b, t: float) -> RGBA:
    """Mistura duas cores (t = 0 → a, 1 → b)."""
    a = parse_color(a) if isinstance(a, str) else tuple(a)
    b = parse_color(b) if isinstance(b, str) else tuple(b)
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3)) + (255,)  # type: ignore[return-value]


class Scene(Paint):
    """Tela de cenário. Herda as máscaras do Paint (ellipse, rect, poly, curve…) e
    pinta cor direto, em camadas de trás para a frente.

        s = Scene(320, 180, seed=3)
        s.sky(["#3a2a4a", "#7a3e5c", "#c85a5a", "#f08a50"], 0, 110)
        s.clouds(60, 30, 90, 18, "#ffb38a", "#d8708a", "#8a4a6e")
        far = s.haze("#5a4a6a", 0.6)                 # cor de longe: clara, azulada, pouco contraste
        s.reflect(110, 150, 150)                     # chão molhado
        s.glow(200, 90, 10, "#ffd08a")
        s.frame("esquerda", "#140c16")               # silhueta em primeiro plano
        s.particles(20, ["#ffd08a"], s.rect(0, 0, 320, 120))
    """

    def __init__(self, width: int, height: int, seed: int = 0, haze_color: str = "#c8a0b8"):
        super().__init__(width, height)
        self.img = np.zeros((height, width, 4), dtype=np.uint8)
        self.rng = np.random.default_rng(seed)
        self.haze_color = parse_color(haze_color)

    # -- básicos ---------------------------------------------------------------

    def put(self, mask: np.ndarray, color) -> None:
        self.img[mask] = parse_color(color) if isinstance(color, str) else tuple(color)

    def haze(self, color, depth: float) -> RGBA:
        """Perspectiva atmosférica: quanto mais longe (depth 0–1), mais perto da cor do ar."""
        return mix(color, self.haze_color, max(0.0, min(1.0, depth)))

    def blocky(self, cell: int = 4, seed: int | None = None) -> np.ndarray:
        """Ruído em blocos (0–1) do tamanho da tela; cada célula cell×cell tem um valor."""
        rng = np.random.default_rng(seed) if seed is not None else self.rng
        small = rng.random((self.h // cell + 2, self.w // cell + 2))
        return np.kron(small, np.ones((cell, cell)))[: self.h, : self.w]

    def sprite(self) -> Sprite:
        return Sprite(self.img.copy())

    def paste(self, sprite: Sprite, x: int, y: int) -> None:
        h, w = sprite.height, sprite.width
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.w), min(y + h, self.h)
        if x0 >= x1 or y0 >= y1:
            return
        src = sprite.pixels[y0 - y:y1 - y, x0 - x:x1 - x]
        m = src[..., 3] > 0
        self.img[y0:y1, x0:x1][m] = src[m]

    # -- céu e nuvens -----------------------------------------------------------

    def sky(self, bands: list, y0: int, y1: int, wobble: int = 3, step: int = 6) -> None:
        """Céu em faixas largas de cor (de cima para baixo), com bordas em degraus
        irregulares — manchas grandes, nada de degradê liso."""
        n = len(bands)
        edges = [y0 + (y1 - y0) * (i + 1) / n for i in range(n - 1)]
        offs = [np.repeat(self.rng.integers(-wobble, wobble + 1, self.w // step + 2), step)[: self.w] for _ in edges]
        for x in range(self.w):
            for y in range(y0, y1):
                i = sum(y >= e + o[x] for e, o in zip(edges, offs))
                self.img[y, x] = parse_color(bands[i]) if isinstance(bands[i], str) else bands[i]

    def streaks(self, y0: int, y1: int, color, count: int = 8, length=(12, 40)) -> None:
        """Nuvens finas horizontais (riscos) para o céu de fim de tarde."""
        for _ in range(count):
            y = int(self.rng.integers(y0, y1))
            x = int(self.rng.integers(-10, self.w))
            L = int(self.rng.integers(*length))
            self.put(self.rect(x, y, x + L, y), color)
            if L > 18:
                self.put(self.rect(x + 3, y + 1, x + L - 6, y + 1), color)

    def clouds(self, cx: float, cy: float, w: float, h: float, light, mid, shadow, puffs: int = 7,
               block: int = 2) -> np.ndarray:
        """Nuvem em blocos: bolhas somadas, topo iluminado, base chata e na sombra."""
        m = np.zeros((self.h, self.w), dtype=bool)
        for i in range(puffs * 2):                                       # bolhas sobrepostas, mais altas no meio
            t = self.rng.uniform(0.05, 0.95)
            px = cx - w / 2 + w * t
            bell = 0.35 + 0.65 * np.sin(np.pi * t)
            r = h * bell * self.rng.uniform(0.45, 0.85)
            m |= self.ellipse(px, cy - r * 0.5 - self.rng.uniform(0, h * 0.25) * bell, r * 1.5, r)
        m |= self.ellipse(cx, cy, w * 0.48, h * 0.3)                       # corpo contínuo
        m &= self.ys <= cy + h * 0.25                                   # base chata
        if block > 1:                                                    # pixels em blocos
            small = m[::block, ::block]
            m = np.kron(small, np.ones((block, block), dtype=bool))[: self.h, : self.w]
        self.put(m, mid)
        self.put(m & ~self.moved(m, 0, block * 2), light)                 # topo na luz
        self.put(m & (self.ys >= cy + h * 0.05), shadow)                 # base na sombra
        self.put(m & self.crescent(m, -block * 2, 0) & (self.ys < cy), mix(mid, shadow, 0.5))
        return m

    # -- textura e vegetação ---------------------------------------------------

    def cluster(self, mask: np.ndarray, colors: list, density: float = 0.3, size=(1, 3)) -> None:
        """Pincel de cluster: manchinhas de 1–3 px das cores dadas dentro da máscara."""
        ys, xs = np.nonzero(mask)
        if not len(xs):
            return
        n = int(len(xs) * density / ((size[0] + size[1]) / 2) ** 2)
        for _ in range(n):
            i = int(self.rng.integers(len(xs)))
            s = int(self.rng.integers(size[0], size[1] + 1))
            c = colors[int(self.rng.integers(len(colors)))]
            self.put(self.rect(xs[i], ys[i], xs[i] + s - 1, ys[i] + max(1, s - 1) - 1) & mask, c)

    def foliage(self, cx: float, cy: float, r: float, colors: list, clumps: int = 40,
                holes: bool = True) -> np.ndarray:
        """Copa de árvore/arbusto: tufos pequenos, escuro embaixo e claro em cima
        (colors do escuro ao claro); borda recortada com folhas soltas."""
        before = self.img.copy()
        m = np.zeros((self.h, self.w), dtype=bool)
        tufts = []
        for _ in range(clumps):
            a = self.rng.uniform(0, 2 * np.pi)
            d = r * np.sqrt(self.rng.uniform(0, 1))
            x, y = cx + np.cos(a) * d, cy + np.sin(a) * d * 0.85
            s = self.rng.uniform(r * 0.18, r * 0.35)
            t = self.ellipse(x, y, s * 1.2, s * 0.9)
            tufts.append((y, t))
            m |= t
        for y, t in sorted(tufts, key=lambda v: -v[0]):                    # de baixo para cima
            light = (cy - y) / (r * 1.7) + 0.5
            i = int(np.clip(light * len(colors), 0, len(colors) - 1))
            self.put(t, colors[i])
            self.put(t & ~self.moved(t, 0, 1) & ~self.moved(t, 1, 0), colors[min(i + 1, len(colors) - 1)])
        if holes:
            edge = m & ~self.moved(m, 0, 2) & ~self.moved(m, 2, 0)
            ys, xs = np.nonzero(edge)
            for i in self.rng.choice(len(xs), size=min(len(xs), len(xs) // 4), replace=False):
                self.img[ys[i], xs[i]] = before[ys[i], xs[i]]                    # folha solta: vê o fundo
        return m

    def frame(self, side: str, color, height: float = 0.6, seed: int | None = None,
              count: int | None = None) -> np.ndarray:
        """Moldura de silhueta em primeiro plano: galhos e folhas escuras entrando pela
        borda (side: esquerda, direita, topo, baixo)."""
        rng = np.random.default_rng(seed) if seed is not None else self.rng
        m = np.zeros((self.h, self.w), dtype=bool)
        W, H = self.w, self.h
        if side in ("esquerda", "direita"):
            x0 = 0 if side == "esquerda" else W - 1
            sgn = 1 if side == "esquerda" else -1
            for _ in range(int(14 * height) + 6):
                y = rng.uniform(0, H * height)
                reach = rng.uniform(W * 0.04, W * 0.18)
                m |= self.curve([(x0, y), (x0 + sgn * reach * 0.6, y + rng.uniform(-8, 8)),
                                 (x0 + sgn * reach, y + rng.uniform(0, 14))], rng.uniform(0.5, 1.4), 0.4)
                for _ in range(6):                                          # folhas na ponta
                    lx = x0 + sgn * reach * rng.uniform(0.4, 1.1)
                    ly = y + rng.uniform(-6, 16)
                    m |= self.ellipse(lx, ly, rng.uniform(1.5, 4), rng.uniform(1, 2.5))
        else:
            y0 = H - 1 if side == "baixo" else 0
            sgn = -1 if side == "baixo" else 1
            for _ in range(count or int(W / 8)):
                x = rng.uniform(0, W)
                hgt = rng.uniform(H * 0.04, H * 0.16) * height / 0.6
                m |= self.capsule(x, y0, x + rng.uniform(-4, 4), y0 + sgn * hgt, rng.uniform(0.5, 1.5), 0.3)
                m |= self.ellipse(x + rng.uniform(-3, 3), y0 + sgn * hgt, rng.uniform(1.5, 3.5), rng.uniform(1, 2.5))
        self.put(m, color)
        return m

    # -- água, luz e vida -----------------------------------------------------

    def reflect(self, src_bottom: int, dst_top: int, dst_bottom: int, strength: float = 0.55,
                water=None, gap: int = 3, x0: int = 0, x1: int | None = None) -> None:
        """Reflexo em faixas horizontais quebradas: espelha o que está acima de
        `src_bottom` na faixa [dst_top, dst_bottom), misturando com a água."""
        x1 = self.w if x1 is None else x1
        src = self.img.copy()
        for k, y in enumerate(range(dst_top, dst_bottom)):
            sy = src_bottom - 1 - k
            if sy < 0:
                break
            if k % gap == gap - 1 and k > 2:                                    # faixa quebrada
                continue
            shift = int(self.rng.integers(-1, 2)) * (k // 6)
            row = np.roll(src[sy, x0:x1], shift, axis=0)
            t = strength * (1 - k / max(dst_bottom - dst_top, 1) * 0.6)
            base = self.img[y, x0:x1].astype(float) if water is None else \
                np.tile(np.array(parse_color(water), float), (x1 - x0, 1))
            keep = np.ones(x1 - x0, dtype=bool)                                   # trechos com falhas
            x = int(self.rng.integers(0, 12))
            while x < x1 - x0:
                seg = int(self.rng.integers(8, 28)) - min(k // 2, 6)
                x += max(seg, 3)
                gapw = int(self.rng.integers(1, 3 + k // 6))
                keep[x:x + gapw] = False
                x += gapw
            mixed = base * (1 - t) + row.astype(float) * t
            self.img[y, x0:x1][keep, :3] = np.round(mixed[keep, :3]).astype(np.uint8)
            self.img[y, x0:x1, 3] = 255

    def glow(self, cx: float, cy: float, r: float, color, core=None, rings: int = 3) -> None:
        """Brilho com halo: anéis quantizados (não degradê) clareando o que está atrás."""
        color = parse_color(color) if isinstance(color, str) else color
        for i in range(rings, 0, -1):
            m = self.ellipse(cx, cy, r * i / rings, r * i / rings)
            t = 0.18 + 0.5 * (rings - i) / rings
            sel = m & (self.img[..., 3] > 0)
            self.img[sel, :3] = np.round(self.img[sel, :3] * (1 - t) + np.array(color[:3]) * t).astype(np.uint8)
        if core:
            self.put(self.ellipse(cx, cy, max(0.6, r / 6), max(0.6, r / 6)), core)

    def particles(self, n: int, colors: list, area: np.ndarray, plus: float = 0.15) -> None:
        """Partículas luminosas (vagalumes, brasas, gotas, neve): 1 px, algumas em cruz."""
        ys, xs = np.nonzero(area)
        if not len(xs):
            return
        for _ in range(n):
            i = int(self.rng.integers(len(xs)))
            c = colors[int(self.rng.integers(len(colors)))]
            x, y = int(xs[i]), int(ys[i])
            self.put(self.rect(x, y, x, y), c)
            if self.rng.random() < plus:
                dim = mix(c, self.img[y, min(x + 2, self.w - 1)], 0.5)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if 0 <= x + dx < self.w and 0 <= y + dy < self.h:
                        self.img[y + dy, x + dx] = dim

    def wire(self, x0: float, y0: float, x1: float, y1: float, sag: float, color) -> None:
        """Fio pendurado (fio elétrico, varal): parábola de 1 px."""
        n = int(abs(x1 - x0)) + 1
        prev = None
        for i in range(n + 1):
            t = i / n
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
            pt = (int(round(x)), int(round(y)))
            if prev:
                self.line_rgba(*prev, *pt, color)
            prev = pt

    def line_rgba(self, x0, y0, x1, y1, color) -> None:
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        c = parse_color(color) if isinstance(color, str) else color
        while True:
            if 0 <= x0 < self.w and 0 <= y0 < self.h:
                self.img[y0, x0] = c
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
