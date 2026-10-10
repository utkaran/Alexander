"""Сохранение и загрузка GameState в JSON."""

import json
from datetime import datetime
from pathlib import Path

from .game import GameState
from .player import Player
from .region import Region
from .army import Army
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

        # Метаданные
        "turn": game.turn,
        "current_player_id": game.current_player_id,
        "_army_counter": game._army_counter,
        "alexander_died": game.alexander_died,
        "game_over": game.game_over,
        "game_over_reason": game.game_over_reason,
        "act1_completed": game.act1_completed,
        "act2_completed": game.act2_completed,
        "act1_goal_regions": sorted(game.act1_goal_regions),
        "act2_goal_regions": sorted(game.act2_goal_regions),
        "tutorial_active": game.tutorial_active,
        "tutorial_scene_id": game.tutorial_scene_id,
        "tutorial_line_index": game.tutorial_line_index,
        'current_act': game.current_act,
        'pending_scenes': list(game.pending_scenes),
        'played_scenes': sorted(game.played_scenes),

        # Регионы
        "regions": [
            {
                "id": r.id,
                "name": r.name,
                "terrain": r.terrain,
                "owner": r.owner,
                "income": r.income,
                "population": r.population,
                "neighbors": list(r.neighbors),
                "is_port": r.is_port,
                "is_capital": r.is_capital,
                "x": r.x,
                "y": r.y,
                "supply": r.supply,
            }
            for r in game.regions.values()
        ],

        # Игроки
        "players": [
            {
                "id": p.id,
                "name": p.name,
                "gold": p.gold,
                "food": p.food,
                "is_ai": p.is_ai,
                "color": list(p.color),
                "regions": list(p.regions),
                "armies": list(p.armies),
            }
            for p in game.players.values()
        ],

        # Армии
        "armies": [
            {
                "id": a.id,
                "owner": a.owner,
                "location": a.location,
                "units": dict(a.units),
                "morale": a.morale,
                "alexander_attached": a.alexander_attached,
                'has_acted': a.has_acted,
            }
            for a in game.armies.values()
        ],
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_game(path: str | Path) -> GameState:
    """Загружает GameState из JSON-файла."""
    path = _resolve_path(path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if data.get("version") != SAVE_VERSION:
        raise ValueError(
            f"Несовместимая версия сейва: {data.get('version')}, ожидается {SAVE_VERSION}"
        )

    game = GameState()

    # Регионы
    for r in data["regions"]:
        region = Region(
            id=r["id"],
            name=r["name"],
            terrain=r["terrain"],
            owner=r["owner"],
            income=r["income"],
            population=r["population"],
            neighbors=list(r["neighbors"]),
            is_port=r["is_port"],
            is_capital=r["is_capital"],
            x=r["x"],
            y=r["y"],
            supply=r["supply"],
        )
        game.regions[region.id] = region

    # Игроки
    for p in data["players"]:
        player = Player(
            id=p["id"],
            name=p["name"],
            gold=p["gold"],
            food=p["food"],
            is_ai=p["is_ai"],
            color=tuple(p["color"]),
            regions=list(p["regions"]),
            armies=list(p["armies"]),
        )
        game.players[player.id] = player

    # Армии
    for a in data["armies"]:
        army = Army(
            id=a["id"],
            owner=a["owner"],
            location=a["location"],
            units=dict(a["units"]),
            morale=a["morale"],
            alexander_attached=a["alexander_attached"],
            has_acted=a.get('has_acted', False)
        )
        game.armies[army.id] = army

    # Метаданные
    game.turn = data["turn"]
    game.current_player_id = data["current_player_id"]
    game._army_counter = data["_army_counter"]
    game.alexander_died = data["alexander_died"]
    game.game_over = data["game_over"]
    game.game_over_reason = data["game_over_reason"]
    game.act1_completed = data["act1_completed"]
    game.act2_completed = data["act2_completed"]
    game.act1_goal_regions = set(data["act1_goal_regions"])
    game.act2_goal_regions = set(data["act2_goal_regions"])

    game.tutorial_active = data.get("tutorial_active", False)
    game.tutorial_scene_id = data.get("tutorial_scene_id", None)
    game.tutorial_line_index = data.get("tutorial_line_index", 0)

    game.current_act = data.get('current_act', 1)
    game.pending_scenes = list(data.get('pending_scenes', []))
    game.played_scenes = set(data.get('played_scenes', []))

    return game

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