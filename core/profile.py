"""Глобальный профиль игрока: разблокировки, банк наследия.

Живёт рядом с сейвами (save_dir/profile.json), НЕ в _MEIPASS.
Заглушка для Этапа 6 (Наследие). Поля есть, механика — потом.
"""

import json
from pathlib import Path

from core.paths import save_dir


PROFILE_VERSION = 1


def _profile_path() -> Path:
    return save_dir() / "profile.json"


def load_profile() -> dict:
    """Загружает профиль. Если файла нет — возвращает дефолт."""
    path = _profile_path()
    if not path.exists():
        return _default_profile()

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return _default_profile()

    # Миграция: добавляем недостающие поля
    default = _default_profile()
    for key, value in default.items():
        data.setdefault(key, value)
    return data


def save_profile(profile: dict) -> None:
    """Сохраняет профиль."""
    path = _profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)


def _default_profile() -> dict:
    return {
        "version": PROFILE_VERSION,
        "campaigns_completed": 0,
        "historical_ending_seen": False,
        "alternate_unlocked": False,
        "legacy_points_bank": 0,
        "scenarios_unlocked": [],
    }