"""Сохранение и загрузка GameState в JSON."""

import json
from datetime import datetime
from pathlib import Path

from .game import GameState
from .player import Player
from .region import Region
from .army import Army


SAVE_VERSION = 1
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_SAVE_DIR = PROJECT_ROOT / "data" / "saves"

def _resolve_path(path: str | Path) -> Path:
    p = Path(path)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p


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

    return game