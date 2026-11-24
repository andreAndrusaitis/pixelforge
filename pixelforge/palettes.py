"""Cores e paletas.

Paletas são arquivos `.hex` (formato Lospec: um hex por linha, sem `#`).
As embutidas ficam em `pixelforge/palettes/`; as do usuário, na pasta
configurada em `[paths] palettes`, e sobrepõem as embutidas com o mesmo nome.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

RGBA = tuple[int, int, int, int]

BUILTIN_DIR = Path(__file__).parent / "palettes"
TRANSPARENT: RGBA = (0, 0, 0, 0)


def parse_color(value: str | Iterable[int]) -> RGBA:
    """Aceita `#rgb`, `#rrggbb`, `#rrggbbaa`, `transparent` ou tupla RGB(A)."""
    if not isinstance(value, str):
        parts = tuple(int(v) for v in value)
        if len(parts) == 3:
            parts += (255,)
        if len(parts) != 4 or not all(0 <= v <= 255 for v in parts):
            raise ValueError(f"cor inválida: {value!r}")
        return parts  # type: ignore[return-value]

    s = value.strip().lower()
    if s in ("transparent", "none", ""):
        return TRANSPARENT
    s = s.lstrip("#")
    if len(s) in (3, 4):
        s = "".join(c * 2 for c in s)
    if len(s) == 6:
        s += "ff"
    try:
        if len(s) != 8:
            raise ValueError
        rgba = tuple(int(s[i : i + 2], 16) for i in range(0, 8, 2))
    except ValueError:
        raise ValueError(f"cor inválida: {value!r}") from None
    return TRANSPARENT if rgba[3] == 0 else rgba  # type: ignore[return-value]


def to_hex(color: RGBA) -> str:
    if color[3] == 0:
        return "transparent"
    r, g, b, a = color
    return f"#{r:02x}{g:02x}{b:02x}" + ("" if a == 255 else f"{a:02x}")


def luminance(color: RGBA) -> float:
    r, g, b = color[:3]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def darkest(colors: Iterable[RGBA]) -> RGBA:
    opaque = [c for c in colors if c[3] > 0]
    if not opaque:
        raise ValueError("nenhuma cor opaca")
    return min(opaque, key=luminance)


def load_hex_file(path: Path) -> list[RGBA]:
    colors = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split(";", 1)[0].strip()
        if line:
            colors.append(parse_color(line))
    if not colors:
        raise ValueError(f"paleta vazia: {path}")
    return colors


def available(extra_dirs: Iterable[Path] = ()) -> dict[str, Path]:
    """Nome → arquivo. Diretórios posteriores sobrepõem os anteriores."""
    found: dict[str, Path] = {}
    for directory in (BUILTIN_DIR, *extra_dirs):
        if directory and Path(directory).is_dir():
            for path in sorted(Path(directory).glob("*.hex")):
                found[path.stem.lower()] = path
    return found


def get(name: str, extra_dirs: Iterable[Path] = ()) -> list[RGBA]:
    palettes = available(extra_dirs)
    try:
        return load_hex_file(palettes[name.lower()])
    except KeyError:
        names = ", ".join(sorted(palettes))
        raise KeyError(f"paleta '{name}' não encontrada. Disponíveis: {names}") from None
