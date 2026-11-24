"""Servidor MCP local (stdio): outros projetos chamam o motor sem shell.

    python -m pixelforge mcp [--raiz <repositório>]

Ferramentas: render, quadro, storyboard, cena, personagem, lint, acervo_buscar,
som_efeito. Cada chamada roda `python -m pixelforge <comando>` num subprocesso com
a raiz do repositório como pasta atual (a saída padrão do servidor é o canal MCP e
fica limpa) e devolve um JSON com os arquivos gerados (caminhos relativos à raiz).
Todo caminho recebido é validado: nada fora do repositório.

O SDK (`mcp`) é opcional, extra `[mcp]`; as funções `tool_*` não dependem dele.
"""

from __future__ import annotations

import functools
import io
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

TIMEOUT = 900  # s; cenas longas com MP4 podem demorar
MAX_IMAGE_SIDE = 1600  # px; imagens maiores voltam reduzidas (vizinho mais próximo)
_SAFE_NAME = re.compile(r"^[\w.-]+$")

INSTRUCTIONS = """\
PixelForge: pixel art, cenas (roteiro JSON → vídeo), personagens, lint e efeitos chiptune,
tudo gerado por código no repositório do PixelForge. Caminhos são relativos à raiz desse
repositório (ex.: art/coletanea/cap7/cap7.json) e não podem sair dele. Fluxo de cena:
storyboard (ver=true) → ajustar o roteiro → quadro em instantes duvidosos → cena (vídeo).
Sempre olhe o preview/storyboard devolvido antes de dar a arte por pronta."""


class ToolInputError(ValueError):
    """Argumento inválido (caminho fora do repositório, nome com barra...)."""


@dataclass
class Result:
    """Resultado de um comando: código, texto e arquivos gerados."""

    command: list[str]
    code: int
    stdout: str
    stderr: str
    files: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.code == 0

    def to_dict(self) -> dict:
        data = {"ok": self.ok, "comando": "python -m pixelforge " + " ".join(self.command),
                "arquivos": self.files, "saida": self.stdout.strip()}
        if self.stderr.strip():
            data["avisos" if self.ok else "erro"] = self.stderr.strip()
        return data


# --------------------------------------------------------------------------
# raiz e caminhos
# --------------------------------------------------------------------------


def find_root(explicit: str | Path | None = None) -> Path:
    """Raiz do PixelForge: --raiz > PIXELFORGE_RAIZ > pasta atual > pasta do pacote."""
    candidates = [explicit, os.environ.get("PIXELFORGE_RAIZ"), Path.cwd(), Path(__file__).resolve().parent.parent]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).resolve()
        if (path / "pixelforge.toml").is_file():
            return path
        if candidate is explicit or candidate == os.environ.get("PIXELFORGE_RAIZ"):
            raise ToolInputError(f"{path}: não é a raiz do PixelForge (falta pixelforge.toml)")
    raise ToolInputError("raiz do PixelForge não encontrada; use --raiz ou PIXELFORGE_RAIZ")


def inside(root: Path, value: str | Path, *, must_exist: bool = True) -> Path:
    """Resolve `value` (relativo à raiz ou absoluto) e garante que fica dentro de `root`."""
    if not str(value).strip():
        raise ToolInputError("caminho vazio")
    path = Path(value)
    path = (path if path.is_absolute() else root / path).resolve()
    if not path.is_relative_to(root):
        raise ToolInputError(f"{value}: fora do repositório ({root}); use caminhos dentro dele")
    if must_exist and not path.exists():
        raise ToolInputError(f"{value}: arquivo não encontrado")
    return path


def relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def safe_name(value: str, what: str = "nome") -> str:
    if not _SAFE_NAME.match(value or ""):
        raise ToolInputError(f"{what} {value!r}: use só letras, números, '.', '_' e '-'")
    return value


def _paths_in(root: Path, text: str) -> list[str]:
    """Arquivos citados na saída do comando ('  <caminho>', 'spec: <caminho>', '<caminho>: info')."""
    found: dict[str, None] = {}
    for line in text.splitlines():
        line = line.strip()
        head, _, tail = line.partition(": ")
        for candidate in (line, head, tail):
            candidate = candidate.strip()
            if not candidate or len(candidate) > 400:
                continue
            path = Path(candidate)
            path = path if path.is_absolute() else root / path
            try:
                if path.is_file() and path.resolve().is_relative_to(root):
                    found[relative(root, path)] = None
            except OSError:
                continue
    return list(found)


# --------------------------------------------------------------------------
# execução
# --------------------------------------------------------------------------


def run_pixelforge(root: Path, args: list[str], timeout: int = TIMEOUT) -> Result:
    # o subprocesso usa o mesmo pacote que o servidor, mesmo sem `pip install -e .`
    package_parent = str(Path(__file__).resolve().parent.parent)
    python_path = os.pathsep.join(p for p in (package_parent, os.environ.get("PYTHONPATH")) if p)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONPATH": python_path}
    try:
        proc = subprocess.run([sys.executable, "-m", "pixelforge", *args], cwd=root, env=env,
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return Result(args, 124, "", f"tempo esgotado ({timeout} s)")
    return Result(args, proc.returncode, proc.stdout, proc.stderr, _paths_in(root, proc.stdout))


def _optional(args: list[str], flag: str, value) -> None:
    if value is not None and value != "":
        args += [flag, str(value)]


def _scene_args(root: Path, roteiro: str, resolucao, escala, fps=None) -> list[str]:
    args = [str(inside(root, roteiro))]
    _optional(args, "--resolucao", resolucao)
    _optional(args, "--escala", escala)
    _optional(args, "--fps", fps)
    return args


# --------------------------------------------------------------------------
# ferramentas (sem dependência do SDK)
# --------------------------------------------------------------------------


def tool_render(root: Path, arquivos: list[str], formatos: str | None = None,
                escalas: str | None = None) -> Result:
    if not arquivos:
        raise ToolInputError("informe ao menos um arquivo (.json, .py ou .png)")
    args = ["render", *(str(inside(root, f)) for f in arquivos)]
    _optional(args, "--formats", formatos)
    _optional(args, "--scales", escalas)
    return run_pixelforge(root, args)


def tool_quadro(root: Path, roteiro: str, t: float, resolucao: str | None = None,
                escala: int | None = None) -> Result:
    return run_pixelforge(root, ["quadro", *_scene_args(root, roteiro, resolucao, escala), "--t", f"{t:g}"])


def tool_storyboard(root: Path, roteiro: str, resolucao: str | None = None, escala: int | None = None) -> Result:
    return run_pixelforge(root, ["storyboard", *_scene_args(root, roteiro, resolucao, escala)])


def tool_cena(root: Path, roteiro: str, formatos: str | None = None, resolucao: str | None = None,
              escala: int | None = None, fps: int | None = None) -> Result:
    args = ["cena", *_scene_args(root, roteiro, resolucao, escala, fps)]
    _optional(args, "--formats", formatos)
    return run_pixelforge(root, args)


def tool_personagem(root: Path, modelo: str, variantes: list[str] | None = None, paleta: str | None = None,
                    mapa: str | None = None, aseprite: bool = False, gravar_specs: bool = True) -> Result:
    args = ["character", str(inside(root, modelo))]
    for variant in variantes or []:
        args += ["--variante", variant]
    _optional(args, "--paleta", paleta)
    _optional(args, "--mapa", mapa)
    if aseprite:
        args.append("--aseprite")
    if not gravar_specs:
        args.append("--no-spec")
    return run_pixelforge(root, args)


def tool_lint(root: Path, arquivos: list[str], verificacoes: str | None = None,
              fundo: str | None = None) -> tuple[Result, dict]:
    if not arquivos:
        raise ToolInputError("informe ao menos um arquivo para o lint")
    args = ["lint", *(str(inside(root, f)) for f in arquivos), "--json"]
    _optional(args, "--checks", verificacoes)
    _optional(args, "--bg", fundo)
    result = run_pixelforge(root, args)
    problems = {}
    if result.ok:
        try:
            raw = json.loads(result.stdout or "{}")
            problems = {relative(root, inside(root, k, must_exist=False)): v for k, v in raw.items()}
        except (json.JSONDecodeError, ToolInputError):
            problems = {}
        result.stdout = ""  # já vai estruturado em `problemas`
    result.files = []
    return result, problems


def tool_acervo_buscar(root: Path, texto: str = "", tipo: str | None = None, tags: list[str] | None = None,
                       projeto: str | None = None) -> tuple[Result, list]:
    args = ["acervo", "buscar", texto] if texto.strip() else ["acervo", "listar"]
    _optional(args, "--tipo", tipo)
    for tag in tags or []:
        args += ["--tag", tag]
    _optional(args, "--projeto", projeto)
    args.append("--json")
    result = run_pixelforge(root, args)
    entries = []
    if result.ok:
        try:
            entries = json.loads(result.stdout or "[]")
        except json.JSONDecodeError:
            entries = []
        result.stdout = ""  # já vai estruturado em `itens`
    result.files = []
    return result, entries


def tool_som_efeito(root: Path, fonte: str, variar: float | None = None, semente: int | None = None,
                    nome: str | None = None) -> Result:
    source = fonte.strip()
    if source.lower().endswith(".json") or "/" in source or "\\" in source:
        source = str(inside(root, source))
    else:
        safe_name(source, "preset")
    args = ["som", "efeito", source]
    _optional(args, "--variar", variar)
    _optional(args, "--semente", semente)
    if nome:
        args += ["--nome", safe_name(nome)]
    return run_pixelforge(root, args)


def preview_of(root: Path, files: list[str], suffixes: tuple[str, ...]) -> Path | None:
    for suffix in suffixes:
        for name in files:
            if name.endswith(suffix):
                return root / name
    return None


def image_bytes(path: Path, max_side: int = MAX_IMAGE_SIDE) -> bytes:
    """PNG do arquivo, reduzido por fator inteiro se passar de `max_side`."""
    from PIL import Image

    with Image.open(path) as image:
        image.load()
        factor = -(-max(image.size) // max_side)
        if factor > 1:
            image = image.resize((max(1, image.width // factor), max(1, image.height // factor)),
                                 Image.Resampling.NEAREST)
        buffer = io.BytesIO()
        image.save(buffer, "PNG")
    return buffer.getvalue()


# --------------------------------------------------------------------------
# servidor (SDK `mcp`)
# --------------------------------------------------------------------------


def _server_class():
    try:
        from mcp.server.mcpserver import Image, MCPServer  # SDK 2.x
        return MCPServer, Image
    except ImportError:
        pass
    try:
        from mcp.server.fastmcp import FastMCP, Image  # SDK 1.x
        return FastMCP, Image
    except ImportError:
        raise ValueError("o servidor MCP precisa do extra [mcp]: pip install -e .[mcp]") from None


def build_server(root: Path):
    server_class, Image = _server_class()
    server = server_class("pixelforge", instructions=INSTRUCTIONS)

    def reply(result: Result, image_suffixes: tuple[str, ...] = (), ver: bool = False, **extra):
        data = result.to_dict() | extra
        text = json.dumps(data, ensure_ascii=False, indent=2)
        if ver and result.ok:
            image = preview_of(root, result.files, image_suffixes)
            if image is not None:
                return [text, Image(data=image_bytes(image), format="png")]
        return text

    def guarded(fn):
        @functools.wraps(fn)
        def call(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except ToolInputError as exc:
                return json.dumps({"ok": False, "erro": str(exc)}, ensure_ascii=False)
        return call

    @server.tool(structured_output=False)
    @guarded
    def render(arquivos: list[str], formatos: str | None = None, escalas: str | None = None,
               ver: bool = False):
        """Renderiza artes (spec .json, script .py ou .png) para out/<nome>/: PNG 1x, ampliado,
        SVG/GIF conforme o pixelforge.toml e <nome>_preview.png (grade a cada pixel).
        formatos: "png,gif,svg,webp,jpg"; escalas: "1,8,16"; ver=true devolve o preview."""
        return reply(tool_render(root, arquivos, formatos, escalas), ("_preview.png",), ver)

    @server.tool(structured_output=False)
    @guarded
    def quadro(roteiro: str, t: float, resolucao: str | None = None, escala: int | None = None,
               ver: bool = True):
        """Um quadro do roteiro de cena no instante t (segundos), PNG ampliado em out/<cena>/.
        Use para conferir um momento duvidoso (diálogo, ator pisando no chão, efeito)."""
        return reply(tool_quadro(root, roteiro, t, resolucao, escala), (".png",), ver)

    @server.tool(structured_output=False)
    @guarded
    def storyboard(roteiro: str, resolucao: str | None = None, escala: int | None = None, ver: bool = True):
        """Folha com início/meio/fim de cada plano (tempo e câmera) do roteiro de cena:
        a revisão obrigatória antes de renderizar o vídeo."""
        return reply(tool_storyboard(root, roteiro, resolucao, escala), ("_storyboard.png",), ver)

    @server.tool(structured_output=False)
    @guarded
    def cena(roteiro: str, formatos: str | None = None, resolucao: str | None = None,
             escala: int | None = None, fps: int | None = None):
        """Renderiza a cena inteira: storyboard + vídeos (formatos "gif,webp,mp4"; padrão do
        pixelforge.toml). Sem o extra [video], o MP4 é pulado com aviso. Pode levar minutos."""
        return reply(tool_cena(root, roteiro, formatos, resolucao, escala, fps))

    @server.tool(structured_output=False)
    @guarded
    def personagem(modelo: str, variantes: list[str] | None = None, paleta: str | None = None,
                   mapa: str | None = None, aseprite: bool = False, gravar_specs: bool = True,
                   ver: bool = False):
        """Gera a folha de personagem de um modelo (*.personagem.json): retrato com expressões,
        sprite em 4 direções, animações (parado, piscar, falar, andar) e as specs com
        animations/anchor para a cena. variantes/paleta/mapa vêm do modelo (mapa: noite,
        por-do-sol, fantasma, sepia)."""
        result = tool_personagem(root, modelo, variantes, paleta, mapa, aseprite, gravar_specs)
        return reply(result, ("_preview.png",), ver)

    @server.tool(structured_output=False)
    @guarded
    def lint(arquivos: list[str], verificacoes: str | None = None, fundo: str | None = None):
        """Lint de pixel art com coordenadas (x, y, quadro): orfao, contorno, cores, banding,
        jaggies, contraste. É aviso, não regra (olhos e brilhos isolados são intencionais).
        verificacoes: "orfao,jaggies"; fundo: "#1a1c2c" para o teste de contraste."""
        result, problems = tool_lint(root, arquivos, verificacoes, fundo)
        total = sum(len(v) for v in problems.values())
        return reply(result, problemas=problems, total=total) if result.ok else reply(result)

    @server.tool(structured_output=False)
    @guarded
    def acervo_buscar(texto: str = "", tipo: str | None = None, tags: list[str] | None = None,
                      projeto: str | None = None):
        """Busca no acervo (art/acervo.json) por nome, tag, tipo ou projeto — todas as palavras
        precisam aparecer. Sem texto, lista com os filtros. tipo: personagem, cenario, objeto,
        cena, som. Devolve arquivo-fonte, tamanho, versões e miniatura de cada item."""
        result, entries = tool_acervo_buscar(root, texto, tipo, tags, projeto)
        return reply(result, itens=entries, total=len(entries)) if result.ok else reply(result)

    @server.tool(structured_output=False)
    @guarded
    def som_efeito(fonte: str, variar: float | None = None, semente: int | None = None,
                   nome: str | None = None):
        """Efeito chiptune em WAV (out/som/): preset (passo, pulo, moeda, magia, golpe, porta,
        explosao, menu, dano, sino) ou .json de parâmetros do repositório. variar (ex.: 0.15)
        + semente dão variações determinísticas; nome muda o arquivo."""
        return reply(tool_som_efeito(root, fonte, variar, semente, nome))

    return server


def serve(root: Path) -> None:
    server = build_server(root)
    server.run("stdio")
