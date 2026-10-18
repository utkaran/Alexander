"""Отрисовка карты: связи между регионами, сами регионы, подсветка цели.

Вынесено из renderer.py (шаг 3.1 рефакторинга).
Не знает про Renderer напрямую — принимает его как аргумент,
потому что внутри нужны режимы (attack/move), туториал и шрифты.
"""

import pygame

from ui.geometry import screen_pos


BG_COLOR = (20, 25, 35)
LINE_COLOR = (80, 90, 110)
TEXT_COLOR = (240, 240, 240)
HIGHLIGHT_COLOR = (255, 220, 100)
TARGET_COLOR = (255, 80, 80)
MOVE_TARGET_COLOR = (100, 180, 255)
TUTORIAL_TARGET_COLOR = (255, 255, 100)
FORCED_OBJECTIVE_COLOR = (255, 80, 80)

REGION_RADIUS = 24


def draw_connections(screen, game, scale_x: float, scale_y: float) -> None:
    """Рисует линии между соседними регионами (без дублей)."""
    drawn = set()
    for region in game.regions.values():
        x1, y1 = screen_pos(game, region, scale_x, scale_y)
        for neighbor_id in region.neighbors:
            if neighbor_id not in game.regions:
                continue
            pair = tuple(sorted([region.id, neighbor_id]))
            if pair in drawn:
                continue
            drawn.add(pair)

            neighbor = game.regions[neighbor_id]
            x2, y2 = screen_pos(game, neighbor, scale_x, scale_y)
            pygame.draw.line(screen, LINE_COLOR, (x1, y1), (x2, y2), 2)


def draw_regions(screen, game, renderer, scale_x: float, scale_y: float) -> None:
    """Рисует регионы: цвет владельца, выделение, подсветка целей, армии.

    renderer нужен для:
      - renderer.attack / renderer.move (режимы)
      - renderer.actions (валидация целей)
      - renderer.selected_region
      - renderer.tutorial_active, renderer.tutorial_engine
      - renderer.font_small / font_medium / font_large
    """
    for region in game.regions.values():
        x, y = screen_pos(game, region, scale_x, scale_y)

        if region.owner and region.owner in game.players:
            color = game.players[region.owner].color
        else:
            color = (120, 120, 120)

        radius = REGION_RADIUS

        # Подсветка цели атаки
        if renderer.attack.is_active() and renderer.actions.is_valid_attack_target(
            renderer.attack.army_id, region.id
        ):
            pygame.draw.circle(screen, TARGET_COLOR, (x, y), radius + 6, 4)
            if (renderer.tutorial.active
                    and renderer.tutorial.engine.current_allow_target == region.id):
                pygame.draw.circle(screen, TUTORIAL_TARGET_COLOR, (x, y), radius + 12, 3)

        # Подсветка цели движения
        if renderer.move.is_active() and renderer.actions.is_valid_move_target(
            renderer.move.army_id, region.id
        ):
            pygame.draw.circle(screen, MOVE_TARGET_COLOR, (x, y), radius + 6, 4)
            if (renderer.tutorial.active
                    and renderer.tutorial.engine.current_allow_target == region.id):
                pygame.draw.circle(screen, TUTORIAL_TARGET_COLOR, (x, y), radius + 12, 3)

        # Выделение выбранного региона
        if renderer.selected_region == region.id:
            pygame.draw.circle(screen, HIGHLIGHT_COLOR, (x, y), radius + 4, 3)

        # Сам регион
        pygame.draw.circle(screen, color, (x, y), radius)
        pygame.draw.circle(screen, (20, 20, 20), (x, y), radius, 2)

        # Название
        text = renderer.font_small.render(region.name, True, TEXT_COLOR)
        text_rect = text.get_rect(center=(x, y + radius + 12))
        screen.blit(text, text_rect)

        # Армия в регионе (первая непустая)
        for army in game.armies.values():
            if army.location == region.id and not army.is_empty():
                count = army.total_count()
                army_text = renderer.font_medium.render(str(count), True, (255, 255, 255))
                army_rect = army_text.get_rect(center=(x, y))
                screen.blit(army_text, army_rect)

                if army.alexander_attached:
                    star = renderer.font_large.render("★", True, (255, 215, 0))
                    star_rect = star.get_rect(center=(x + 22, y - 22))
                    screen.blit(star, star_rect)
                break


def draw_forced_objective_highlight(screen, game, scale_x: float, scale_y: float) -> None:
    """Пульсирующая подсветка обязательной цели (например, Фивы)."""
    import math

    region = game.regions.get(game.forced_objective)
    if region is None:
        return
    x, y = screen_pos(game, region, scale_x, scale_y)
    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 200.0)
    base = FORCED_OBJECTIVE_COLOR
    color = (
        int(base[0] * (0.4 + 0.6 * pulse)),
        int(base[1] * (0.4 + 0.6 * pulse)),
        int(base[2] * (0.4 + 0.6 * pulse)),
    )
    pygame.draw.circle(screen, color, (x, y), REGION_RADIUS + 12, 2)
    pygame.draw.circle(screen, color, (x, y), REGION_RADIUS + 8, 4)