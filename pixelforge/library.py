"""Acervo: índice dos assets em `art/acervo.json`, versões e busca.

Cada arquivo de `art/` (spec .json, script .py, imagem, roteiro de cena,
cenário em camadas, som) vira uma entrada:

    {"nome": "heroi_v2", "tipo": "personagem", "tags": ["floresta"],
     "projeto": "coletanea", "base": "heroi", "versao": 2, "herda": "heroi_v1",
     "arquivo": "art/personagens/heroi_v2.json", "miniatura": "out/heroi_v2/heroi_v2_miniatura.png",
     "tamanho": [32, 32], "quadros": 4}

Metadados opcionais declarados no próprio arquivo têm prioridade:
- spec/roteiro .json: campo `"acervo": {"tipo": ..., "tags": [...], "projeto": ..., "herda": ...}`;
- script .py: variável `ACERVO = {...}` (lida sem executar o script).
Tags dadas pela CLI (`acervo tag`) ficam no índice e sobrevivem à reindexação.

Versões: `heroi_v2` herda de `heroi_v1` (ou de `heroi`, a versão 1 implícita).
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

INDEX_NAME = "acervo.json"
TYPES = ("personagem", "cenario", "objeto", "cena", "som")
TYPE_ALIASES = {"cenário": "cenario", "personagens": "personagem", "cenarios": "cenario",
                "cenários": "cenario", "objetos": "objeto", "cenas": "cena", "sons": "som"}
ART_SUFFIXES = (".json", ".py", ".png", ".gif", ".webp")
SOUND_SUFFIXES = (".wav", ".ogg", ".mp3", ".flac")
THUMB_SIDE = 128
_VERSION = re.compile(r"^(?P<base>.+?)_v(?P<n>\d+)$")


@dataclass
class Entry:
    nome: str
    tipo: str
    arquivo: str
    tags: list[str] = field(default_factory=list)
    projeto: str = ""
    base: str = ""
    versao: int = 1
    herda: str | None = None
    miniatura: str | None = None
    tamanho: list[int] | None = None
    quadros: int = 1
    fixo: list[str] = field(default_factory=list)  # campos definidos à mão (acervo tag)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Entry":
        known = {k: data[k] for k in cls.__dataclass_fields__ if k in data}
        return cls(**known)

    def matches(self, text: str = "", tipo: str | None = None, tags: list[str] | None = None,
                projeto: str | None = None) -> bool:
        if tipo and self.tipo != normalize_type(tipo):
            return False
        if projeto and self.projeto.lower() != projeto.lower():
            return False
        own = {t.lower() for t in self.tags}
        if tags and not all(t.lower() in own for t in tags):
            return False
        if text:
            hay = " ".join([self.nome, self.tipo, self.projeto, self.arquivo, *self.tags]).lower()
            return all(word in hay for word in text.lower().split())
        return True


def normalize_type(value: str) -> str:
    value = value.strip().lower()
    value = TYPE_ALIASES.get(value, value)
    if value not in TYPES:
        raise ValueError(f"tipo '{value}' inválido. Use: {', '.join(TYPES)}")
    return value


def split_version(name: str) -> tuple[str, int]:
    """'heroi_v2' → ('heroi', 2); 'heroi' → ('heroi', 1)."""
    match = _VERSION.match(name)
    if match:
        return match["base"], int(match["n"])
    return name, 1


def normalize_tags(tags) -> list[str]:
    if isinstance(tags, str):
        tags = re.split(r"[,\s]+", tags)
    out: list[str] = []
    for tag in tags or []:
        tag = str(tag).strip().lower().lstrip("#")
        if tag and tag not in out:
            out.append(tag)
    return out


# --------------------------------------------------------------------------
# Índice
# --------------------------------------------------------------------------


class Library:
    def __init__(self, root: Path, art_dir: Path, output_dir: Path):
        self.root = Path(root).resolve()
        self.art_dir = Path(art_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.entries: dict[str, Entry] = {}
        self._declared_type: set[str] = set()

    @classmethod
    def from_config(cls, config) -> "Library":
        return cls(config.root, config.art_dir, config.output_dir)

    @property
    def index_path(self) -> Path:
        return self.art_dir / INDEX_NAME

    def rel(self, path: Path) -> str:
        path = Path(path).resolve()
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def abs(self, rel: str) -> Path:
        return (self.root / rel).resolve()

    # ----- leitura / escrita -------------------------------------------

    def load(self) -> "Library":
        self.entries = {}
        if self.index_path.is_file():
            try:
                data = json.loads(self.index_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{self.index_path}: JSON inválido ({exc})") from None
            for raw in data.get("itens", []):
                entry = Entry.from_dict(raw)
                self.entries[entry.nome] = entry
        return self

    def save(self) -> Path:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        items = sorted(self.entries.values(), key=lambda e: (e.base, e.versao, e.nome))
        # um item por linha: diffs legíveis no git
        lines = ",\n".join("    " + json.dumps(e.to_dict(), ensure_ascii=False) for e in items)
        text = '{\n  "versao_indice": 1,\n  "itens": [\n' + lines + "\n  ]\n}\n"
        self.index_path.write_text(text, encoding="utf-8")
        return self.index_path

    def load_or_scan(self) -> "Library":
        if self.index_path.is_file():
            return self.load()
        self.scan()
        return self

    # ----- varredura ----------------------------------------------------

    def asset_files(self) -> list[Path]:
        if not self.art_dir.is_dir():
            return []
        files = []
        for path in sorted(self.art_dir.rglob("*")):
            if not path.is_file() or path.name == INDEX_NAME or path.name.startswith(("_", ".")):
                continue
            if any(part.startswith((".", "_")) for part in path.relative_to(self.art_dir).parts[:-1]):
                continue
            if path.suffix.lower() in ART_SUFFIXES + SOUND_SUFFIXES:
                files.append(path)
        return files

    def scan(self, thumbnails: bool = False, log=None) -> list[str]:
        """Reconstrói o índice a partir de `art/`. Guarda tags e campos dados pela CLI.
        Devolve avisos (arquivos que não puderam ser lidos)."""
        previous = dict(self.entries) if self.entries else dict(self.load().entries)
        warnings: list[str] = []
        entries: dict[str, Entry] = {}
        self._declared_type = set()
        for path in self.asset_files():
            try:
                entry = self._entry_for(path, previous)
            except (ValueError, SyntaxError, OSError) as exc:
                warnings.append(f"{self.rel(path)}: {exc}")
                continue
            if entry is None:
                continue
            if entry.nome in entries:
                warnings.append(f"{entry.arquivo}: nome '{entry.nome}' repetido (já em {entries[entry.nome].arquivo})")
                continue
            entries[entry.nome] = entry
        self.entries = entries
        self._link_versions()
        self._mark_layers()
        for entry in self.entries.values():
            if thumbnails:
                try:
                    self.make_thumbnail(entry)
                except Exception as exc:  # script com erro não derruba a indexação
                    warnings.append(f"{entry.arquivo}: miniatura falhou ({exc})")
            if entry.miniatura is None:
                entry.miniatura = self._existing_thumbnail(entry.nome)
            if log:
                log(entry)
        self.save()
        return warnings

    def _entry_for(self, path: Path, previous: dict[str, Entry]) -> Entry | None:
        declared, data = self._declared(path)
        name = str((data or {}).get("name") or path.stem) if path.suffix.lower() == ".json" else path.stem
        if path.suffix.lower() == ".py":
            name = str(declared.pop("_name", None) or path.stem)
        old = previous.get(name)
        base, version = split_version(name)

        fixed = list(old.fixo) if old else []
        if declared.get("tipo"):
            self._declared_type.add(name)
        tipo = (declared.get("tipo") or (old.tipo if "tipo" in fixed else None)
                or self._infer_type(path, data))
        tags = normalize_tags(declared.get("tags")) + (old.tags if old else [])
        tags += [p.lower() for p in path.relative_to(self.art_dir).parts[:-1]]
        entry = Entry(
            nome=name,
            tipo=normalize_type(tipo),
            arquivo=self.rel(path),
            tags=normalize_tags(tags),
            projeto=str(declared.get("projeto") or (old.projeto if "projeto" in fixed else "") or ""),
            base=base,
            versao=version,
            herda=declared.get("herda"),
            fixo=fixed,
        )
        if isinstance(data, dict) and "palette" in data:
            frames = data.get("frames") or [data.get("pixels") or []]
            entry.quadros = len(frames)
            rows = frames[0] if frames else []
            if rows:
                entry.tamanho = [len(rows[0]), len(rows)]
        elif isinstance(data, dict) and isinstance(data.get("size"), list):
            entry.tamanho = list(data["size"])
        elif path.suffix.lower() in (".png", ".gif", ".webp"):
            from PIL import Image

            with Image.open(path) as im:
                entry.tamanho = list(im.size)
                entry.quadros = getattr(im, "n_frames", 1)
        if old and old.tamanho and entry.tamanho is None:
            entry.tamanho, entry.quadros = old.tamanho, old.quadros
        return entry

    def _declared(self, path: Path) -> tuple[dict, dict | None]:
        suffix = path.suffix.lower()
        if suffix == ".json":
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON inválido ({exc})") from None
            if not isinstance(data, dict):
                raise ValueError("JSON não é um objeto")
            declared = data.get("acervo") if isinstance(data.get("acervo"), dict) else {}
            return dict(declared), data
        if suffix == ".py":
            return _script_metadata(path), None
        return {}, None

    def _infer_type(self, path: Path, data: dict | None) -> str:
        if path.suffix.lower() in SOUND_SUFFIXES:
            return "som"
        if isinstance(data, dict):
            if "planos" in data:
                return "cena"
            if "camadas" in data:
                return "cenario"
        for part in reversed(path.relative_to(self.art_dir).parts[:-1]):
            part = TYPE_ALIASES.get(part.lower(), part.lower())
            if part in TYPES:
                return part
        return "objeto"

    def _mark_layers(self) -> None:
        """Artes usadas como camada de um cenário (`camadas[].arte`) viram tipo cenario."""
        for scenery in [e for e in self.entries.values() if e.tipo == "cenario" and e.arquivo.endswith(".json")]:
            try:
                data = json.loads(self.abs(scenery.arquivo).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            folder = self.abs(scenery.arquivo).parent
            for layer in data.get("camadas") or []:
                ref = layer.get("arte") if isinstance(layer, dict) else None
                if not isinstance(ref, str):
                    continue
                for base in (folder, self.art_dir):
                    hits = [e for e in self.entries.values()
                            if self.abs(e.arquivo).with_suffix("") == (base / ref).resolve().with_suffix("")]
                    if hits:
                        break
                for entry in hits:
                    if entry.nome not in self._declared_type and "tipo" not in entry.fixo:
                        entry.tipo = "cenario"
                    entry.tags = normalize_tags(entry.tags + ["camada", scenery.nome])

    def _link_versions(self) -> None:
        by_base: dict[str, list[Entry]] = {}
        for entry in self.entries.values():
            by_base.setdefault(entry.base, []).append(entry)
        for family in by_base.values():
            family.sort(key=lambda e: e.versao)
            for i, entry in enumerate(family):
                if entry.herda and entry.herda in self.entries:
                    continue
                entry.herda = family[i - 1].nome if i > 0 else None

    # ----- miniaturas ---------------------------------------------------

    def _existing_thumbnail(self, name: str) -> str | None:
        folder = self.output_dir / name
        for candidate in (f"{name}_miniatura.png", f"{name}.png", f"{name}_storyboard.png"):
            if (folder / candidate).is_file():
                return self.rel(folder / candidate)
        return None

    def make_thumbnail(self, entry: Entry) -> str | None:
        """Grava out/<nome>/<nome>_miniatura.png (1º quadro, ampliado) se faltar ou estiver velha."""
        if entry.tipo in ("cena", "som") or Path(entry.arquivo).suffix.lower() not in ART_SUFFIXES:
            return entry.miniatura
        if Path(entry.arquivo).suffix.lower() == ".json":
            data = json.loads(self.abs(entry.arquivo).read_text(encoding="utf-8"))
            if "palette" not in data:
                return entry.miniatura
        source = self.abs(entry.arquivo)
        target = self.output_dir / entry.nome / f"{entry.nome}_miniatura.png"
        if not target.is_file() or target.stat().st_mtime < source.stat().st_mtime:
            from .export import upscale

            art = load_art_file(source)
            image = art.frames[0].to_image()
            scale = max(1, THUMB_SIDE // max(image.size))
            target.parent.mkdir(parents=True, exist_ok=True)
            upscale(image, scale).save(target)
            entry.tamanho, entry.quadros = list(art.size), len(art.frames)
        entry.miniatura = self.rel(target)
        return entry.miniatura

    # ----- consultas ----------------------------------------------------

    def search(self, text: str = "", tipo: str | None = None, tags: list[str] | None = None,
               projeto: str | None = None) -> list[Entry]:
        found = [e for e in self.entries.values() if e.matches(text, tipo, tags, projeto)]
        return sorted(found, key=lambda e: (e.tipo, e.base, e.versao))

    def get(self, name: str) -> Entry:
        if name in self.entries:
            return self.entries[name]
        by_file = [e for e in self.entries.values() if e.arquivo == name or Path(e.arquivo).stem == name]
        if by_file:
            return by_file[0]
        raise KeyError(f"'{name}' não está no acervo (rode: python -m pixelforge acervo indexar)")

    def versions(self, name: str) -> list[Entry]:
        """Família inteira (todas as versões da mesma base), da mais antiga à mais nova."""
        base = self.get(name).base
        return sorted((e for e in self.entries.values() if e.base == base), key=lambda e: e.versao)

    def history(self, name: str) -> list[Entry]:
        """Cadeia de herança até a origem: [v1, v2, ..., name]."""
        chain = [self.get(name)]
        seen = {chain[0].nome}
        while chain[0].herda and chain[0].herda in self.entries and chain[0].herda not in seen:
            chain.insert(0, self.entries[chain[0].herda])
            seen.add(chain[0].nome)
        return chain

    def next_version_name(self, name: str) -> str:
        base = split_version(name)[0]
        taken = [e.versao for e in self.entries.values() if e.base == base]
        taken.append(split_version(name)[1])
        candidate = f"{base}_v{max(taken) + 1}"
        while candidate in self.entries:
            candidate = f"{base}_v{split_version(candidate)[1] + 1}"
        return candidate

    def tag(self, name: str, add: list[str] = (), remove: list[str] = (), tipo: str | None = None,
            projeto: str | None = None) -> Entry:
        entry = self.get(name)
        tags = [t for t in entry.tags if t not in normalize_tags(remove)]
        entry.tags = normalize_tags(tags + normalize_tags(add))
        if tipo:
            entry.tipo = normalize_type(tipo)
            entry.fixo = sorted(set(entry.fixo) | {"tipo"})
        if projeto is not None:
            entry.projeto = projeto
            entry.fixo = sorted(set(entry.fixo) | {"projeto"})
        self.save()
        return entry

    def update_file(self, path: Path, thumbnails: bool = True) -> Entry | None:
        """Atualiza (ou cria) só a entrada de um arquivo, sem varrer tudo."""
        if not self.entries:
            self.load_or_scan()
        entry = self._entry_for(Path(path).resolve(), self.entries)
        if entry is None:
            return None
        self.entries[entry.nome] = entry
        self._link_versions()
        self._mark_layers()
        if thumbnails:
            self.make_thumbnail(entry)
        if entry.miniatura is None:
            entry.miniatura = self._existing_thumbnail(entry.nome)
        self.save()
        return entry


def load_art_file(path: Path):
    try:
        from .artfile import load_art
    except ImportError:  # antes da extração para artfile.py
        from .cli import load_art
    return load_art(Path(path))


def _script_metadata(path: Path) -> dict:
    """Lê `ACERVO = {...}` e `NAME = "..."` de um script sem executá-lo."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: dict = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target = node.targets[0].id
            if target in ("ACERVO", "NAME"):
                try:
                    value = ast.literal_eval(node.value)
                except ValueError:
                    continue
                if target == "ACERVO" and isinstance(value, dict):
                    found.update(value)
                elif target == "NAME" and isinstance(value, str):
                    found["_name"] = value
    return found
