"""Тесты движка новелл."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from story.engine import NovelEngine


def test_load_and_walk():
    engine = NovelEngine()
    engine.load_scenes("story/scenes/prologue.json")
    engine.start("prologue_01")

    # Сцена 1, строка 1
    line = engine.current_line()
    assert line["who"] == "narrator"
    assert "Ночь" in line["text"]

    # Далее
    result = engine.next_line()
    assert result == "line"
    assert engine.current_line()["who"] == "philip"

    # Далее
    result = engine.next_line()
    assert result == "line"
    assert engine.current_line()["who"] == "olympias"

    # Далее
    result = engine.next_line()
    assert result == "line"
    assert engine.current_line()["who"] == "narrator"

    # Далее — переходим в следующую сцену
    result = engine.next_line()
    assert result == "next_scene"
    assert engine.current_scene_id == "prologue_02"
    assert engine.current_line()["who"] == "narrator"

    print("✅ test_load_and_walk — OK")


def test_final_scene():
    engine = NovelEngine()
    engine.load_scenes("story/scenes/prologue.json")
    engine.start("prologue_04")

    # Прокручиваем до конца
    while True:
        result = engine.next_line()
        if result == "final":
            break

    assert engine.is_finished
    print("✅ test_final_scene — OK")


if __name__ == "__main__":
    test_load_and_walk()
    test_final_scene()
    print("\nВсе тесты новелл пройдены.")