"""Тесты движка новелл."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from story.engine import NovelEngine


def test_load_and_walk():
    engine = NovelEngine()
    engine.load_scenes("story/scenes/prologue.json")
    engine.start("prologue_01")

    scene1 = engine.current_scene()
    assert scene1 is not None, "Сцена prologue_01 не загружена"

    line_count = len(scene1["lines"])
    assert line_count >= 2, "В сцене должно быть минимум 2 строки"

    line0 = engine.current_line()
    assert line0 is not None
    assert "who" in line0 and "text" in line0

    for i in range(line_count - 1):
        result = engine.next_line()
        assert result == "line", f"На шаге {i} ожидали 'line', получили {result}"

    result = engine.next_line()
    assert result == "next_scene", f"Ожидали 'next_scene', получили {result}"
    assert engine.current_scene_id == "prologue_02"

    print("✅ test_load_and_walk — OK")


def test_final_scene():
    engine = NovelEngine()
    engine.load_scenes("story/scenes/prologue.json")
    engine.start("prologue_04")

    while True:
        result = engine.next_line()
        if result == "final":
            break

    assert engine.is_finished
    print("✅ test_final_scene — OK")


def test_wait_for():
    """Проверяем блокировку и разблокировку через wait_for."""
    engine = NovelEngine()

    # Создаём тестовую сцену прямо в движке
    engine.scenes["test_wait"] = {
        "id": "test_wait",
        "title": "Тест",
        "is_tutorial": True,
        "lines": [
            {"who": "narrator", "text": "Первая строка"},
            {
                "who": "alexander",
                "text": "Нажми на кнопку",
                "wait_for": {"event": "button_clicked", "id": "recruit"},
            },
            {"who": "narrator", "text": "Третья строка"},
        ],
    }
    engine.start("test_wait")

    # Первая строка — обычная
    assert engine.current_line()["text"] == "Первая строка"
    result = engine.next_line()
    assert result == "line"

    # Вторая строка — с wait_for. Не двигается без события.
    assert engine.current_line()["text"] == "Нажми на кнопку"
    result = engine.next_line()
    assert result == "waiting", f"Ожидали 'waiting', получили {result}"

    # Событие с неправильным id — не принимается
    assert engine.notify("button_clicked", id="move") is False

    # Событие с правильным id — принимается, движок идёт дальше
    assert engine.notify("button_clicked", id="recruit") is True
    assert engine.current_line()["text"] == "Третья строка"

    print("✅ test_wait_for — OK")


def test_allow_permissions():
    """Проверяем, что allow_region и allow_action читаются."""
    engine = NovelEngine()
    engine.scenes["test_allow"] = {
        "id": "test_allow",
        "is_tutorial": True,
        "lines": [
            {
                "who": "alexander",
                "text": "Только Фессалия, только найм",
                "allow_region": "thessaly",
                "allow_action": "recruit",
                "wait_for": {"event": "recruit_completed", "region": "thessaly"},
            },
            {
                "who": "alexander",
                "text": "Свободен",
            },
        ],
    }
    engine.start("test_allow")

    print(f"DEBUG: current_line = {engine.current_line()}")
    print(f"DEBUG: current_allow_region = {engine.current_allow_region}")
    print(f"DEBUG: current_allow_action = {engine.current_allow_action}")

    assert engine.current_allow_region == "thessaly"
    assert engine.current_allow_action == "recruit"
    assert engine.is_tutorial() is True

    engine.notify("recruit_completed", region="thessaly")

    assert engine.current_allow_region is None
    assert engine.current_allow_action is None

    print("✅ test_allow_permissions — OK")


if __name__ == "__main__":
    test_load_and_walk()
    test_final_scene()
    test_wait_for()
    test_allow_permissions()
    print("\nВсе тесты новелл пройдены.")