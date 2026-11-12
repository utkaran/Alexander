"""Тесты сохранения/загрузки."""
import pytest

from core.save_load import save_game, load_game


def test_save_load_preserves_pending_hints(tmp_path, simple_game):
    """pending_hints сохраняется и загружается."""
    simple_game.pending_hints = ['hint_a', 'hint_b']
    path = tmp_path / "save.json"

    save_game(simple_game, path)
    loaded = load_game(path)

    assert loaded.pending_hints == ['hint_a', 'hint_b']


def test_save_load_preserves_pending_scenes(tmp_path, simple_game):
    """pending_scenes сохраняется и загружается (симметрично)."""
    simple_game.pending_scenes = ['scene_a', 'scene_b']
    path = tmp_path / "save.json"

    save_game(simple_game, path)
    loaded = load_game(path)

    assert loaded.pending_scenes == ['scene_a', 'scene_b']


def test_load_old_save_without_pending_hints(tmp_path, simple_game):
    """Старый сейв без pending_hints загружается без ошибок."""
    import json

    path = tmp_path / "save.json"
    save_game(simple_game, path)

    # Удаляем pending_hints из JSON — эмулируем старый сейв
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    data.pop('pending_hints', None)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    loaded = load_game(path)   # не должно упасть
    assert loaded.pending_hints == []

def test_save_load_preserves_revolt_timers(tmp_path, simple_game):
    """revolt_timers сохраняется и загружается."""
    simple_game.revolt_timers = {'thebes': 2, 'athens': 1}
    path = tmp_path / "save.json"
    save_game(simple_game, path)
    loaded = load_game(path)
    assert loaded.revolt_timers == {'thebes': 2, 'athens': 1}


def test_load_old_save_with_single_revolt_timer(tmp_path, simple_game):
    """Старый сейв с revolt_timer (int) мигрирует в revolt_timers (dict)."""
    import json
    path = tmp_path / "save.json"
    save_game(simple_game, path)

    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    # Эмулируем старый формат
    data.pop('revolt_timers', None)
    data['revolt_timer'] = 3
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    loaded = load_game(path)
    assert loaded.revolt_timers == {'thebes': 3}

def test_load_save_with_obsolete_act1_goal_regions(tmp_path, simple_game):
    """Старый сейв с act1_goal_regions загружается без ошибок."""
    import json
    path = tmp_path / "save.json"
    save_game(simple_game, path)

    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    data["act1_goal_regions"] = ["hellespont"]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

    loaded = load_game(path)  # не должно упасть
    assert loaded.turn == simple_game.turn  # базовая проверка

def test_load_save_without_tutorial_clears_tutorial_state(tmp_path, simple_game):
    """Загрузка сейва без туториала сбрасывает tutorial_active."""
    # Сохраняем игру БЕЗ туториала
    simple_game.tutorial_active = False
    simple_game.tutorial_scene_id = None
    simple_game.tutorial_line_index = 0
    path = tmp_path / "save.json"
    save_game(simple_game, path)

    loaded = load_game(path)
    assert loaded.tutorial_active is False
    assert loaded.tutorial_scene_id is None
    assert loaded.tutorial_line_index == 0