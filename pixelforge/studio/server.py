"""Servidor HTTP do estúdio (stdlib). Só 127.0.0.1; API JSON em /api/*.

    GET  /api/estado                  paletas, chaves de spec, motor de cena disponível?
    GET  /api/acervo                  itens do índice (art/acervo.json)
    POST /api/acervo/indexar          reconstrói o índice (com miniaturas)
    POST /api/acervo/tag              {nome, adicionar, remover, tipo, projeto}
    GET  /api/arte?arquivo=art/x.json spec (para .py/.png: spec gerada) + cores normalizadas
    POST /api/arte                    {arquivo, spec} grava na spec (formato dump_spec) + preview
    POST /api/arte/versao             {arquivo, spec} grava art/<base>_vN.json herdando da atual
    POST /api/render                  {arquivo} renderiza como `pixelforge render`
    GET  /api/paleta?nome=pico8       cores de uma paleta
    GET  /api/comparar?arquivo=       painel do compare com a foto de referência
    GET  /api/cenas | /api/cena?nome= cenas com vídeo/storyboard e planos
    GET  /api/quadro?roteiro=&t=      um quadro (precisa de pixelforge/scene/)
    GET  /api/pedidos                 pedidos ao Claude (pedidos/*.md)
    POST /api/pedido                  {arquivo|imagem, texto, marcas, quadro, t}
    POST /api/pedido/estado           {pedido, estado}
    GET  /arquivo/<caminho>           arquivos de art/, out/, refs/, pedidos/
"""

from __future__ import annotations

import json
import mimetypes
import re
import sys
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from ..config import Config
from .api import ApiError, Studio

STATIC_DIR = Path(__file__).parent / "static"
HOST = "127.0.0.1"
MAX_BODY = 8 * 1024 * 1024


class StudioServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, config: Config, port: int):
        self.studio = Studio(config)
        super().__init__((HOST, port), Handler)

    @property
    def url(self) -> str:
        return f"http://{HOST}:{self.server_port}/"


class Handler(BaseHTTPRequestHandler):
    server: StudioServer
    protocol_version = "HTTP/1.1"

    GET_ROUTES = {
        "/api/estado": lambda s, q: s.state(),
        "/api/acervo": lambda s, q: s.catalog(),
        "/api/arte": lambda s, q: s.read_art(q.get("arquivo", "")),
        "/api/paleta": lambda s, q: s.palette(q.get("nome", "")),
        "/api/comparar": lambda s, q: s.compare(q.get("arquivo", "")),
        "/api/cenas": lambda s, q: s.scenes(),
        "/api/cena": lambda s, q: s.scene(q.get("nome", "")),
        "/api/quadro": lambda s, q: s.frame(q.get("roteiro", ""), _float(q.get("t", "0")),
                                            int(q["escala"]) if q.get("escala", "").isdigit() else None),
        "/api/pedidos": lambda s, q: s.requests(),
    }
    POST_ROUTES = {
        "/api/acervo/indexar": lambda s, b: s.reindex(),
        "/api/acervo/tag": lambda s, b: s.tag(b),
        "/api/arte": lambda s, b: s.save_art(b),
        "/api/arte/versao": lambda s, b: s.save_version(b),
        "/api/render": lambda s, b: s.render(b),
        "/api/pedido": lambda s, b: s.create_request(b),
        "/api/pedido/estado": lambda s, b: s.set_request_state(b),
    }

    def log_message(self, fmt, *args) -> None:  # silencioso; erros saem em _error
        pass

    # ------------------------------------------------------------------

    def do_GET(self) -> None:
        if not self._host_ok():
            return
        url = urlparse(self.path)
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path in self.GET_ROUTES:
                return self._json(self.GET_ROUTES[url.path](self.server.studio, query))
            if url.path.startswith("/arquivo/"):
                return self._file(self.server.studio.path(unquote(url.path[len("/arquivo/"):])), cache=False)
            if url.path.startswith("/api/"):
                raise ApiError(f"rota desconhecida: {url.path}", 404)
            return self._static(url.path)
        except ApiError as exc:
            self._error(exc.status, str(exc))
        except Exception as exc:  # erro inesperado: responde em vez de derrubar a conexão
            print(f"estúdio: erro em GET {url.path}: {exc!r}", file=sys.stderr)
            self._error(500, f"erro interno: {exc}")

    def do_POST(self) -> None:
        if not self._host_ok():
            return
        url = urlparse(self.path)
        try:
            if url.path not in self.POST_ROUTES:
                raise ApiError(f"rota desconhecida: {url.path}", 404)
            if "application/json" not in (self.headers.get("Content-Type") or ""):
                raise ApiError("envie Content-Type: application/json", 415)
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                raise ApiError("corpo grande demais", 413)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError as exc:
                raise ApiError(f"JSON inválido: {exc}") from None
            if not isinstance(body, dict):
                raise ApiError("corpo deve ser um objeto JSON")
            self._json(self.POST_ROUTES[url.path](self.server.studio, body))
        except ApiError as exc:
            self._error(exc.status, str(exc))
        except Exception as exc:
            print(f"estúdio: erro em POST {url.path}: {exc!r}", file=sys.stderr)
            self._error(500, f"erro interno: {exc}")

    # ------------------------------------------------------------------

    def _host_ok(self) -> bool:
        """Bloqueia DNS rebinding: só aceita Host local."""
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]").lower()
        if host in ("127.0.0.1", "localhost", "::1"):
            return True
        self._error(403, "host não permitido")
        return False

    def _send(self, status: int, body: bytes, content_type: str, cache: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "max-age=60" if cache else "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, data, status: int = 200) -> None:
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _error(self, status: int, message: str) -> None:
        self._json({"erro": message}, status)

    def _file(self, path: Path, cache: bool) -> None:
        if not path.is_file():
            raise ApiError("não encontrado", 404)
        kind = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if kind.startswith("text/") or kind in ("application/json", "application/javascript"):
            kind += "; charset=utf-8"
        data = path.read_bytes()
        match = re.match(r"bytes=(\d*)-(\d*)$", self.headers.get("Range") or "")
        if not match or not data:
            return self._send(200, data, kind, cache)
        # Range: o <video> precisa disso para o scrub (buscar posição no MP4)
        first, last = match.groups()
        size = len(data)
        start = int(first) if first else max(0, size - int(last or 0))
        end = min(int(last), size - 1) if first and last else size - 1
        if start >= size or start > end:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(206)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data[start:end + 1])

    def _static(self, path: str) -> None:
        name = "index.html" if path in ("", "/") else path.lstrip("/")
        if name.startswith("static/"):
            name = name[len("static/"):]
        target = (STATIC_DIR / name).resolve()
        if not target.is_relative_to(STATIC_DIR.resolve()) or not target.is_file():
            raise ApiError("não encontrado", HTTPStatus.NOT_FOUND)
        self._file(target, cache=False)


def _float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        raise ApiError(f"número inválido: {value}") from None


mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("video/mp4", ".mp4")
mimetypes.add_type("image/webp", ".webp")


def make_server(config: Config, port: int = 8765) -> StudioServer:
    return StudioServer(config, port)


def serve(config: Config, port: int = 8765, open_browser: bool = False) -> None:
    server = make_server(config, port)
    print(f"estúdio PixelForge em {server.url}  (Ctrl+C para sair)")
    print(f"  raiz: {server.studio.root}")
    if open_browser:
        threading.Timer(0.5, webbrowser.open, (server.url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nestúdio encerrado")
    finally:
        server.server_close()
