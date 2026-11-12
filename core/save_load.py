"""Сохранение и загрузка GameState в JSON."""
import json
from datetime import datetime
from pathlib import Path

from .game import GameState
from core.paths import save_dir

SAVE_VERSION = 1

def _resolve_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    parts = p.parts
    if len(parts) >= 2 and parts[0] == 'data' and parts[1] == 'saves':
        return save_dir() / Path(*parts[2:])
    from core.paths import resource_path
    return resource_path(str(path))

def save_game(game: GameState, path: str | Path) -> None:
    """Сохраняет GameState в JSON-файл."""
    path = _resolve_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "version": SAVE_VERSION,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        **game.to_dict(),
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_game(path: str | Path) -> GameState:
    """Загружает GameState из JSON-файла."""
    path = _resolve_path(path)
    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    if data.get("version") != SAVE_VERSION:
        raise ValueError(
            f"Несовместимая версия сейва: {data.get('version')}, ожидается {SAVE_VERSION}"
        )
    return GameState.from_dict(data)

def get_save_info(path: str | Path) -> dict | None:
    """Возвращает краткую информацию о сейве без полной загрузки.

    Возвращает {"turn": int, "player": str} или None, если файла нет / он битый.
    """
    p = _resolve_path(path)
    if not p.exists():
        return None
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        return {
            "turn": data.get("turn", 0),
            "player": data.get("current_player_id", "?"),
        }
    except Exception:
        return None