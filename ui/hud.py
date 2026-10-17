"""HUD: топ-бар, панель региона, лог ИИ.

Вынесено из renderer.py (шаг 3.2 рефакторинга).
Принимает renderer как аргумент — нужны шрифты, panel_*, selected_region,
actions и tutorial-состояние.
"""

import pygame

from core.constants import UNIT_STATS


TEXT_COLOR = (240, 240, 240)
GOLD_COLOR = (255, 215, 0)
STRENGTH_COLOR = (200, 220, 255)
HINT_COLOR = (150, 150, 150)
ARMY_TITLE_COLOR = (255, 220, 100)
ATTACK_COLOR = (255, 180, 180)
DEFENSE_COLOR = (180, 200, 255)
ALEXANDER_COLOR = (255, 215, 0)

TOP_BAR_BG = (30, 35, 50)
PANEL_BG = (30, 35, 50)
PANEL_BORDER = (80, 90, 110)
AI_LOG_BG_ALPHA = 180
AI_LOG_BORDER = (80, 90, 110)


def draw_top_bar(screen, game, renderer) -> None:
    """Топ-бар: ход, текущий игрок, золото, сила, подсказка."""
    pygame.draw.rect(screen, TOP_BAR_BG, (0, 0, renderer.width, 50))

    current = game.current_player()
    player = game.players["macedonia"]

    turn_text = renderer.font_medium.render(f"Ход: {game.turn}", True, TEXT_COLOR)
    screen.blit(turn_text, (20, 15))

    who_text = renderer.font_medium.render(
        f"Сейчас: {current.name}", True, (200, 200, 200),
    )
    screen.blit(who_text, (150, 15))

    income = sum(
        game.regions[rid].income
        for rid in player.regions
        if rid in game.regions
    )
    gold_text = renderer.font_medium.render(
        f"Твоё золото: {player.gold} (+{income}/ход)", True, GOLD_COLOR,
    )
    screen.blit(gold_text, (400, 15))

    total_strength = sum(
        army.total_strength()
        for army in game.armies.values()
        if army.owner == player.id
    )
    strength_text = renderer.font_medium.render(
        f"Сила: {total_strength:.0f}", True, STRENGTH_COLOR,
    )
    screen.blit(strength_text, (620, 15))

    hint = renderer.font_small.render(
        "ЛКМ — выбрать регион | ESC — выход", True, HINT_COLOR,
    )
    hint_rect = hint.get_rect(topright=(renderer.width - 20, 20))
    screen.blit(hint, hint_rect)


def draw_info_panel(screen, game, renderer) -> None:
    """Панель выбранного региона: владелец, местность, доход, армия."""
    region = game.regions[renderer.selected_region]

    renderer.panel_h = renderer._calculate_panel_height(region)
    renderer.buttons_y_start = renderer.panel_y + renderer.panel_h + 15

    panel_rect = pygame.Rect(
        renderer.panel_x, renderer.panel_y, renderer.panel_w, renderer.panel_h,
    )
    pygame.draw.rect(screen, PANEL_BG, panel_rect)
    pygame.draw.rect(screen, PANEL_BORDER, panel_rect, 2)

    y = renderer.panel_y + 15
    lines = [
        (region.name, renderer.font_large),
        (f"Владелец: {game.players[region.owner].name if region.owner else 'нейтрал'}",
         renderer.font_medium),
        (f"Местность: {region.terrain}", renderer.font_medium),
        (f"Доход: {region.income}", renderer.font_medium),
        (f"Население: {region.population}", renderer.font_medium),
    ]

    for text, font in lines:
        surf = font.render(text, True, TEXT_COLOR)
        screen.blit(surf, (renderer.panel_x + 15, y))
        y += font.get_height() + 6

    for army in game.armies.values():
        if army.location == region.id and not army.is_empty():
            y += 12

            army_title = renderer.font_medium.render(
                f"Армия: {army.total_count()} юнитов", True, ARMY_TITLE_COLOR,
            )
            screen.blit(army_title, (renderer.panel_x + 15, y))
            y += 25

            attack = army.attack_strength()
            defense = army.defense_strength()

            attack_surf = renderer.font_small.render(
                f"Атака: {attack:.0f}", True, ATTACK_COLOR,
            )
            screen.blit(attack_surf, (renderer.panel_x + 15, y))
            y += 18

            defense_surf = renderer.font_small.render(
                f"Защита: {defense:.0f}", True, DEFENSE_COLOR,
            )
            screen.blit(defense_surf, (renderer.panel_x + 15, y))
            y += 20

            for unit_type, count in army.units.items():
                stats = UNIT_STATS.get(unit_type, {})
                power = stats.get("attack", 0) + stats.get("defense", 0)
                unit_line = f"  {unit_type}: {count} (сила {power} каждый)"
                unit_surf = renderer.font_small.render(
                    unit_line, True, (220, 220, 220),
                )
                screen.blit(unit_surf, (renderer.panel_x + 15, y))
                y += 18

            if army.alexander_attached:
                y += 5
                star_text = renderer.font_small.render(
                    f"★ Александр (+30% к атаке: {attack:.0f} → {attack * 1.3:.0f})",
                    True, ALEXANDER_COLOR,
                )
                screen.blit(star_text, (renderer.panel_x + 15, y))
                y += 18

            break


def draw_ai_log(screen, ai_log: list[str], width: int, height: int, font_small) -> None:
    """Лог действий ИИ (правый нижний угол)."""
    if not ai_log:
        return

    line_height = 22
    padding = 10
    panel_w = 400
    panel_h = len(ai_log) * line_height + padding * 2
    panel_x = width - panel_w - 20
    panel_y = height - panel_h - 20

    panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    bg.fill((0, 0, 0, AI_LOG_BG_ALPHA))
    screen.blit(bg, (panel_x, panel_y))
    pygame.draw.rect(screen, AI_LOG_BORDER, panel, 1)

    y = panel_y + padding
    for line in ai_log:
        surf = font_small.render(line, True, (220, 220, 220))
        screen.blit(surf, (panel_x + padding, y))
        y += line_height