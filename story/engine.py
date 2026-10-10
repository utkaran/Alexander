"""Движок новелл: загрузка сцен, переходы, выборы.

Не знает ничего о Pygame. Чистая логика.
"""

import json
from pathlib import Path
from core.paths import resource_path

class NovelEngine:
    def __init__(self) -> None:
        self.scenes: dict[str, dict] = {}
        self.current_scene_id: str | None = None
        self.current_line_index: int = 0
        self.is_finished: bool = False

        # Туториал: разрешения текущей строки
        self.current_allow_region: str | None = None
        self.current_allow_action: str | None = None

        self.current_allow_unit: str | None = None

        self.current_allow_target: str | None = None

    # ЗАГРУЗКА
    def load_scenes(self, path: str | Path) -> None:
        path = Path(path)
        if not path.is_absolute():
            path = resource_path(str(path))

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
        self._update_allow_from_current_line()

    def start_at(self, scene_id: str, line_index: int) -> None:
        """Начинает новеллу с указанной сцены И строки."""
        if scene_id not in self.scenes:
            raise ValueError(f"Сцена не найдена: {scene_id}")

        self.current_scene_id = scene_id
        self.current_line_index = max(0, line_index)
        self.is_finished = False
        self._update_allow_from_current_line()

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

    def get_position(self) -> tuple[str | None, int]:
        """Возвращает (scene_id, line_index) — текущую позицию."""
        return self.current_scene_id, self.current_line_index

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

    def is_tutorial(self) -> bool:
        """Текущая сцена — обучающая?"""
        scene = self.current_scene()
        if scene is None:
            return False
        return bool(scene.get('is_tutorial', False))

    def current_wait_for(self) -> dict | None:
        """Событие, которого ждёт текущая строка. None — если не ждёт."""
        line = self.current_line()
        if line is None:
            return None
        if 'wait_for' in line:
            return line.get('wait_for')
        scene = self.current_scene()
        if scene is None:
            return None
        return scene.get('wait_for')

    # ДВИЖЕНИЕ

    def _advance_line(self) -> str:
        """Двигает строку вперёд без проверки wait_for.
        Возвращает 'line', 'choices', 'next_scene' или 'final'.
        """
        if self.is_on_last_line():
            scene = self.current_scene()
            if scene is None:
                self.is_finished = True
                return "final"

            if scene.get("choices"):
                return "choices"

            next_id = scene.get("next")
            if next_id:
                self._goto_scene(next_id)
                return "next_scene"

            self.is_finished = True
            return "final"

        self.current_line_index += 1
        self._update_allow_from_current_line()
        return "line"

    def next_line(self) -> str:
        """Переход к следующей строке.

            Возвращает:
            "line"— перешли к следующей строке
            "choices"— строки кончились, есть выборы
            "next_scene" — строки кончились, есть next
            "final" — строки кончились, сцена финальная
        """

        if self.current_wait_for() is not None:
            return "waiting"
        return self._advance_line()

    def choose(self, choice_index: int) -> dict:
        """Применяет выбор. Возвращает dict с 'goto' и 'effects'."""
        scene = self.current_scene()
        if scene  is None:
            raise ValueError('Нет активной сцены')

        choices = scene.get('choices', [])
        if choice_index < 0 or choice_index >= len(choices):
            raise ValueError(f'Неверный индекс выбора: {choice_index}')

        choice = choices[choice_index]
        effects = choice.get('effects', {})
        goto = choice.get('goto')

        if goto:
            self._goto_scene(goto)
        else:
            self.is_finished = True
        return {'goto': goto, 'effects': effects}

    def notify(self, event: str, **kwargs) -> bool:
        wait_for = self.current_wait_for()
        if wait_for is None:
            return False

        if isinstance(wait_for, str):
            expected_event = wait_for
            expected_params = {}
        elif isinstance(wait_for, dict):
            expected_event = wait_for.get("event")
            expected_params = {k: v for k, v in wait_for.items() if k != "event"}
        else:
            return False

        if event != expected_event:
            return False

        for key, value in expected_params.items():
            if kwargs.get(key) != value:
                return False

        # Событие принято — сдвигаем строку НАПРЯМУЮ
        self._advance_line()
        return True

    def _goto_scene(self, scene_id: str) -> None:
        """Переход к другой сцене."""
        if scene_id not in self.scenes:
            raise ValueError(f'Сцена не найдена: {scene_id}')
        self.current_scene_id = scene_id
        self.current_line_index = 0
        self._update_allow_from_current_line()

    def _update_allow_from_current_line(self) -> None:
        """Обновляет разрешения из текущей строки."""
        line = self.current_line()
        if line is None:
            self.current_allow_region = None
            self.current_allow_action = None
            self.current_allow_unit = None
            self.current_allow_target = None
            return

        scene = self.current_scene() or {}

        self.current_allow_region = line.get('allow_region', scene.get('allow_region'))
        self.current_allow_action = line.get('allow_action', scene.get('allow_action'))
        self.current_allow_unit = line.get("allow_unit", scene.get('allow_unit'))
        self.current_allow_target = line.get("allow_target", scene.get('allow_target'))