"""Operações da API do estúdio (independentes de HTTP, para testar direto).

Caminhos chegam sempre relativos à raiz do repositório e passam por
`Studio.path()`, que recusa qualquer coisa fora dela.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import json
import re
import threading
from pathlib import Path

from PIL import Image, ImageDraw

from .. import palettes as pal
from ..config import Config
from ..export import ExportOptions, export, preview, upscale
from ..library import ART_SUFFIXES, Library, load_art_file, split_version
from ..sprite import SPEC_KEYS, SpecError, dump_spec, parse_spec, spec_from_art

READABLE_DIRS = ("art", "out", "refs", "pedidos")
WRITABLE_DIRS = ("art",)
PROTECTED_DIRS = ("art/examples",)
VIDEO_SUFFIXES = (".mp4", ".webm", ".webp", ".gif")
MAX_MARKS = 50


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


class Studio:
    def __init__(self, config: Config):
        self.config = config
        self.root = Path(config.root).resolve()
        self.library = Library.from_config(config)
        self.lock = threading.RLock()
        self._timelines: dict[tuple[str, float], object] = {}

    # ------------------------------------------------------------------
    # caminhos
    # ------------------------------------------------------------------

    def path(self, rel: str, dirs: tuple[str, ...] = READABLE_DIRS, must_exist: bool = True) -> Path:
        if not rel or not isinstance(rel, str):
            raise ApiError("caminho vazio")
        rel = rel.replace("\\", "/").strip()
        if rel.startswith("/") or re.match(r"^[a-zA-Z]:", rel) or "\0" in rel:
            raise ApiError(f"caminho deve ser relativo ao repositório: {rel}", 403)
        target = (self.root / rel).resolve()
        try:
            inside = target.relative_to(self.root).as_posix()
        except ValueError:
            raise ApiError(f"fora do repositório: {rel}", 403) from None
        allowed = [self._dir_name(d) for d in dirs]
        if not any(inside == d or inside.startswith(d + "/") for d in allowed):
            raise ApiError(f"acesso negado: {rel} (permitido: {', '.join(allowed)}/)", 403)
        if must_exist and not target.exists():
            raise ApiError(f"não encontrado: {rel}", 404)
        return target

    def _dir_name(self, kind: str) -> str:
        """Pastas configuráveis (pixelforge.toml) relativas à raiz."""
        if kind == "art":
            return self.rel(self.config.art_dir)
        if kind == "out":
            return self.rel(self.config.output_dir)
        if kind == "art/examples":
            return self.rel(self.config.art_dir / "examples")
        return kind

    def rel(self, path: Path) -> str:
        return Path(path).resolve().relative_to(self.root).as_posix()

    def writable(self, rel: str, must_exist: bool = True) -> Path:
        target = self.path(rel, WRITABLE_DIRS, must_exist)
        inside = self.rel(target)
        for protected in PROTECTED_DIRS:
            prefix = self._dir_name(protected)
            if inside == prefix or inside.startswith(prefix + "/"):
                raise ApiError(f"{rel}: art/examples/ é só leitura (salve como nova versão)", 403)
        return target

    # ------------------------------------------------------------------
    # estado / acervo
    # ------------------------------------------------------------------

    def state(self) -> dict:
        return {
            "raiz": self.root.name,
            "cena_disponivel": scene_engine() is not None,
            "paletas": sorted(pal.available(self.config.palette_dirs)),
            "chaves": SPEC_KEYS,
        }

    def catalog(self) -> dict:
        with self.lock:
            self.library.load_or_scan()
            return {"itens": [e.to_dict() for e in self.library.search()]}

    def reindex(self) -> dict:
        with self.lock:
            warnings = self.library.scan(thumbnails=True)
            return {"itens": [e.to_dict() for e in self.library.search()], "avisos": warnings}

    def tag(self, body: dict) -> dict:
        with self.lock:
            self.library.load_or_scan()
            try:
                entry = self.library.tag(str(body.get("nome", "")), body.get("adicionar") or [],
                                         body.get("remover") or [], body.get("tipo") or None,
                                         body.get("projeto"))
            except KeyError as exc:
                raise ApiError(exc.args[0], 404) from None
            except ValueError as exc:
                raise ApiError(str(exc)) from None
            return entry.to_dict()

    def palette(self, name: str) -> dict:
        try:
            colors = pal.get(name, self.config.palette_dirs)
        except KeyError as exc:
            raise ApiError(exc.args[0], 404) from None
        return {"nome": name, "cores": [pal.to_hex(c) for c in colors if c[3] > 0]}

    # ------------------------------------------------------------------
    # arte: ler / gravar spec
    # ------------------------------------------------------------------

    def read_art(self, rel: str) -> dict:
        path = self.path(rel, ("art",))
        if path.suffix.lower() not in ART_SUFFIXES:
            raise ApiError(f"{rel}: não é uma arte ({', '.join(ART_SUFFIXES)})")
        editable = path.suffix.lower() == ".json"
        message = None
        if editable:
            spec = _read_json(path)
            if "palette" not in spec:
                raise ApiError(f"{rel}: não é uma spec de arte (sem 'palette')")
            _validate(spec, path.stem)
        else:
            try:
                art = load_art_file(path)
                spec = spec_from_art(art)
            except SpecError as exc:
                spec, message = None, str(exc)
            except Exception as exc:  # script com erro
                raise ApiError(f"{rel}: {exc}") from None
        result = {"arquivo": self.rel(path), "editavel": editable, "spec": spec, "aviso": message,
                  "protegido": self._protected(path)}
        if spec:
            result["nome"] = spec.get("name") or path.stem
            result["cores"] = {k: _hex(v) for k, v in spec["palette"].items()}
        else:
            result["nome"] = path.stem
        result["fonte"] = spec.get("source") if spec else None
        return result

    def _protected(self, path: Path) -> bool:
        try:
            self.writable(self.rel(path))
            return False
        except ApiError:
            return True

    def save_art(self, body: dict) -> dict:
        rel = str(body.get("arquivo", ""))
        with self.lock:
            path = self.writable(rel)
            if path.suffix.lower() != ".json":
                raise ApiError(f"{rel}: só specs .json são gravadas; use 'nova versão' para scripts e imagens")
            raw = _read_json(path)
            merged = merge_spec(raw, _body_spec(body))
            _validate(merged, path.stem)
            path.write_text(dump_spec(merged), encoding="utf-8")
            return self._after_write(path)

    def save_version(self, body: dict) -> dict:
        rel = str(body.get("arquivo", ""))
        with self.lock:
            source = self.path(rel, ("art",))
            self.library.load_or_scan()
            current = self.read_art(rel)
            name = current["nome"]
            new_name = self.library.next_version_name(name)
            folder = source.parent
            if self._protected(source):
                folder = self.config.art_dir
            target = folder / f"{new_name}.json"
            self.writable(self.rel(target.parent / "x.json"), must_exist=False)
            if target.exists():
                raise ApiError(f"{self.rel(target)} já existe", 409)
            base = current["spec"] or {}
            merged = merge_spec(base, _body_spec(body))
            merged["name"] = new_name
            meta = dict(merged.get("acervo") or {})
            meta["herda"] = name
            merged = _insert_after(merged, "name", "acervo", meta)
            _validate(merged, new_name)
            target.write_text(dump_spec(merged), encoding="utf-8")
            return self._after_write(target)

    def _after_write(self, path: Path) -> dict:
        art = load_art_file(path)
        out_dir = self.config.output_dir / art.name
        written = export(art, out_dir, ExportOptions(formats=["png"], scales=[1], preview=True))
        entry = self.library.update_file(path)
        return {"arquivo": self.rel(path), "nome": art.name, "saidas": [self.rel(p) for p in written],
                "entrada": entry.to_dict() if entry else None}

    def render(self, body: dict) -> dict:
        rel = str(body.get("arquivo", ""))
        path = self.path(rel, ("art",))
        with self.lock:
            try:
                art = load_art_file(path)
            except Exception as exc:
                raise ApiError(f"{rel}: {exc}") from None
            out = self.config.data["output"]
            options = ExportOptions(formats=list(out["formats"]), scales=list(out["scales"]), preview=True,
                                    jpg_background=out["jpg_background"], jpg_quality=out["jpg_quality"])
            written = export(art, self.config.output_dir / art.name, options)
            self.library.load_or_scan()
            self.library.update_file(path)
            return {"nome": art.name, "saidas": [self.rel(p) for p in written],
                    "preview": self.rel(self.config.output_dir / art.name / f"{art.name}_preview.png")}

    # ------------------------------------------------------------------
    # comparador com a foto de referência
    # ------------------------------------------------------------------

    def compare(self, rel: str) -> dict:
        from ..compare import compare_image, reference_grid, similarity
        from ..convert import ConvertOptions

        path = self.path(rel, ("art",))
        art = load_art_file(path)
        source = art.meta.get("source")
        if not source:
            raise ApiError("esta arte não guarda a foto de origem ('source'); veja o comando compare", 404)
        source_path = self.path(str(source), ("refs", "art"), must_exist=False)
        if not source_path.is_file():
            raise ApiError(f"foto de referência não encontrada: {source}", 404)
        values = dict(art.meta.get("convert", {}))
        values["size"] = list(art.size)
        if values.get("mask"):
            values["mask"] = str(self.path(str(values["mask"]), ("refs", "art", "out"), must_exist=False))
        options = ConvertOptions.from_dict(values)
        with self.lock:
            reference = reference_grid(source_path, options)
            score = similarity(reference, art.frames[0], options.alpha_threshold)
            out = self.config.output_dir / art.name / f"{art.name}_compare.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            compare_image(reference, art.frames[0]).save(out)
        return {"painel": self.rel(out), "nota": str(score), "foto": self.rel(source_path)}

    # ------------------------------------------------------------------
    # cenas
    # ------------------------------------------------------------------

    def scenes(self) -> dict:
        with self.lock:
            self.library.load_or_scan()
            names = {e.nome: e.arquivo for e in self.library.search(tipo="cena")}
        out_dir = self.config.output_dir
        if out_dir.is_dir():
            for folder in sorted(out_dir.iterdir()):
                if folder.is_dir() and (folder / f"{folder.name}_storyboard.png").is_file():
                    names.setdefault(folder.name, None)
        return {"motor": scene_engine() is not None, "cenas": [self._scene_files(n, r) for n, r in sorted(names.items())]}

    def _scene_files(self, name: str, script: str | None) -> dict:
        folder = self.config.output_dir / name
        videos = [self.rel(folder / f"{name}{s}") for s in VIDEO_SUFFIXES if (folder / f"{name}{s}").is_file()]
        board = folder / f"{name}_storyboard.png"
        return {"nome": name, "roteiro": script, "videos": videos,
                "storyboard": self.rel(board) if board.is_file() else None}

    def scene(self, name: str) -> dict:
        found = {s["nome"]: s for s in self.scenes()["cenas"]}
        if name not in found:
            raise ApiError(f"cena '{name}' não encontrada", 404)
        info = found[name]
        info["planos"], info["fps"], info["duracao"], info["quadros"] = [], 12, 0.0, 0
        if info["roteiro"]:
            raw = _read_json(self.path(info["roteiro"], ("art",)))
            info["fps"] = int(raw.get("fps") or 12)
            t = 0.0
            for i, shot in enumerate(raw.get("planos", [])):
                dur = float(shot.get("dur") or 0) if isinstance(shot, dict) else 0.0
                info["planos"].append({"plano": i + 1, "inicio": t, "dur": dur})
                t += dur
            info["duracao"] = t
            engine = scene_engine()
            if engine:
                try:
                    timeline = self._timeline(info["roteiro"])
                    info["fps"], info["duracao"], info["quadros"] = timeline.fps, timeline.duration, timeline.frame_count
                    info["planos"] = [{"plano": i + 1, "inicio": a / timeline.fps, "dur": (b - a) / timeline.fps}
                                      for i, (a, b) in enumerate(timeline.shot_ranges)]
                except Exception as exc:
                    info["erro"] = str(exc)
        if not info["quadros"]:
            info["quadros"] = round(info["duracao"] * info["fps"])
        return info

    def _timeline(self, script_rel: str):
        engine = scene_engine()
        path = self.path(script_rel, ("art",))
        key = (str(path), path.stat().st_mtime)
        with self.lock:
            if key not in self._timelines:
                self._timelines = {key: engine.open_scene(path, self.config)}
            return self._timelines[key]

    def frame(self, script_rel: str, t: float, scale: int | None = None) -> dict:
        engine = scene_engine()
        if engine is None:
            raise ApiError("motor de cena ainda não instalado (pixelforge/scene/); use o vídeo", 501)
        try:
            timeline = self._timeline(script_rel)
            state = timeline.at(t)
            pixels = engine.render_frame(timeline, state)
        except ApiError:
            raise
        except Exception as exc:
            raise ApiError(str(exc)) from None
        scale = max(1, min(int(scale or timeline.scale), 8))
        name = timeline.scene.name
        out = self.config.output_dir / name / "_estudio" / f"{name}_q{state.index:05d}@{scale}x.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        image = Image.fromarray(pixels[..., :3] if pixels.shape[-1] == 4 else pixels, "RGB")
        upscale(image, scale).save(out)
        return {"imagem": self.rel(out), "indice": state.index, "plano": state.shot, "t": state.time,
                "escala": scale, "camera": list(state.camera)}

    # ------------------------------------------------------------------
    # pedidos ao Claude
    # ------------------------------------------------------------------

    @property
    def requests_dir(self) -> Path:
        return self.root / "pedidos"

    def create_request(self, body: dict) -> dict:
        text = str(body.get("texto") or "").strip()
        if not text:
            raise ApiError("escreva o que mudar")
        marks = body.get("marcas") or []
        if not isinstance(marks, list) or len(marks) > MAX_MARKS:
            raise ApiError(f"marcas: lista com no máximo {MAX_MARKS}")
        marks = [_mark(m, i) for i, m in enumerate(marks)]

        art_rel, image_rel = body.get("arquivo"), body.get("imagem")
        frame_index = int(body.get("quadro") or 0)
        scale_note = int(body.get("escala") or 1)
        if art_rel:
            path = self.path(str(art_rel), ("art",))
            art = load_art_file(path)
            frame_index = max(0, min(frame_index, len(art.frames) - 1))
            sprite = art.frames[frame_index]
            name, base_image, unit = art.name, preview(sprite), None
            unit = base_image.width // sprite.width
            source = self.rel(path)
        elif image_rel:
            path = self.path(str(image_rel), ("out", "art"))
            with Image.open(path) as opened:
                base_image = opened.convert("RGBA")
            unit = 1
            name = str(body.get("nome") or path.stem)
            source = self.rel(path)
        else:
            raise ApiError("informe 'arquivo' (arte) ou 'imagem' (quadro)")

        slug = re.sub(r"[^a-z0-9_-]+", "-", name.lower()).strip("-") or "arte"
        now = dt.datetime.now()
        with self.lock:
            self.requests_dir.mkdir(exist_ok=True)
            stem = f"{now:%Y-%m-%d}-{slug}"
            n = 1
            while (self.requests_dir / f"{stem}.md").exists():
                n += 1
                stem = f"{now:%Y-%m-%d}-{slug}-{n}"
            image_path = self.requests_dir / f"{stem}.png"
            annotate(base_image, marks, unit).save(image_path)
            md = request_markdown(name, source, text, marks, now, image_path.name, frame_index if art_rel else None,
                                  body.get("t"), scale_note if image_rel else 1, body.get("cena"))
            md_path = self.requests_dir / f"{stem}.md"
            md_path.write_text(md, encoding="utf-8")
        return {"pedido": self.rel(md_path), "imagem": self.rel(image_path)}

    def requests(self) -> dict:
        items = []
        if self.requests_dir.is_dir():
            for path in sorted(self.requests_dir.glob("*.md"), reverse=True):
                if path.name.lower() == "readme.md":
                    continue
                head = _front_matter(path.read_text(encoding="utf-8"))
                items.append({"pedido": self.rel(path), "estado": head.get("estado", "aberto"),
                              "arte": head.get("arte"), "criado": head.get("criado"),
                              "imagem": f"pedidos/{head['imagem']}" if head.get("imagem") else None,
                              "texto": _body_text(path.read_text(encoding="utf-8"))})
        return {"pedidos": items}

    def set_request_state(self, body: dict) -> dict:
        path = self.path(str(body.get("pedido", "")), ("pedidos",))
        state = str(body.get("estado", ""))
        if state not in ("aberto", "feito", "descartado") or path.suffix != ".md":
            raise ApiError("estado: aberto | feito | descartado")
        with self.lock:
            text = path.read_text(encoding="utf-8")
            text = re.sub(r"(?m)^estado: .*$", f"estado: {state}", text, count=1)
            path.write_text(text, encoding="utf-8")
        return {"pedido": self.rel(path), "estado": state}


# --------------------------------------------------------------------------
# auxiliares
# --------------------------------------------------------------------------


def scene_engine():
    """Módulo `pixelforge.scene` (outra frente do roadmap) ou None se ainda não existir."""
    try:
        if importlib.util.find_spec("pixelforge.scene") is None:
            return None
        import pixelforge.scene as engine
    except ImportError:
        return None
    if not all(hasattr(engine, n) for n in ("open_scene", "render_frame")):
        return None
    return engine


def merge_spec(raw: dict, incoming: dict) -> dict:
    """Troca só os campos de desenho, mantendo a ordem e os demais campos da spec."""
    merged = dict(raw)
    for key in ("size", "fps", "palette", "animations"):
        if key in incoming:
            merged[key] = incoming[key]
    frames = incoming.get("frames")
    if frames is None and "pixels" in incoming:
        frames = [incoming["pixels"]]
    if frames is not None:
        if len(frames) == 1 and "frames" not in raw:
            merged["pixels"] = frames[0]
            merged.pop("frames", None)
        else:
            merged["frames"] = frames
            merged.pop("pixels", None)
            merged.setdefault("fps", 8)
        if frames and frames[0]:
            merged["size"] = [len(frames[0][0]), len(frames[0])]
    if "palette" in merged:
        merged = _move_to_end(merged, "palette", before=("pixels", "frames"))
    return merged


def _move_to_end(spec: dict, key: str, before: tuple[str, ...]) -> dict:
    """Garante que `key` venha antes da grade (como gera o spec_from_art)."""
    keys = list(spec)
    grid = [k for k in keys if k in before]
    if not grid or keys.index(key) < keys.index(grid[0]):
        return spec
    value = spec[key]
    out = {}
    for k in keys:
        if k == key:
            continue
        if k == grid[0]:
            out[key] = value
        out[k] = spec[k]
    return out


def _insert_after(spec: dict, after: str, key: str, value) -> dict:
    out = {}
    for k, v in spec.items():
        if k == key:
            continue
        out[k] = v
        if k == after:
            out[key] = value
    out.setdefault(key, value)
    return out


def _body_spec(body: dict) -> dict:
    spec = body.get("spec")
    if not isinstance(spec, dict):
        raise ApiError("corpo precisa de 'spec' (objeto)")
    return spec


def _validate(spec: dict, name: str) -> None:
    try:
        parse_spec(spec, default_name=name)
    except SpecError as exc:
        raise ApiError(f"spec inválida: {exc}") from None
    animations = spec.get("animations")
    if animations is not None:
        count = len(spec.get("frames") or [spec.get("pixels")])
        if not isinstance(animations, dict):
            raise ApiError("'animations' deve ser um objeto nome → {frames, fps}")
        for anim, data in animations.items():
            frames = data.get("frames") if isinstance(data, dict) else None
            if not isinstance(frames, list) or not all(isinstance(i, int) and 0 <= i < count for i in frames):
                raise ApiError(f"animations['{anim}']: frames devem ser índices de 0 a {count - 1}")


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ApiError(f"{path.name}: JSON inválido ({exc})") from None
    if not isinstance(data, dict):
        raise ApiError(f"{path.name}: JSON não é um objeto")
    return data


def _hex(value) -> str:
    try:
        r, g, b, a = pal.parse_color(value)
    except ValueError:
        return "#00000000"
    return f"#{r:02x}{g:02x}{b:02x}{a:02x}"


def _mark(raw, index: int) -> dict:
    if not isinstance(raw, dict) or raw.get("tipo") not in ("ponto", "retangulo"):
        raise ApiError(f"marca {index + 1}: tipo deve ser 'ponto' ou 'retangulo'")
    try:
        mark = {"tipo": raw["tipo"], "x": int(raw["x"]), "y": int(raw["y"])}
        if raw["tipo"] == "retangulo":
            mark["w"], mark["h"] = max(1, int(raw["w"])), max(1, int(raw["h"]))
    except (KeyError, TypeError, ValueError):
        raise ApiError(f"marca {index + 1}: x, y (e w, h no retângulo) devem ser inteiros") from None
    note = str(raw.get("nota") or "").strip()
    if note:
        mark["nota"] = note[:300]
    return mark


MARK_COLOR = (255, 0, 170, 255)


def annotate(image: Image.Image, marks: list[dict], unit: int) -> Image.Image:
    """Desenha as marcas (numeradas) sobre a imagem; `unit` = px da imagem por px de coordenada."""
    image = image.convert("RGBA").copy()
    draw = ImageDraw.Draw(image)
    width = max(2, unit // 4, image.width // 300)
    for i, mark in enumerate(marks, 1):
        x, y = mark["x"] * unit, mark["y"] * unit
        if mark["tipo"] == "retangulo":
            box = (x, y, x + mark["w"] * unit - 1, y + mark["h"] * unit - 1)
        else:
            r = max(unit, 6)
            cx, cy = x + unit // 2, y + unit // 2
            box = (cx - r, cy - r, cx + r, cy + r)
        if mark["tipo"] == "retangulo":
            draw.rectangle(box, outline=MARK_COLOR, width=width)
        else:
            draw.ellipse(box, outline=MARK_COLOR, width=width)
        label = str(i)
        lx, ly = box[0], max(0, box[1] - 14)
        draw.rectangle((lx, ly, lx + 8 * len(label) + 4, ly + 13), fill=MARK_COLOR)
        draw.text((lx + 3, ly + 1), label, fill=(255, 255, 255, 255))
    return image


def request_markdown(name: str, source: str, text: str, marks: list[dict], when: dt.datetime, image: str,
                     frame: int | None, t, scale: int, scene: str | None) -> str:
    head = ["---", "estado: aberto", f"criado: {when:%Y-%m-%d %H:%M}", f"arte: {name}", f"arquivo: {source}"]
    if scene:
        head.append(f"cena: {scene}")
    if frame is not None:
        head.append(f"quadro: {frame}")
    if t is not None:
        head.append(f"t: {float(t):g}")
    head += [f"imagem: {image}", "---", "", f"# Pedido: {name}", "", text, ""]
    if marks:
        unit = "pixels da arte" if frame is not None else (
            f"pixels da imagem ampliada ×{scale}; entre colchetes, pixel lógico da cena" if scale > 1
            else "pixels da imagem")
        head += [f"## Marcas ({unit}; origem no canto superior esquerdo)", ""]
        for i, mark in enumerate(marks, 1):
            if mark["tipo"] == "ponto":
                desc = f"ponto em ({mark['x']}, {mark['y']})"
            else:
                x2, y2 = mark["x"] + mark["w"] - 1, mark["y"] + mark["h"] - 1
                desc = (f"retângulo x={mark['x']} y={mark['y']} largura={mark['w']} altura={mark['h']} "
                        f"(de {mark['x']},{mark['y']} até {x2},{y2})")
            if scale > 1 and frame is None:
                lx, ly = mark["x"] // scale, mark["y"] // scale
                if mark["tipo"] == "ponto":
                    desc += f" [{lx}, {ly}]"
                else:
                    desc += (f" [x={lx} y={ly} até {(mark['x'] + mark['w'] - 1) // scale},"
                             f"{(mark['y'] + mark['h'] - 1) // scale}]")
            note = f" — {mark['nota']}" if mark.get("nota") else ""
            head.append(f"{i}. {desc}{note}")
        head.append("")
    head += [f"![imagem anotada]({image})", ""]
    return "\n".join(head)


def _front_matter(text: str) -> dict:
    match = re.match(r"^---\n(.*?)\n---", text.replace("\r\n", "\n"), re.S)
    if not match:
        return {}
    out = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def _body_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    body = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.S)
    body = re.sub(r"(?m)^# .*$", "", body, count=1)
    return body.split("\n## ", 1)[0].split("\n![", 1)[0].strip()
