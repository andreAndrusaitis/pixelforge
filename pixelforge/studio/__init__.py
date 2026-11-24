"""Estúdio web local: python -m pixelforge studio [--porta 8765].

Só stdlib (`http.server`) + HTML/CSS/JS estático em `pixelforge/studio/static/`.
Escuta apenas em 127.0.0.1; a API nunca lê nem grava fora do repositório.
"""

from .server import StudioServer, make_server, serve

__all__ = ["StudioServer", "make_server", "serve"]
