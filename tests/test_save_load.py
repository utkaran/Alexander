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