"""Тест сохранения и загрузки GameState."""

import os
from pathlib import Path
os.chdir(Path(__file__).parent.parent)

from core.game import GameState
from core.army import Army
from core.save_load import save_game, load_game


def setup_game() -> GameState:
    game = GameState()
    game.load_map('data/map_act1.json')

    army = Army(id='army1', owner='macedonia', location='pella')
    army.add_units('Фаланга', 5)
    army.add_units('Гетайры', 2)
    army.alexander_attached = True
    game.armies[army.id] = army
    game.players['macedonia'].armies.append(army.id)

    game.start('macedonia')
    return game


def test_save_load_roundtrip() -> None:
    game = setup_game()

    # Что-то меняем, чтобы сейв не был идентичен старту
    game.recruit('macedonia', 'pella', 'Лучники', 2)
    game.end_turn()  # ход переходит Греции

    save_path = Path('data/saves/_test_roundtrip.json')
    save_game(game, save_path)

    loaded = load_game(save_path)

    # Сравниваем ключевые поля
    assert loaded.turn == game.turn, f"turn: {loaded.turn} != {game.turn}"
    assert loaded.current_player_id == game.current_player_id
    assert loaded._army_counter == game._army_counter
    assert len(loaded.regions) == len(game.regions)
    assert len(loaded.players) == len(game.players)
    assert len(loaded.armies) == len(game.armies)

    # Сравниваем конкретную армию
    assert 'army1' in loaded.armies
    loaded_army = loaded.armies['army1']
    assert loaded_army.owner == 'macedonia'
    assert loaded_army.location == 'pella'
    assert loaded_army.alexander_attached is True
    assert loaded_army.units == {'Фаланга': 5, 'Гетайры': 2, 'Лучники': 2}

    # Сравниваем игрока
    assert loaded.players['macedonia'].gold == game.players['macedonia'].gold
    assert loaded.players['macedonia'].regions == game.players['macedonia'].regions

    # Сравниваем регион
    assert loaded.regions['pella'].owner == 'macedonia'
    assert loaded.regions['pella'].name == 'Пелла'

    # Убираем тестовый сейв
    save_path.unlink()
    print("✅ test_save_load_roundtrip — OK")


def test_double_roundtrip() -> None:
    """Сохранить → загрузить → сохранить → загрузить. Должно быть стабильно."""
    game = setup_game()
    game.end_turn()

    path1 = Path('data/saves/_test_rt1.json')
    path2 = Path('data/saves/_test_rt2.json')

    save_game(game, path1)
    game2 = load_game(path1)
    save_game(game2, path2)
    game3 = load_game(path2)

    assert game3.turn == game.turn
    assert game3.current_player_id == game.current_player_id
    assert len(game3.armies) == len(game.armies)

    path1.unlink()
    path2.unlink()
    print("✅ test_double_roundtrip — OK")


if __name__ == '__main__':
    test_save_load_roundtrip()
    test_double_roundtrip()
    print("\nВсе тесты сейвов пройдены.")