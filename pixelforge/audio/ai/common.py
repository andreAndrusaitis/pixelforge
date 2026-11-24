"""Pasta de modelos, checagem de dependências e escolha de dispositivo."""

from __future__ import annotations

import importlib
import importlib.util
import os
import warnings
from pathlib import Path

INSTALL_HINT = "pip install -e .[audio-ia]  (e PyTorch com CUDA; veja o docs/manual.md, seção Som)"


class BackendError(RuntimeError):
    """Dependência, modelo ou GPU indisponível para um backend de IA."""


def models_dir(override: Path | str | None = None) -> Path:
    """Onde ficam os pesos: argumento > $PIXELFORGE_MODELS > ~/.cache/pixelforge.

    Fica fora do repositório por padrão (pesos têm GBs; a pasta do projeto pode
    estar sincronizada com nuvem). Configurável em `[som] modelos` no pixelforge.toml.
    """
    path = Path(override or os.environ.get("PIXELFORGE_MODELS") or Path.home() / ".cache" / "pixelforge")
    path = path.expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def use_hf_cache(base: Path) -> Path:
    """Aponta o cache do Hugging Face para <modelos>/hf (antes de importar as libs)."""
    cache = base / "hf"
    os.environ["HF_HUB_CACHE"] = str(cache)
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("DIFFUSERS_VERBOSITY", "error")
    for category in (UserWarning, FutureWarning, DeprecationWarning):
        warnings.filterwarnings("ignore", category=category)
    return cache


def require(module: str, what: str):
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        raise BackendError(f"{what} precisa do pacote '{module}' ({exc.name} não encontrado). Instale: {INSTALL_HINT}") from None


def device(prefer: str | None = None) -> str:
    torch = require("torch", "som por IA")
    if prefer:
        return prefer
    return "cuda" if torch.cuda.is_available() else "cpu"


def available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None
