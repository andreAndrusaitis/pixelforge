"""Trilha por descrição com ACE-Step 1.5 (MIT).

O ACE-Step fixa versões próprias (torch 2.7.1, transformers < 4.58), então roda num
ambiente separado, criado pelo `uv` dentro de <modelos>/ace-step, e é chamado por
subprocesso. Instalação (uma vez): `python -m pixelforge som instalar musica`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .common import BackendError, models_dir

REPO_URL = "https://github.com/ACE-Step/ACE-Step-1.5.git"
RUNNER = Path(__file__).with_name("ace_runner.py")


def ace_dir(models: Path | None = None) -> Path:
    return Path(os.environ.get("PIXELFORGE_ACE_STEP") or models_dir(models) / "ace-step")


def ace_python(root: Path) -> Path:
    exe = root / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not exe.is_file():
        raise BackendError(f"ACE-Step não instalado em {root}. Rode: python -m pixelforge som instalar musica")
    return exe


def _uv() -> str:
    found = shutil.which("uv") or str(Path(sys.executable).with_name("uv.exe" if sys.platform == "win32" else "uv"))
    if not Path(found).exists():
        raise BackendError("instalar o ACE-Step precisa do uv: pip install uv (vem no extra [audio-ia])")
    return found


def install(models: Path | None = None) -> Path:
    """Clona o ACE-Step 1.5 e cria o ambiente dele com `uv sync` (vários GB)."""
    root = ace_dir(models)
    if not (root / "pyproject.toml").is_file():
        if shutil.which("git") is None:
            raise BackendError("instalar o ACE-Step precisa do git")
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(root)], check=True)
    subprocess.run([_uv(), "sync", "--python", "3.12"], cwd=root, check=True)
    return root


def generate(prompt: str, seconds: float = 30.0, out: Path | str = "out/som/musica.wav", seed: int = 0,
             bpm: int | None = None, lyrics: str = "", lm: bool = True, models: Path | None = None) -> dict:
    """Descrição (de preferência em inglês: gênero, instrumentos, clima) → WAV em `out`.

    Na primeira vez baixa os pesos (~10 GB) para <modelos>/ace-step/checkpoints.
    Devolve {"path", "seconds" (geração), "load_seconds", "lm"}.
    """
    root = ace_dir(models)
    python = ace_python(root)
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    request = {"caption": prompt, "duration": float(seconds), "seed": int(seed), "bpm": bpm,
               "lyrics": lyrics, "out": str(out), "lm": lm}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(request, fh)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "ACESTEP_CHECKPOINTS_DIR": str(root / "checkpoints")}
    try:
        proc = subprocess.run([str(python), str(RUNNER), fh.name], cwd=root, env=env, capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
    finally:
        os.unlink(fh.name)
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("PIXELFORGE_RESULT ")]
    if not lines:
        tail = (proc.stderr or proc.stdout).strip()[-1500:]
        raise BackendError(f"ACE-Step falhou (código {proc.returncode}):\n{tail}")
    result = json.loads(lines[-1].split(" ", 1)[1])
    if "error" in result:
        raise BackendError(f"ACE-Step: {result['error']}")
    return result
