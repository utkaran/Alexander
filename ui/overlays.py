"""Оверлеи: боевой отчёт, окно найма, game over, завершение акта/туториала.

Вынесено из renderer.py (шаг 3.3 рефакторинга).
Принимает renderer как аргумент — нужны шрифты, recruit-состояние,
tutorial-состояние, actions.
"""

import pygame

from core.constants import UNIT_STATS


TEXT_COLOR = (240, 240, 240)
GOLD_COLOR = (255, 215, 0)
HINT_COLOR = (150, 150, 150)

OVERLAY_DARK = (0, 0, 0, 150)
OVERLAY_GREEN = (0, 30, 0, 180)
OVERLAY_GREEN_STRONG = (0, 30, 0, 200)
OVERLAY_RED = (30, 0, 0, 180)

PANEL_BG = (30, 35, 50)
PANEL_BORDER = (100, 100, 120)
PANEL_BORDER_DIM = (80, 90, 110)

TITLE_GREEN = (100, 255, 100)
TITLE_RED = (255, 100, 100)
TITLE_BLUE = (100, 180, 255)
TITLE_GOLD = (255, 220, 100)
TITLE_WHITE = (255, 255, 255)
SUBTITLE_GREEN = (200, 255, 200)
SUBTITLE_RED = (255, 200, 200)
SUBTITLE_GOLD = (255, 240, 180)
HINT_RED = (200, 150, 150)


# ============================================================
# БОЕВОЙ ОТЧЁТ
# ============================================================
def draw_battle_report(screen, report: dict, width: int, height: int, renderer) -> None:
    """Модальное окно с результатом боя / найма / перемещения / сейва."""
    if not report:
        return

    w, h = 500, 260
    x = (width - w) // 2
    y = (height - h) // 2

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill(OVERLAY_DARK)
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, PANEL_BG, panel, border_radius=12)
    pygame.draw.rect(screen, PANEL_BORDER, panel, 2, border_radius=12)

    if not report.get("ok"):
        title = "ОШИБКА"
        title_color = TITLE_RED
        body = [report.get("reason", "Неизвестная ошибка")]
    elif report.get("winner") == "recruit":
        title = "НАЙМ"
        title_color = TITLE_GREEN
        body = [report.get("recruit_info", "Юнит нанят")]
        if "strength_delta" in report:
            body.append(f"Прирост силы: +{report['strength_delta']:.1f}")
    elif report.get("winner") == "save":
        title = "СОХРАНЕНО"
        title_color = TITLE_GREEN
        body = [report.get("move_info", "Игра сохранена")]
    elif report.get("winner") == "load":
        title = "ЗАГРУЖЕНО"
        title_color = TITLE_BLUE
        body = [report.get("move_info", "Игра загружена")]
    elif report.get("winner") == "move":
        title = "ПЕРЕМЕЩЕНИЕ"
        title_color = TITLE_BLUE
        body = [report.get("move_info", "Армия перемещена")]
    else:
        winner = report["winner"]
        if winner == "attacker":
            title = "ПОБЕДА!"
            title_color = TITLE_GREEN
        else:
            title = "ПОРАЖЕНИЕ"
            title_color = TITLE_RED

        body = [
            f"Регион: {report['region']}",
            f"Потери: {report['losses']}",
            f"Сила атакующего: {report.get('attacker_strength', '?')}",
            f"Сила защитника: {report.get('defender_strength', '?')}",
        ]

    title_surf = renderer.font_large.render(title, True, title_color)
    title_rect = title_surf.get_rect(center=(width // 2, y + 40))
    screen.blit(title_surf, title_rect)

    ty = y + 90
    for line in body:
        surf = renderer.font_medium.render(line, True, TEXT_COLOR)
        surf_rect = surf.get_rect(center=(width // 2, ty))
        screen.blit(surf, surf_rect)
        ty += 32

    if report.get("alexander_died"):
        death_surf = renderer.font_medium.render(
            "★ Александр погиб. Империя распадается...",
            True, (255, 80, 80),
        )
        death_rect = death_surf.get_rect(center=(width // 2, ty + 10))
        screen.blit(death_surf, death_rect)

    hint = renderer.font_small.render("Кликните, чтобы закрыть", True, HINT_COLOR)
    hint_rect = hint.get_rect(center=(width // 2, y + h - 20))
    screen.blit(hint, hint_rect)


# ============================================================
# ОКНО НАЙМА
# ============================================================
def draw_recruit_window(screen, game, renderer) -> None:
    """Модальное окно найма юнитов в выбранном регионе."""
    width, height = renderer.width, renderer.height

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    w, h = 520, 420
    x = (width - w) // 2
    y = (height - h) // 2

    panel = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, PANEL_BG, panel, border_radius=12)
    pygame.draw.rect(screen, PANEL_BORDER, panel, 2, border_radius=12)

    region = game.regions[renderer.recruit.region_id]
    title = renderer.font_large.render(f"Найм в {region.name}", True, TEXT_COLOR)
    title_rect = title.get_rect(center=(width // 2, y + 35))
    screen.blit(title, title_rect)

    me = game.players.get("macedonia")
    gold_text = renderer.font_medium.render(
        f"Золото: {me.gold}", True, GOLD_COLOR,
    )
    gold_rect = gold_text.get_rect(center=(width // 2, y + 75))
    screen.blit(gold_text, gold_rect)

    current_strength = renderer.actions.get_army_strength_in_region(renderer.recruit.region_id)
    strength_text = renderer.font_medium.render(
        f"Текущая сила армии: {current_strength:.0f}", True, (200, 200, 200),
    )
    strength_rect = strength_text.get_rect(center=(width // 2, y + 105))
    screen.blit(strength_text, strength_rect)

    mouse_pos = pygame.mouse.get_pos()
    unit_list = list(UNIT_STATS.items())
    item_h = 50
    start_y = y + 120

    for i, (unit_type, stats) in enumerate(unit_list):
        item_rect = pygame.Rect(x + 30, start_y + i * (item_h + 8), w - 60, item_h)
        cost = stats["cost"]
        can_afford = me.gold >= cost
        allowed = renderer._is_tutorial_allowed_unit(unit_type)
        hovered = item_rect.collidepoint(mouse_pos) and can_afford

        if not allowed:
            bg = (30, 30, 35)
            text_col = (70, 70, 70)
        elif not can_afford:
            bg = (40, 40, 50)
            text_col = (100, 100, 100)
        elif hovered:
            bg = (60, 100, 80)
            text_col = (255, 255, 255)
        else:
            bg = (45, 55, 70)
            text_col = TEXT_COLOR

        pygame.draw.rect(screen, bg, item_rect, border_radius=8)

        show_highlight = (
            renderer.tutorial_active
            and renderer.tutorial_engine.current_allow_unit == unit_type
            and not hovered
        )
        if show_highlight:
            pygame.draw.rect(screen, (255, 215, 0), item_rect, 3, border_radius=8)

        name_surf = renderer.font_medium.render(unit_type, True, text_col)
        name_rect = name_surf.get_rect(midleft=(item_rect.x + 20, item_rect.centery))
        screen.blit(name_surf, name_rect)

        power = stats["attack"] + stats["defense"]
        strength_after = current_strength + power
        strength_surf = renderer.font_small.render(
            f"Сила: {current_strength:.0f} → {strength_after:.0f}",
            True,
            (200, 220, 200) if can_afford else (100, 100, 100),
        )
        strength_rect = strength_surf.get_rect(midright=(item_rect.right - 130, item_rect.centery))
        screen.blit(strength_surf, strength_rect)

        cost_surf = renderer.font_medium.render(f"{cost} зол.", True, text_col)
        cost_rect = cost_surf.get_rect(midright=(item_rect.right - 20, item_rect.centery))
        screen.blit(cost_surf, cost_rect)

    hint = renderer.font_small.render(
        "Клик по юниту — нанять 1 | ESC или клик мимо — закрыть",
        True, HINT_COLOR,
    )
    hint_rect = hint.get_rect(center=(width // 2, y + h - 20))
    screen.blit(hint, hint_rect)


# ============================================================
# GAME OVER
# ============================================================
def draw_game_over_overlay(screen, game, width: int, height: int, renderer) -> None:
    """Оверлей конца игры: победа, потеря Пеллы, кампания, смерть Александра."""
    reason = game.game_over_reason

    if reason == 'victory':
        overlay_color = OVERLAY_GREEN
        title = "АКТ I ПРОЙДЕН"
        title_color = TITLE_GREEN
        subtitle = "Греция укрощена. Александр смотрит на восток."
        subtitle_color = SUBTITLE_GREEN
    elif reason == 'pella_lost':
        overlay_color = OVERLAY_RED
        title = "ПЕЛЛА ПОТЕРЯНА"
        title_color = (255, 80, 80)
        subtitle = "Македония пала. Поход окончен."
        subtitle_color = SUBTITLE_RED
    elif reason == 'campaign_complete':
        overlay_color = OVERLAY_GREEN_STRONG
        title = "Кампания пройдена!"
        title_color = TITLE_GOLD
        subtitle = "Александр дошёл до края мира. Но это только начало..."
        subtitle_color = SUBTITLE_GOLD
    else:
        overlay_color = OVERLAY_RED
        title = "АЛЕКСАНДР ПОГИБ"
        title_color = (255, 80, 80)
        subtitle = "Империя распадается. Симуляция распада — в разработке."
        subtitle_color = SUBTITLE_RED

    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill(overlay_color)
    screen.blit(overlay, (0, 0))

    title_surf = renderer.font_huge.render(title, True, title_color)
    title_rect = title_surf.get_rect(center=(width // 2, height // 2 - 30))
    screen.blit(title_surf, title_rect)

    subtitle_surf = renderer.font_medium.render(subtitle, True, subtitle_color)
    subtitle_rect = subtitle_surf.get_rect(center=(width // 2, height // 2 + 20))
    screen.blit(subtitle_surf, subtitle_rect)

    hint = renderer.font_small.render("ESC — выход", True, HINT_RED)
    hint_rect = hint.get_rect(center=(width // 2, height // 2 + 70))
    screen.blit(hint, hint_rect)


# ============================================================
# ЗАВЕРШЕНИЕ АКТА
# ============================================================
def draw_act_completed_overlay(screen, width: int, height: int, renderer) -> None:
    """Оверлей «АКТ I ПРОЙДЕН» (временный, 5 секунд)."""
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill(OVERLAY_GREEN)
    screen.blit(overlay, (0, 0))

    title = renderer.font_huge.render("АКТ I ПРОЙДЕН", True, TITLE_GREEN)
    title_rect = title.get_rect(center=(width // 2, height // 2 - 30))
    screen.blit(title, title_rect)

    subtitle = renderer.font_medium.render(
        "Греция укрощена. Александр смотрит на восток.", True, SUBTITLE_GREEN,
    )
    subtitle_rect = subtitle.get_rect(center=(width // 2, height // 2 + 20))
    screen.blit(subtitle, subtitle_rect)

    hint = renderer.font_small.render(
        "Персия пробудилась. Новая цель: захватить три персидские столицы.",
        True, TITLE_GOLD,
    )
    hint_rect = hint.get_rect(center=(width // 2, height // 2 + 70))
    screen.blit(hint, hint_rect)


# ============================================================
# ЗАВЕРШЕНИЕ ТУТОРИАЛА
# ============================================================
def draw_tutorial_complete_overlay(screen, width: int, height: int, renderer) -> None:
    """Оверлей «ОБУЧЕНИЕ ЗАВЕРШЕНО» (2 секунды)."""
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill(OVERLAY_GREEN)
    screen.blit(overlay, (0, 0))

    title = renderer.font_huge.render("ОБУЧЕНИЕ ЗАВЕРШЕНО", True, TITLE_GREEN)
    title_rect = title.get_rect(center=(width // 2, height // 2 - 20))
    screen.blit(title, title_rect)

    subtitle = renderer.font_medium.render(
        "Теперь ты готов покорить мир. Удачи, завоеватель!",
        True, SUBTITLE_GREEN,
    )
    subtitle_rect = subtitle.get_rect(center=(width // 2, height // 2 + 30))
    screen.blit(subtitle, subtitle_rect)