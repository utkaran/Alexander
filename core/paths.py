"""Централизованные пути. Работает и из исходников, и из собранного .exe."""

import sys
from pathlib import Path


def is_frozen() -> bool:
    """Запущены ли мы из собранного .exe."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def resource_path(rel: str) -> Path:
    """Путь к ресурсу (картинки, JSON карты, сцены).

    Из исходников: от корня проекта.
    Из .exe: из временной папки _MEIPASS, куда PyInstaller распаковал --add-data.
    """
    if is_frozen():
        return Path(sys._MEIPASS) / rel
    return Path(__file__).resolve().parent.parent / rel


def save_dir() -> Path:
    """Путь к папке сейвов. ВСЕГДА рядом с exe/проектом, НЕ во временной папке."""
    if is_frozen():
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parent.parent
    d = base / "data" / "saves"
    d.mkdir(parents=True, exist_ok=True)
    return d