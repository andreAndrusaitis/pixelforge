"""Aseprite: exportação de sprite sheet + JSON e leitura/escrita de `.ase`/`.aseprite`.

- `export_sheet`: PNG + JSON no formato que o Aseprite exporta ("frames" em lista,
  `meta.frameTags` com as animações, `meta.slices` com o pivô = `anchor`). Importadores
  de Godot e Unity que leem o JSON do Aseprite entendem este arquivo; a folha
  também é uma grade regular (uma linha por animação) para quem fatiar por tamanho.
- `read_ase`: parser próprio do formato binário (RGBA, tons de cinza e indexado;
  camadas visíveis compostas com opacidade, modo normal; tags → animations).
- `write_ase`: grava `.aseprite` RGBA (camadas, quadros, tags) para retoque no Aseprite.
- `read_sheet_json`: lê de volta um JSON + PNG exportado (pelo Aseprite ou por nós).

Formato binário: https://github.com/aseprite/aseprite/blob/main/docs/ase-file-specs.md
"""

from __future__ import annotations

import json
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image

from .animate import animations_of
from .sprite import Art, Sprite

MAGIC_FILE = 0xA5E0
MAGIC_FRAME = 0xF1FA
CHUNK_OLD_PALETTE_4 = 0x0004
CHUNK_OLD_PALETTE_11 = 0x0011
CHUNK_LAYER = 0x2004
CHUNK_CEL = 0x2005
CHUNK_TAGS = 0x2018
CHUNK_PALETTE = 0x2019
CHUNK_SLICE = 0x2022
DIRECTIONS = ["forward", "reverse", "pingpong", "pingpong_reverse"]


class AseError(ValueError):
    pass


# --------------------------------------------------------------------------
# Exportação: sheet + JSON
# --------------------------------------------------------------------------


def sheet_layout(art: Art) -> list[tuple[str, list[int], int]]:
    """[(animação, índices dos quadros, fps)]; sem animations → uma linha 'parado'."""
    return [(name, list(a["frames"]), int(a.get("fps", art.fps))) for name, a in animations_of(art).items()]


def export_sheet(art: Art, out_dir: str | Path, name: str | None = None, layout: str = "linhas",
                 scale: int = 1) -> tuple[Path, Path]:
    """Grava <nome>.png e <nome>.json. layout: 'linhas' (uma linha por animação)
    ou 'horizontal' (todas numa linha)."""
    if layout not in ("linhas", "horizontal"):
        raise ValueError("layout deve ser 'linhas' ou 'horizontal'")
    if scale < 1:
        raise ValueError("escala deve ser >= 1")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = name or art.name
    w, h = art.size
    sw, sh = w * scale, h * scale
    rows = sheet_layout(art)
    if layout == "horizontal":
        flat = [i for _, frames, _ in rows for i in frames]
        grid = [flat]
    else:
        grid = [frames for _, frames, _ in rows]
    cols = max(len(r) for r in grid)
    sheet = np.zeros((len(grid) * sh, cols * sw, 4), dtype=np.uint8)
    frames_json, tags = [], []
    k = 0
    durations = [round(1000 / max(fps, 1)) for _, frames, fps in rows for _ in frames]
    anchor = art.meta.get("anchor")
    for r, row in enumerate(grid):
        for c, idx in enumerate(row):
            px = art.frames[idx].pixels
            if scale > 1:
                px = px.repeat(scale, axis=0).repeat(scale, axis=1)
            sheet[r * sh:(r + 1) * sh, c * sw:(c + 1) * sw] = px
            frames_json.append({
                "filename": f"{name} {k}.aseprite",
                "frame": {"x": c * sw, "y": r * sh, "w": sw, "h": sh},
                "rotated": False, "trimmed": False,
                "spriteSourceSize": {"x": 0, "y": 0, "w": sw, "h": sh},
                "sourceSize": {"w": sw, "h": sh},
                "duration": durations[k],
            })
            k += 1
    start = 0
    for anim, frames, _ in rows:
        tags.append({"name": anim, "from": start, "to": start + len(frames) - 1, "direction": "forward",
                     "color": "#000000ff"})
        start += len(frames)
    meta = {
        "app": "pixelforge", "version": "1", "image": f"{name}.png", "format": "RGBA8888",
        "size": {"w": sheet.shape[1], "h": sheet.shape[0]}, "scale": str(scale),
        "frameTags": tags, "layers": [{"name": "arte", "opacity": 255, "blendMode": "normal"}], "slices": [],
    }
    if anchor:
        meta["slices"].append({"name": "anchor", "color": "#0000ffff", "keys": [{
            "frame": 0, "bounds": {"x": 0, "y": 0, "w": sw, "h": sh},
            "pivot": {"x": int(anchor[0]) * scale, "y": int(anchor[1]) * scale}}]})
    png = out_dir / f"{name}.png"
    Image.fromarray(sheet, "RGBA").save(png)
    js = out_dir / f"{name}.json"
    js.write_text(json.dumps({"frames": frames_json, "meta": meta}, indent=1, ensure_ascii=False), encoding="utf-8")
    return png, js


def read_sheet_json(path: str | Path) -> Art:
    """Lê JSON (lista ou dicionário de frames) + a imagem citada em meta.image."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AseError(f"{path}: JSON inválido ({exc})") from None
    frames = data.get("frames")
    meta = data.get("meta") or {}
    if isinstance(frames, dict):
        frames = list(frames.values())
    if not frames or "image" not in meta:
        raise AseError(f"{path}: não parece um JSON do Aseprite (faltam 'frames' ou 'meta.image')")
    image_path = path.parent / meta["image"]
    if not image_path.is_file():
        raise FileNotFoundError(f"imagem da folha não encontrada: {image_path}")
    with Image.open(image_path) as im:
        sheet = np.array(im.convert("RGBA"), dtype=np.uint8)
    sprites, durations = [], []
    for f in frames:
        src = f["sourceSize"]
        fr, ss = f["frame"], f.get("spriteSourceSize", {"x": 0, "y": 0})
        if f.get("rotated"):
            raise AseError(f"{path}: quadros rotacionados não são suportados")
        canvas = np.zeros((src["h"], src["w"], 4), dtype=np.uint8)
        piece = sheet[fr["y"]:fr["y"] + fr["h"], fr["x"]:fr["x"] + fr["w"]]
        canvas[ss["y"]:ss["y"] + piece.shape[0], ss["x"]:ss["x"] + piece.shape[1]] = piece
        sprites.append(Sprite(canvas))
        durations.append(int(f.get("duration", 100)))
    tags = [(t["name"], t["from"], t["to"], t.get("direction", "forward")) for t in meta.get("frameTags", [])]
    art = _with_tags(path.stem, sprites, durations, tags)
    for s in meta.get("slices", []):
        if s.get("name") == "anchor" and s.get("keys") and "pivot" in s["keys"][0]:
            pv = s["keys"][0]["pivot"]
            scale = int(meta.get("scale", "1") or 1)
            art.meta["anchor"] = [int(pv["x"]) // scale, int(pv["y"]) // scale]
            if scale > 1:
                art.frames = [Sprite(f.pixels[::scale, ::scale].copy()) for f in art.frames]
    return art


def _fps(durations: list[int]) -> int:
    return max(1, round(1000 / (sum(durations) / len(durations)))) if durations else 8


def _with_tags(name: str, sprites: list[Sprite], durations: list[int], tags: list[tuple]) -> Art:
    """Monta Art com animations a partir de tags (from, to, direção).

    Com tags, quadros idênticos são guardados uma vez só (as animações apontam para eles).
    """
    art = Art(name, sprites, _fps(durations))
    if tags:
        unique: dict[bytes, int] = {}
        remap = [unique.setdefault(s.pixels.tobytes(), len(unique)) for s in sprites]
        kept = {}
        for i, j in enumerate(remap):
            kept.setdefault(j, sprites[i])
        art.frames = [kept[j] for j in range(len(kept))]
        anims = {}
        for tag_name, start, end, direction in tags:
            idx = list(range(start, end + 1))
            if direction in ("reverse", 1):
                idx = idx[::-1]
            elif direction in ("pingpong", 2):
                idx = idx + idx[-2:0:-1]
            elif direction in ("pingpong_reverse", 3):
                idx = idx[::-1] + idx[1:-1]
            anims[tag_name] = {"frames": [remap[i] for i in idx], "fps": _fps([durations[i] for i in range(start, end + 1)])}
        art.meta["animations"] = anims
    return art


# --------------------------------------------------------------------------
# Leitura do binário .ase / .aseprite
# --------------------------------------------------------------------------


class _Reader:
    def __init__(self, data: bytes, pos: int = 0):
        self.data, self.pos = data, pos

    def take(self, fmt: str):
        size = struct.calcsize("<" + fmt)
        if self.pos + size > len(self.data):
            raise AseError("arquivo truncado")
        values = struct.unpack_from("<" + fmt, self.data, self.pos)
        self.pos += size
        return values if len(values) > 1 else values[0]

    def bytes(self, n: int) -> bytes:
        if self.pos + n > len(self.data):
            raise AseError("arquivo truncado")
        out = self.data[self.pos:self.pos + n]
        self.pos += n
        return out

    def string(self) -> str:
        n = self.take("H")
        return self.bytes(n).decode("utf-8", errors="replace")


@dataclass
class AseLayer:
    name: str
    flags: int
    kind: int
    level: int
    opacity: int
    blend: int

    @property
    def visible(self) -> bool:
        return bool(self.flags & 1)


@dataclass
class AseFile:
    width: int
    height: int
    depth: int
    transparent_index: int
    layers: list[AseLayer] = field(default_factory=list)
    frames: list[dict[int, tuple]] = field(default_factory=list)  # camada → (x, y, opacidade, pixels)
    durations: list[int] = field(default_factory=list)
    tags: list[tuple] = field(default_factory=list)
    palette: list[tuple[int, int, int, int]] = field(default_factory=list)
    layer_opacity_valid: bool = True


def parse_ase(data: bytes) -> AseFile:
    r = _Reader(data)
    _size, magic, nframes, width, height, depth, flags, _speed = r.take("IHHHHHIH")
    if magic != MAGIC_FILE:
        raise AseError("não é um arquivo do Aseprite (assinatura inválida)")
    if depth not in (8, 16, 32):
        raise AseError(f"profundidade de cor {depth} não suportada")
    r.take("II")
    transparent = r.take("B")
    r.bytes(3)
    r.take("H")
    r.bytes(128 - r.pos)
    ase = AseFile(width, height, depth, transparent, layer_opacity_valid=bool(flags & 1))
    ase.palette = [(0, 0, 0, 0)] * 256

    for f in range(nframes):
        start = r.pos
        frame_size, fmagic, old_chunks, duration = r.take("IHHH")
        if fmagic != MAGIC_FRAME:
            raise AseError(f"quadro {f}: assinatura inválida")
        r.bytes(2)
        new_chunks = r.take("I")
        nchunks = new_chunks or old_chunks
        cels: dict[int, tuple] = {}
        for _ in range(nchunks):
            cstart = r.pos
            csize, ctype = r.take("IH")
            body = _Reader(data[cstart + 6:cstart + csize])
            if ctype == CHUNK_LAYER:
                lflags, kind, level, _dw, _dh, blend, opacity = body.take("HHHHHHB")
                body.bytes(3)
                ase.layers.append(AseLayer(body.string(), lflags, kind, level, opacity, blend))
            elif ctype == CHUNK_CEL:
                cel = _parse_cel(body, ase, f)
                if cel is not None:
                    cels[cel[0]] = cel[1:]
            elif ctype == CHUNK_TAGS:
                ntags = body.take("H")
                body.bytes(8)
                for _ in range(ntags):
                    t_from, t_to, direction, _repeat = body.take("HHBH")
                    body.bytes(6 + 3 + 1)
                    ase.tags.append((body.string(), t_from, t_to, DIRECTIONS[direction] if direction < 4 else "forward"))
            elif ctype == CHUNK_PALETTE:
                _n, first, last = body.take("III")
                body.bytes(8)
                for i in range(first, last + 1):
                    pflags, red, green, blue, alpha = body.take("HBBBB")
                    if pflags & 1:
                        body.string()
                    if i < 256:
                        ase.palette[i] = (red, green, blue, alpha)
            elif ctype in (CHUNK_OLD_PALETTE_4, CHUNK_OLD_PALETTE_11) and not any(ase.palette[1:]):
                packets = body.take("H")
                i = 0
                for _ in range(packets):
                    skip, count = body.take("BB")
                    i += skip
                    for _ in range(count or 256):
                        red, green, blue = body.take("BBB")
                        if ctype == CHUNK_OLD_PALETTE_11:
                            red, green, blue = (v * 255 // 63 for v in (red, green, blue))
                        if i < 256:
                            ase.palette[i] = (red, green, blue, 255)
                        i += 1
            r.pos = cstart + csize
        ase.frames.append(cels)
        ase.durations.append(duration)
        r.pos = start + frame_size
    return ase


def _parse_cel(body: _Reader, ase: AseFile, frame: int):
    layer, x, y, opacity, ctype, _z = body.take("HhhBHh")
    body.bytes(5)
    if ctype == 1:  # linkado
        linked = body.take("H")
        src = ase.frames[linked].get(layer) if linked < len(ase.frames) else None
        return (layer, *src) if src else None
    if ctype not in (0, 2):
        return None  # tilemap: ignorado
    w, h = body.take("HH")
    raw = body.bytes(len(body.data) - body.pos)
    if ctype == 2:
        try:
            raw = zlib.decompress(raw)
        except zlib.error as exc:
            raise AseError(f"quadro {frame}: cel comprimido inválido ({exc})") from None
    bpp = ase.depth // 8
    if len(raw) < w * h * bpp:
        raise AseError(f"quadro {frame}: cel com dados incompletos")
    buf = np.frombuffer(raw[:w * h * bpp], dtype=np.uint8)
    if ase.depth == 32:
        px = buf.reshape(h, w, 4).copy()
    elif ase.depth == 16:
        g = buf.reshape(h, w, 2)
        px = np.dstack([g[..., 0], g[..., 0], g[..., 0], g[..., 1]])
    else:
        idx = buf.reshape(h, w)
        pal = np.array(ase.palette, dtype=np.uint8)
        px = pal[idx].copy()
        px[idx == ase.transparent_index] = 0
    return layer, x, y, opacity, px


def compose_frame(ase: AseFile, frame: int) -> Sprite:
    """Compõe as camadas visíveis (modo normal) de um quadro."""
    out = np.zeros((ase.height, ase.width, 4), dtype=np.float64)
    visible_stack: list[bool] = []
    for i, layer in enumerate(ase.layers):
        visible_stack = visible_stack[:layer.level]
        parent_visible = all(visible_stack)
        visible_stack.append(layer.visible)
        if layer.kind != 0 or not (layer.visible and parent_visible) or i not in ase.frames[frame]:
            continue
        x, y, cel_opacity, px = ase.frames[frame][i]
        opacity = (cel_opacity / 255) * ((layer.opacity / 255) if ase.layer_opacity_valid else 1)
        h, w = px.shape[:2]
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, ase.width), min(y + h, ase.height)
        if x0 >= x1 or y0 >= y1:
            continue
        src = px[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float64)
        dst = out[y0:y1, x0:x1]
        sa = src[..., 3:4] / 255 * opacity
        da = dst[..., 3:4] / 255
        oa = sa + da * (1 - sa)
        with np.errstate(invalid="ignore", divide="ignore"):
            rgb = np.where(oa > 0, (src[..., :3] * sa + dst[..., :3] * da * (1 - sa)) / oa, 0)
        dst[..., :3] = rgb
        dst[..., 3:4] = oa * 255
    result = np.clip(np.round(out), 0, 255).astype(np.uint8)
    result[result[..., 3] == 0] = 0
    return Sprite(result)


def read_ase(path: str | Path) -> Art:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"arquivo não encontrado: {path}")
    try:
        ase = parse_ase(path.read_bytes())
    except AseError as exc:
        raise AseError(f"{path}: {exc}") from None
    sprites = [compose_frame(ase, i) for i in range(len(ase.frames))]
    art = _with_tags(path.stem, sprites, ase.durations, ase.tags)
    art.meta["aseprite"] = {"camadas": [layer.name for layer in ase.layers if layer.kind == 0]}
    return art


# --------------------------------------------------------------------------
# Escrita do binário (RGBA)
# --------------------------------------------------------------------------


def _string(s: str) -> bytes:
    b = s.encode("utf-8")
    return struct.pack("<H", len(b)) + b


def _chunk(ctype: int, body: bytes) -> bytes:
    return struct.pack("<IH", len(body) + 6, ctype) + body


def write_ase(path: str | Path, layers: list[tuple[str, list[Sprite]]], durations: list[int],
              tags: list[tuple[str, int, int]] = ()) -> Path:
    """Grava .aseprite RGBA. layers = [(nome, [quadro0, quadro1, ...])], de baixo para cima."""
    if not layers or not layers[0][1]:
        raise AseError("nada para gravar")
    nframes = len(layers[0][1])
    if any(len(frames) != nframes for _, frames in layers) or len(durations) != nframes:
        raise AseError("todas as camadas precisam do mesmo número de quadros (e uma duração por quadro)")
    h, w = layers[0][1][0].pixels.shape[:2]
    frames_bytes = []
    for f in range(nframes):
        chunks = []
        if f == 0:
            for name, _ in layers:
                chunks.append(_chunk(CHUNK_LAYER, struct.pack("<HHHHHHB", 3, 0, 0, 0, 0, 0, 255) + bytes(3)
                                     + _string(name)))
            if tags:
                body = struct.pack("<H", len(tags)) + bytes(8)
                for name, start, end in tags:
                    body += struct.pack("<HHBH", start, end, 0, 0) + bytes(6) + bytes(3) + bytes(1) + _string(name)
                chunks.append(_chunk(CHUNK_TAGS, body))
        for li, (_, frames) in enumerate(layers):
            px = frames[f].pixels
            opaque = px[..., 3] > 0
            if not opaque.any():
                continue
            ys, xs = np.nonzero(opaque)
            x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
            crop = np.ascontiguousarray(px[y0:y1, x0:x1])
            body = struct.pack("<HhhBHh", li, int(x0), int(y0), 255, 2, 0) + bytes(5)
            body += struct.pack("<HH", x1 - x0, y1 - y0) + zlib.compress(crop.tobytes())
            chunks.append(_chunk(CHUNK_CEL, body))
        content = b"".join(chunks)
        header = struct.pack("<IHHH", 16 + len(content), MAGIC_FRAME, min(len(chunks), 0xFFFF),
                             int(durations[f])) + bytes(2) + struct.pack("<I", len(chunks))
        frames_bytes.append(header + content)
    body = b"".join(frames_bytes)
    header = struct.pack("<IHHHHHIH", 128 + len(body), MAGIC_FILE, nframes, w, h, 32, 1,
                         int(durations[0])) + struct.pack("<II", 0, 0) + bytes([0]) + bytes(3)
    header += struct.pack("<H", 0) + bytes([1, 1]) + struct.pack("<hhHH", 0, 0, 16, 16)
    header += bytes(128 - len(header))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + body)
    return path


def art_to_ase(art: Art, path: str | Path, layer_maps: list[np.ndarray] | None = None,
               layer_names: tuple[str, ...] = ()) -> Path:
    """Arte → .aseprite. Com `layer_maps` (personagem), separa em camadas.

    As animações viram tags; como uma tag é um intervalo contínuo, os quadros
    são desenrolados na ordem das animações (um quadro pode aparecer repetido).
    """
    rows = sheet_layout(art)
    order = [i for _, frames, _ in rows for i in frames]
    durations = [round(1000 / max(fps, 1)) for _, frames, fps in rows for _ in frames]
    tags, start = [], 0
    for name, frames, _ in rows:
        tags.append((name, start, start + len(frames) - 1))
        start += len(frames)
    if layer_maps is None:
        layers = [("arte", [art.frames[i] for i in order])]
    else:
        layers = []
        for li, lname in enumerate(layer_names):
            frames = []
            for i in order:
                px = np.zeros_like(art.frames[i].pixels)
                mask = layer_maps[i] == li
                px[mask] = art.frames[i].pixels[mask]
                frames.append(Sprite(px))
            if any(f.pixels[..., 3].any() for f in frames):
                layers.append((lname, frames))
    return write_ase(path, layers, durations, tags)
