"""Режимы UI: атака, движение, найм.

Каждый режим — маленький класс с методами:
- start() — включить режим
- cancel() — выключить
- is_active() — включён ли
- handle_click(pos, game, actions) — обработать клик (возвращает результат или None)
- draw(screen, renderer) — отрисовать подсказку режима
"""

import pygame


class AttackMode:
    def __init__(self) -> None:
        self.active = False
        self.army_id: str | None = None

    def start(self, army_id: str) -> None:
        self.active = True
        self.army_id = army_id

    def cancel(self) -> None:
        self.active = False
        self.army_id = None

    def is_active(self) -> bool:
        return self.active


class MoveMode:
    def __init__(self) -> None:
        self.active = False
        self.army_id: str | None = None

    def start(self, army_id: str) -> None:
        self.active = True
        self.army_id = army_id

    def cancel(self) -> None:
        self.active = False
        self.army_id = None

    def is_active(self) -> bool:
        return self.active


class RecruitMode:
    def __init__(self) -> None:
        self.active = False
        self.region_id: str | None = None

    def start(self, region_id: str) -> None:
        self.active = True
        self.region_id = region_id

    def cancel(self) -> None:
        self.active = False
        self.region_id = None

    def is_active(self) -> bool:
        return self.active