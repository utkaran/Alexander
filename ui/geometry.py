"""Геометрия карты: масштаб и экранные координаты регионов.

Чистые функции — не зависят от Renderer, легко тестируются.
"""

import pygame


def compute_scale(game, screen_w: int, screen_h: int, padding: int = 100) -> tuple[float, float]:
    """Вычисляет масштаб карты под экран."""
    if not game.regions:
        return 1.0, 1.0
    xs = [r.x for r in game.regions.values()]
    ys = [r.y for r in game.regions.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    map_w = max_x - min_x or 1
    map_h = max_y - min_y or 1

    scale_x = (screen_w - padding * 2) / map_w
    scale_y = (screen_h - padding * 2) / map_h
    return scale_x, scale_y


def screen_pos(game, region, scale_x: float, scale_y: float, padding: int = 100) -> tuple[int, int]:
    """Экранные координаты региона."""
    xs = [r.x for r in game.regions.values()]
    ys = [r.y for r in game.regions.values()]
    min_x, min_y = min(xs), min(ys)

    x = padding + (region.x - min_x) * scale_x
    y = padding + (region.y - min_y) * scale_y
    return int(x), int(y)