"""Движок новелл: загрузка сцен, переходы, выборы.

Не знает ничего о Pygame. Чистая логика.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCENES_DIR = PROJECT_ROOT / 'story' / 'scenes'

class NovelEngine:
    def __init__(self) -> None:
        self.scenes: dict[str, dict] = {}
        self.current_scene_id: str | None = None
        self.current_line_index: int = 0
        self.is_finished: bool = False

    # ЗАГРУЗКА
    def load_scenes(self, path: str | Path) -> None:
        path = Path(path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path

        with open(path, encoding='utf-8') as f:
            data = json.load(f)

        for scene in data['scenes']:
            self.scenes[scene['id']] = scene

    # УПРАВЛЕНИЕ

    def start(self, scene_id: str) -> None:
        # Начинает новеллу с указанной сцены.
        if scene_id not in self.scenes:
            raise ValueError(f"Сцена не найдена: {scene_id}")

        self.current_scene_id = scene_id
        self.current_line_index = 0
        self.is_finished = False

    def current_scene(self) -> dict | None:
        # Текущая сцена (dict) или None.
        if self.current_scene_id is None:
            return None
        return self.scenes.get(self.current_scene_id)

    def current_line(self) -> dict | None:
        """Текущая строка (dict) или None, если сцена закончилась."""
        scene = self.current_scene()
        if scene is None:
            return None
        lines = scene.get('lines', [])
        if self.current_line_index >= len(lines):
            return None
        return lines[self.current_line_index]

    def is_on_last_line(self) -> bool:
        """Мы на последней строке сцены?"""
        scene = self.current_scene()
        if scene is None:
            return True
        lines = scene.get('lines', [])
        return self.current_line_index >= len(lines) - 1

    def has_choices(self) -> bool:
        """Есть ли у текущей сцены выборы (после последней строки)?"""
        scene = self.current_scene()
        if scene is None:
            return False
        return bool(scene.get('choices'))

    # ДВИЖЕНИЕ
    def next_line(self) -> str:
        """Переход к следующей строке.

            Возвращает:
            "line"— перешли к следующей строке
            "choices"— строки кончились, есть выборы
            "next_scene" — строки кончились, есть next
            "final" — строки кончились, сцена финальная
        """

        if self.is_on_last_line():
            scene = self.current_scene()
            if scene is None:
                self.is_finished = True
                return 'final'

            if scene.get('choices'):
                return 'choices'

            next_id = scene.get('next')
            if next_id:
                self._goto_scene(next_id)
                return 'next_scene'

            self.is_finished = True
            return 'final'
        self.current_line_index += 1
        return 'line'

    def choose(self, choice_index: int) -> dict:
