"""Отрисовка игрового мира на Pygame."""

import pygame

from core.game import GameState
from core.constants import UNIT_STATS
from ui.actions import ActionController
from ui.widgets import Button


BG_COLOR = (20, 25, 35)
LINE_COLOR = (80, 90, 110)
TEXT_COLOR = (240, 240, 240)
HIGHLIGHT_COLOR = (255, 220, 100)
TARGET_COLOR = (255, 80, 80)
ATTACK_BTN_COLOR = (150, 50, 50)
RECRUIT_BTN_COLOR = (50, 120, 80)
MOVE_BTN_COLOR = (50, 100, 150)


class Renderer:
    def __init__(self, screen: pygame.Surface, game: GameState) -> None:
        self.screen = screen
        self.game = game
        self.actions = ActionController(game)
        self.width, self.height = screen.get_size()

        self.font_small = pygame.font.SysFont("arial", 14, bold=True)
        self.font_medium = pygame.font.SysFont("arial", 18, bold=True)
        self.font_large = pygame.font.SysFont("arial", 24, bold=True)
        self.font_huge = pygame.font.SysFont("arial", 48, bold=True)

        self.scale_x, self.scale_y = self._compute_scale()
        self.selected_region: str | None = None

        self.panel_x = self.width - 320
        self.panel_y = 70
        self.panel_w = 300
        self.panel_h = 200

        self.buttons_y_start = 0
        self.buttons_x = self.panel_x + 50

        btn_w, btn_h = 220, 60
        self.end_turn_button = Button(
            x=self.width - btn_w - 30,
            y=self.height - btn_h - 30,
            width=btn_w,
            height=btn_h,
            text="КОНЕЦ ХОДА",
            font=self.font_large,
        )

        self.save_button = Button(
            x=0, y=8, width=90, height=34,
            text="СОХР.",
            font=self.font_small,
            color=(60, 100, 60),
            hover_color=(80, 140, 80),
        )
        self.load_button = Button(
            x=0, y=8, width=90, height=34,
            text="ЗАГР.",
            font=self.font_small,
            color=(60, 80, 120),
            hover_color=(80, 110, 160)
        )

        self.attack_button = Button(
            x=0, y=0, width=200, height=45,
            text='Атаковать!',
            font=self.font_medium,
            color=ATTACK_BTN_COLOR,
            hover_color=(200, 70, 70),
        )
        self.attack_button.enabled = False

        self.recruit_button = Button(
            x=0, y=0, width=200, height=45,
            text="НАНЯТЬ",
            font=self.font_medium,
            color=RECRUIT_BTN_COLOR,
            hover_color=(70, 160, 110),
        )
        self.recruit_button.enabled = False

        self.move_button = Button(
            x=0, y=0, width=200, height=45,
            text="ДВИГАТЬСЯ",
            font=self.font_medium,
            color=MOVE_BTN_COLOR,
            hover_color=(70, 130, 190),
        )
        self.move_button.enabled = False

        self.attack_mode = False
        self.attacker_army_id: str | None = None

        self.recruit_mode = False
        self.recruit_region_id: str | None = None

        self.move_mode = False
        self.moving_army_id: str | None = None

        self.battle_report: dict | None = None
        self.battle_report_timer = 0

        self.ai_turn_active = False

        # Анимация хода ИИ
        self.ai_plan:list[dict] = []
        self.ai_action_timer = 0
        self.ai_action_delay = 700
        self.ai_log: list[str] = []

        self.act_completed_overlay_timer = 0

        self._act_overlay_shown = False

    def reset_state(self) -> None:
        """Сбрасывает всё UI-состояние. Вызывать при смене хода."""
        self.selected_region = None
        self._cancel_attack()
        self._cancel_move()
        self._close_recruit()
        self.battle_report = None
        self.battle_report_timer = 0
        self.ai_log = []
        self.ai_plan = []
        self.ai_turn_active = False

    # ============================================================
    # ГЕОМЕТРИЯ
    # ============================================================
    def _compute_scale(self) -> tuple[float, float]:
        if not self.game.regions:
            return 1.0, 1.0
        xs = [r.x for r in self.game.regions.values()]
        ys = [r.y for r in self.game.regions.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        padding = 100
        map_w = max_x - min_x or 1
        map_h = max_y - min_y or 1

        scale_x = (self.width - padding * 2) / map_w
        scale_y = (self.height - padding * 2) / map_h
        return scale_x, scale_y

    def _screen_pos(self, region) -> tuple[int, int]:
        xs = [r.x for r in self.game.regions.values()]
        ys = [r.y for r in self.game.regions.values()]
        min_x, min_y = min(xs), min(ys)

        padding = 100
        x = padding + (region.x - min_x) * self.scale_x
        y = padding + (region.y - min_y) * self.scale_y
        return int(x), int(y)

    # ============================================================
    # РЕЖИМЫ (только UI-состояние, логика — в ActionController)
    # ============================================================
    def _start_attack_mode(self) -> None:
        if not self.selected_region:
            return
        army_id = self.actions.get_army_in_region(self.selected_region)
        if not army_id:
            return
        self.attack_mode = True
        self.attacker_army_id = army_id

    def _cancel_attack(self) -> None:
        self.attack_mode = False
        self.attacker_army_id = None

    def _execute_attack(self, target_region_id: str) -> None:
        result = self.actions.execute_attack(self.attacker_army_id, target_region_id)
        self.battle_report = result
        self.battle_report_timer = 3000
        self._cancel_attack()
        self.selected_region = target_region_id

    def _start_move_mode(self) -> None:
        if not self.selected_region:
            return
        army_id = self.actions.get_army_in_region(self.selected_region)
        if not army_id:
            return
        self.move_mode = True
        self.moving_army_id = army_id

    def _cancel_move(self) -> None:
        self.move_mode = False
        self.moving_army_id = None

    def _execute_move(self, target_region_id: str) -> None:
        result = self.actions.execute_move(self.moving_army_id, target_region_id)
        if result['ok']:
            self.battle_report = {
                "ok": True,
                "winner": "move",
                "region": result["to"],
                "move_info": "Армия объединена" if result.get("merged") else "Армия перемещена",
            }
            self.battle_report_timer = 1500
        self._cancel_move()
        self.selected_region = target_region_id

    def _open_recruit(self) -> None:
        if not self.selected_region:
            return
        if not self.actions.can_recruit_in(self.selected_region):
            return
        self.recruit_mode = True
        self.recruit_region_id = self.selected_region

    def _close_recruit(self) -> None:
        self.recruit_mode = False
        self.recruit_region_id = None

    def _execute_recruit(self, unit_type: str) -> None:
        """Нанимает 1 юнит в выбранном регионе."""
        if not self.recruit_region_id:
            return

        strength_before = self.actions.get_army_strength_in_region(self.recruit_region_id)
        result = self.actions.execute_recruit(self.recruit_region_id, unit_type, 1)

        if result["ok"]:
            region_name = self.game.regions[self.recruit_region_id].name
            strength_after = self.actions.get_army_strength_in_region(self.recruit_region_id)
            delta = strength_after - strength_before

            self._close_recruit()
            self.battle_report = {
                "ok": True,
                "winner": "recruit",
                "region": region_name,
                "losses": 0,
                "recruit_info": f"Нанят: {unit_type}",
                "strength_delta": delta,
            }
            self.battle_report_timer = 1500
        else:
            self.battle_report = {
                "ok": False,
                "reason": result.get("reason", "Не удалось нанять"),
            }
            self.battle_report_timer = 2000

    # ============================================================
    # ОТРИСОВКА
    # ============================================================
    def draw(self) -> None:
        self.screen.fill(BG_COLOR)
        self._draw_connections()
        self._draw_regions()
        if self.selected_region and not self.attack_mode and not self.move_mode:
            self._draw_info_panel()
        self._draw_top_bar()

        mouse_pos = pygame.mouse.get_pos()
        self.end_turn_button.update(mouse_pos)
        self.end_turn_button.enabled = not self.ai_turn_active and not self.game.game_over
        self.end_turn_button.draw(self.screen)

        if (self.selected_region
                and not self.ai_turn_active
                and not self.game.game_over
                and not self.recruit_mode
                and not self.attack_mode
                and not self.move_mode):
            army_id = self.actions.get_army_in_region(self.selected_region)
            is_mine = self.actions.is_my_region(self.selected_region)

            btn_y = self.buttons_y_start
            btn_x = self.buttons_x

            if is_mine:
                self.recruit_button.rect.x = btn_x
                self.recruit_button.rect.y = btn_y
                self.recruit_button.enabled = True
                self.recruit_button.update(mouse_pos)
                self.recruit_button.draw(self.screen)
                btn_y += 55
            else:
                self.recruit_button.enabled = False

            if army_id and not self.attack_mode and not self.move_mode:
                self.attack_button.rect.x = btn_x
                self.attack_button.rect.y = btn_y
                self.attack_button.enabled = True
                self.attack_button.update(mouse_pos)
                self.attack_button.draw(self.screen)
                btn_y += 55
            else:
                self.attack_button.enabled = False

            if army_id and not self.attack_mode and not self.move_mode:
                self.move_button.rect.x = btn_x
                self.move_button.rect.y = btn_y
                self.move_button.enabled = True
                self.move_button.update(mouse_pos)
                self.move_button.draw(self.screen)
                btn_y += 55
            else:
                self.move_button.enabled = False

        if self.attack_mode:
            text = self.font_medium.render(
                "Выберите цель атаки (клик по красному региону). ESC — отмена",
                True, TARGET_COLOR
            )
            text_rect = text.get_rect(center=(self.width // 2, 70))
            self.screen.blit(text, text_rect)

        if self.move_mode:
            text = self.font_medium.render(
                "Выберите свой регион для перемещения. ESC — отмена",
                True, (100, 180, 255)
            )
            text_rect = text.get_rect(center=(self.width // 2, 70))
            self.screen.blit(text, text_rect)

        if self.ai_turn_active:
            text = self.font_medium.render(
                f"Ход ИИ: {self.game.current_player().name}...",
                True, (255, 220, 100),
            )
            text_rect = text.get_rect(center=(self.width // 2, self.height - 50))
            self.screen.blit(text, text_rect)

        if self.battle_report:
            self._draw_battle_report()

        if self.recruit_mode:
            self._draw_recruit_window()

        if self.act_completed_overlay_timer > 0 and not self.game.game_over:
            self._draw_act_completed_overlay()

        if self.game.game_over:
            self._draw_game_over_overlay()

        if self.ai_log and self.ai_turn_active:
            self._draw_ai_log()

    def _draw_act_completed_overlay(self) -> None:
        """Оверлей «Акт пройден», исчезает через несколько секунд."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 30, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.font_huge.render("АКТ I ПРОЙДЕН", True, (100, 255, 100))
        title_rect = title.get_rect(center=(self.width // 2, self.height // 2 - 30))
        self.screen.blit(title, title_rect)

        subtitle = self.font_medium.render(
            "Греция укрощена. Александр смотрит на восток.",
            True, (200, 255, 200),
        )
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, self.height // 2 + 20))
        self.screen.blit(subtitle, subtitle_rect)

        hint = self.font_small.render(
            "Персия пробудилась. Новая цель: захватить три персидские столицы.",
            True, (255, 220, 100),
        )
        hint_rect = hint.get_rect(center=(self.width // 2, self.height // 2 + 70))
        self.screen.blit(hint, hint_rect)

    def _draw_game_over_overlay(self) -> None:
        """Оверлей при завершении игры (победа, смерть Александра, потеря Пеллы)."""
        reason = self.game.game_over_reason

        if reason == 'victory':
            overlay_color = (0, 30, 0, 180)
            title = "АКТ I ПРОЙДЕН"
            title_color = (100, 255, 100)
            subtitle = "Греция укрощена. Александр смотрит на восток."
            subtitle_color = (200, 255, 200)
        elif reason == 'pella_lost':
            overlay_color = (30, 0, 0, 180)
            title = "ПЕЛЛА ПОТЕРЯНА"
            title_color = (255, 80, 80)
            subtitle = "Македония пала. Поход окончен."
            subtitle_color = (255, 200, 200)
        elif reason == 'campaign_complete':
            overlay_color = (0, 30, 0, 200)
            title = 'Кампания пройдена!'
            title_color = (255, 220, 100)
            subtitle = "Александр дошёл до края мира. Но это только начало..."
            subtitle_color = (255, 240, 180)
        else:  # 'alexander_died' или None
            overlay_color = (30, 0, 0, 180)
            title = "АЛЕКСАНДР ПОГИБ"
            title_color = (255, 80, 80)
            subtitle = "Империя распадается. Симуляция распада — в разработке."
            subtitle_color = (255, 200, 200)

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill(overlay_color)
        self.screen.blit(overlay, (0, 0))

        title_surf = self.font_huge.render(title, True, title_color)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 2 - 30))
        self.screen.blit(title_surf, title_rect)

        subtitle_surf = self.font_medium.render(subtitle, True, subtitle_color)
        subtitle_rect = subtitle_surf.get_rect(center=(self.width // 2, self.height // 2 + 20))
        self.screen.blit(subtitle_surf, subtitle_rect)

        hint = self.font_small.render("ESC — выход", True, (200, 150, 150))
        hint_rect = hint.get_rect(center=(self.width // 2, self.height // 2 + 70))
        self.screen.blit(hint, hint_rect)

    def _draw_connections(self) -> None:
        drawn = set()
        for region in self.game.regions.values():
            x1, y1 = self._screen_pos(region)
            for neighbor_id in region.neighbors:
                if neighbor_id not in self.game.regions:
                    continue
                pair = tuple(sorted([region.id, neighbor_id]))
                if pair in drawn:
                    continue
                drawn.add(pair)

                neighbor = self.game.regions[neighbor_id]
                x2, y2 = self._screen_pos(neighbor)
                pygame.draw.line(self.screen, LINE_COLOR, (x1, y1), (x2, y2), 2)

    def _draw_regions(self) -> None:
        for region in self.game.regions.values():
            x, y = self._screen_pos(region)

            if region.owner and region.owner in self.game.players:
                color = self.game.players[region.owner].color
            else:
                color = (120, 120, 120)

            radius = 24

            if self.attack_mode and self.actions.is_valid_attack_target(self.attacker_army_id, region.id):
                pygame.draw.circle(self.screen, TARGET_COLOR, (x, y), radius + 6, 4)

            if self.move_mode and self.actions.is_valid_move_target(self.moving_army_id, region.id):
                pygame.draw.circle(self.screen, (100, 180, 255), (x, y), radius + 6, 4)

            if self.selected_region == region.id:
                pygame.draw.circle(self.screen, HIGHLIGHT_COLOR, (x, y), radius + 4, 3)

            pygame.draw.circle(self.screen, color, (x, y), radius)
            pygame.draw.circle(self.screen, (20, 20, 20), (x, y), radius, 2)

            text = self.font_small.render(region.name, True, TEXT_COLOR)
            text_rect = text.get_rect(center=(x, y + radius + 12))
            self.screen.blit(text, text_rect)

            for army in self.game.armies.values():
                if army.location == region.id and not army.is_empty():
                    count = army.total_count()
                    army_text = self.font_medium.render(str(count), True, (255, 255, 255))
                    army_rect = army_text.get_rect(center=(x, y))
                    self.screen.blit(army_text, army_rect)

                    if army.alexander_attached:
                        star = self.font_large.render("★", True, (255, 215, 0))
                        star_rect = star.get_rect(center=(x + 22, y - 22))
                        self.screen.blit(star, star_rect)
                    break

    def _draw_top_bar(self) -> None:
        pygame.draw.rect(self.screen, (30, 35, 50), (0, 0, self.width, 50))

        current = self.game.current_player()
        player = self.game.players["macedonia"]

        turn_text = self.font_medium.render(f"Ход: {self.game.turn}", True, TEXT_COLOR)
        self.screen.blit(turn_text, (20, 15))

        who_text = self.font_medium.render(
            f"Сейчас: {current.name}",
            True, (200, 200, 200),
        )
        self.screen.blit(who_text, (150, 15))

        income = sum(
            self.game.regions[rid].income
            for rid in player.regions
            if rid in self.game.regions
        )
        gold_text = self.font_medium.render(
            f"Твоё золото: {player.gold} (+{income}/ход)",
            True, (255, 215, 0),
        )
        self.screen.blit(gold_text, (400, 15))

        total_strength = sum(
            army.total_strength()
            for army in self.game.armies.values()
            if army.owner == player.id
        )
        strength_text = self.font_medium.render(
            f"Сила: {total_strength:.0f}",
            True, (200, 220, 255),
        )
        self.screen.blit(strength_text, (620, 15))

        hint = self.font_small.render(
            "ЛКМ — выбрать регион | ESC — выход",
            True, (150, 150, 150),
        )
        hint_rect = hint.get_rect(topright=(self.width - 220, 20))
        self.screen.blit(hint, hint_rect)

        # Кнопки сейвов — в правом верхнем углу
        mouse_pos = pygame.mouse.get_pos()

        self.save_button.rect.x = self.width - 200
        self.save_button.update(mouse_pos)
        self.save_button.draw(self.screen)

        self.load_button.rect.x = self.width - 100
        self.load_button.update(mouse_pos)
        self.load_button.draw(self.screen)

    def _draw_info_panel(self) -> None:
        region = self.game.regions[self.selected_region]

        self.panel_h = self._calculate_panel_height(region)
        self.buttons_y_start = self.panel_y + self.panel_h + 15

        panel_rect = pygame.Rect(self.panel_x, self.panel_y, self.panel_w, self.panel_h)
        pygame.draw.rect(self.screen, (30, 35, 50), panel_rect)
        pygame.draw.rect(self.screen, (80, 90, 110), panel_rect, 2)

        y = self.panel_y + 15
        lines = [
            (region.name, self.font_large),
            (f"Владелец: {self.game.players[region.owner].name if region.owner else 'нейтрал'}", self.font_medium),
            (f"Местность: {region.terrain}", self.font_medium),
            (f"Доход: {region.income}", self.font_medium),
            (f"Население: {region.population}", self.font_medium),
        ]

        for text, font in lines:
            surf = font.render(text, True, TEXT_COLOR)
            self.screen.blit(surf, (self.panel_x + 15, y))
            y += font.get_height() + 6

        for army in self.game.armies.values():
            if army.location == region.id and not army.is_empty():
                y += 12

                army_title = self.font_medium.render(
                    f"Армия: {army.total_count()} юнитов",
                    True, (255, 220, 100),
                )
                self.screen.blit(army_title, (self.panel_x + 15, y))
                y += 25

                strength_surf = self.font_small.render(
                    f"Сила: {army.total_strength():.0f}",
                    True, (200, 220, 255),
                )
                self.screen.blit(strength_surf, (self.panel_x + 15, y))
                y += 20

                for unit_type, count in army.units.items():
                    stats = UNIT_STATS.get(unit_type, {})
                    power = stats.get("attack", 0) + stats.get("defense", 0)
                    unit_line = f"  {unit_type}: {count} (сила {power} каждый)"
                    unit_surf = self.font_small.render(
                        unit_line,
                        True, (220, 220, 220),
                    )
                    self.screen.blit(unit_surf, (self.panel_x + 15, y))
                    y += 18

                if army.alexander_attached:
                    y += 5
                    star_text = self.font_small.render(
                        "★ Александр (+30% к атаке)",
                        True, (255, 215, 0),
                    )
                    self.screen.blit(star_text, (self.panel_x + 15, y))
                    y += 18

                break

    def _draw_ai_log(self) -> None:
        """Лог событий хода ИИ в правом нижнем углу."""
        if not self.ai_log:
            return

        # Размер панели
        line_height = 22
        padding = 10
        panel_w = 400
        panel_h = len(self.ai_log) * line_height + padding * 2
        panel_x = self.width - panel_w - 20
        panel_y = self.height - panel_h - 20

        # Фон
        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        self.screen.blit(bg, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (80, 90, 110), panel, 1)

        # Строки
        y = panel_y + padding
        for line in self.ai_log:
            surf = self.font_small.render(line, True, (220, 220, 220))
            self.screen.blit(surf, (panel_x + padding, y))
            y += line_height

    def start_ai_turn(self, game: GameState) -> None:
        from core.ai import ai_plan

        current = game.current_player()
        self.ai_plan = ai_plan(game, current.id)
        self.ai_action_timer = 0
        self.ai_log = []
        self.ai_turn_active = True

    def _execute_next_ai_action(self) -> None:
        from core.ai import execute_action
        if not self.ai_plan:
            self._finish_ai_turn()
            return
        action = self.ai_plan.pop(0)
        result = execute_action(self.game, action)

        # Пишем в лог
        player_name = self.game.current_player().name
        log_line = f"[{player_name}] {result['text']}"
        self.ai_log.append(log_line)
        if len(self.ai_log) > 8:
            self.ai_log.pop(0)

            # Если после действия игра закончилась (смерть Александра, победа)
        if self.game.game_over:
            self.ai_turn_active = False
            self.ai_plan = []
            return

            # Если действие было атакой — покажем отчёт о бое на 2 секунды
        if result.get("type") == "attack" and result.get("battle"):
            self.battle_report = result["battle"]
            self.battle_report_timer = 2000
                # Задержим следующее действие чуть дольше, чтобы игрок успел прочитать
            self.ai_action_delay = 2200
        else:
            self.ai_action_delay = 700

    def _finish_ai_turn(self) -> None:
        """Завершает ход ИИ: передаёт ход следующему игроку."""
        self.ai_turn_active = False
        self.ai_plan = []
        self.game.end_turn()

        next_player = self.game.current_player()
        if next_player.is_ai:
            # Следующий тоже ИИ — запускаем его ход
            self.start_ai_turn(self.game)
        # Если игрок — ничего не делаем, ход переходит к нему
    def _calculate_panel_height(self, region) -> int:
        base_h = 15
        base_h += self.font_large.get_height() + 6
        base_h += (self.font_medium.get_height() + 6) * 4

        for army in self.game.armies.values():
            if army.location == region.id and not army.is_empty():
                base_h += 12
                base_h += self.font_medium.get_height() + 6
                base_h += self.font_small.get_height() + 6
                base_h += len(army.units) * (self.font_small.get_height() + 4)
                if army.alexander_attached:
                    base_h += self.font_small.get_height() + 9
                break

        base_h += 15
        return base_h

    def _draw_recruit_window(self) -> None:
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        w, h = 520, 420
        x = (self.width - w) // 2
        y = (self.height - h) // 2

        panel = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, (30, 35, 50), panel, border_radius=12)
        pygame.draw.rect(self.screen, (100, 100, 120), panel, 2, border_radius=12)

        region = self.game.regions[self.recruit_region_id]
        title = self.font_large.render(f"Найм в {region.name}", True, TEXT_COLOR)
        title_rect = title.get_rect(center=(self.width // 2, y + 35))
        self.screen.blit(title, title_rect)

        me = self.game.players.get("macedonia")
        gold_text = self.font_medium.render(
            f"Золото: {me.gold}",
            True, (255, 215, 0),
        )
        gold_rect = gold_text.get_rect(center=(self.width // 2, y + 75))
        self.screen.blit(gold_text, gold_rect)

        current_strength = self.actions.get_army_strength_in_region(self.recruit_region_id)
        strength_text = self.font_medium.render(
            f"Текущая сила армии: {current_strength:.0f}",
            True, (200, 200, 200),
        )
        strength_rect = strength_text.get_rect(center=(self.width // 2, y + 105))
        self.screen.blit(strength_text, strength_rect)

        mouse_pos = pygame.mouse.get_pos()
        unit_list = list(UNIT_STATS.items())
        item_h = 50
        start_y = y + 120

        for i, (unit_type, stats) in enumerate(unit_list):
            item_rect = pygame.Rect(x + 30, start_y + i * (item_h + 8), w - 60, item_h)
            cost = stats["cost"]
            can_afford = me.gold >= cost
            hovered = item_rect.collidepoint(mouse_pos) and can_afford

            if not can_afford:
                bg = (40, 40, 50)
                text_col = (100, 100, 100)
            elif hovered:
                bg = (60, 100, 80)
                text_col = (255, 255, 255)
            else:
                bg = (45, 55, 70)
                text_col = TEXT_COLOR

            pygame.draw.rect(self.screen, bg, item_rect, border_radius=8)
            pygame.draw.rect(self.screen, (80, 90, 110), item_rect, 1, border_radius=8)

            name_surf = self.font_medium.render(unit_type, True, text_col)
            name_rect = name_surf.get_rect(midleft=(item_rect.x + 20, item_rect.centery))
            self.screen.blit(name_surf, name_rect)

            power = stats["attack"] + stats["defense"]
            strength_after = current_strength + power
            strength_surf = self.font_small.render(
                f"Сила: {current_strength:.0f} → {strength_after:.0f}",
                True,
                (200, 220, 200) if can_afford else (100, 100, 100),
            )
            strength_rect = strength_surf.get_rect(midright=(item_rect.right - 130, item_rect.centery))
            self.screen.blit(strength_surf, strength_rect)

            cost_surf = self.font_medium.render(f"{cost} зол.", True, text_col)
            cost_rect = cost_surf.get_rect(midright=(item_rect.right - 20, item_rect.centery))
            self.screen.blit(cost_surf, cost_rect)

        hint = self.font_small.render(
            "Клик по юниту — нанять 1 | ESC или клик мимо — закрыть",
            True, (150, 150, 150),
        )
        hint_rect = hint.get_rect(center=(self.width // 2, y + h - 20))
        self.screen.blit(hint, hint_rect)

    def _draw_battle_report(self) -> None:
        if not self.battle_report:
            return
        report = self.battle_report

        w, h = 500, 260
        x = (self.width - w) // 2
        y = (self.height - h) // 2

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.screen, (30, 35, 50), panel, border_radius=12)
        pygame.draw.rect(self.screen, (100, 100, 120), panel, 2, border_radius=12)

        if not report.get("ok"):
            title = "ОШИБКА"
            title_color = (255, 100, 100)
            body = [report.get("reason", "Неизвестная ошибка")]
        elif report.get("winner") == "recruit":
            title = "НАЙМ"
            title_color = (100, 255, 150)
            body = [report.get("recruit_info", "Юнит нанят")]
            if "strength_delta" in report:
                body.append(f"Прирост силы: +{report['strength_delta']:.1f}")
        elif report.get('winner') == 'save':
            title = 'СОХРАНЕНО'
            title_color = (100, 255, 150)
            body = [report.get('move_info', 'Игра сохранена')]
        elif report.get('winner') == 'load':
            title = 'ЗАГРУЖЕНО'
            title_color = (100, 180, 255)
            body = [report.get('move_info', 'Игра загружена')]
        elif report.get('winner') == 'move':
            title = 'ПЕРЕМЕЩЕНИЕ'
            title_color = (100, 180, 255)
            body = [report.get('move_info', 'Армия перемещена')]
        else:
            winner = report["winner"]
            if winner == "attacker":
                title = "ПОБЕДА!"
                title_color = (100, 255, 100)
            else:
                title = "ПОРАЖЕНИЕ"
                title_color = (255, 100, 100)

            body = [
                f"Регион: {report['region']}",
                f"Потери: {report['losses']}",
                f"Сила атакующего: {report.get('attacker_strength', '?')}",
                f"Сила защитника: {report.get('defender_strength', '?')}",
            ]

        title_surf = self.font_large.render(title, True, title_color)
        title_rect = title_surf.get_rect(center=(self.width // 2, y + 40))
        self.screen.blit(title_surf, title_rect)

        ty = y + 90
        for line in body:
            surf = self.font_medium.render(line, True, TEXT_COLOR)
            surf_rect = surf.get_rect(center=(self.width // 2, ty))
            self.screen.blit(surf, surf_rect)
            ty += 32

        if report.get("alexander_died"):
            death_surf = self.font_medium.render(
                "★ Александр погиб. Империя распадается...",
                True, (255, 80, 80),
            )
            death_rect = death_surf.get_rect(center=(self.width // 2, ty + 10))
            self.screen.blit(death_surf, death_rect)

        hint = self.font_small.render("Кликните, чтобы закрыть", True, (150, 150, 150))
        hint_rect = hint.get_rect(center=(self.width // 2, y + h - 20))
        self.screen.blit(hint, hint_rect)

    def update(self, dt: int) -> None:
        if self.battle_report:
            self.battle_report_timer -= dt
            if self.battle_report_timer <= 0:
                self.battle_report = None

        if self.act_completed_overlay_timer > 0:
            self.act_completed_overlay_timer -= dt

        # Проверяем, не завершился ли акт только что
        if (self.game.act1_completed
            and not self.game.game_over
            and not self._act_overlay_shown):
            self.act_completed_overlay_timer = 5000
            self._act_overlay_shown = True

        if self.ai_turn_active:
            self.ai_action_timer += dt
            if self.ai_action_timer >= self.ai_action_delay:
                self.ai_action_timer = 0
                self._execute_next_ai_action()

    # ============================================================
    # ОБРАБОТКА КЛИКОВ
    # ============================================================
    def handle_click(self, pos: tuple[int, int]) -> str | None:

        if self.game.game_over:
            return None

        if self.save_button.is_clicked(pos):
            return 'save_game'

        if self.load_button.is_clicked(pos):
            return 'load_game'

        if self.act_completed_overlay_timer > 0:
            return None

        if self.recruit_mode:
            return self._handle_recruit_click(pos)

        if self.battle_report:
            self.battle_report = None
            return None

        if self.move_mode:
            for region in self.game.regions.values():
                x, y = self._screen_pos(region)
                dx = pos[0] - x
                dy = pos[1] - y
                if dx * dx + dy * dy <= 24 * 24:
                    if self.actions.is_valid_move_target(self.moving_army_id, region.id):
                        self._execute_move(region.id)
                    return None
            self._cancel_move()
            return None

        if self.attack_mode:
            for region in self.game.regions.values():
                x, y = self._screen_pos(region)
                dx = pos[0] - x
                dy = pos[1] - y
                if dx * dx + dy * dy <= 24 * 24:
                    if self.actions.is_valid_attack_target(self.attacker_army_id, region.id):
                        self._execute_attack(region.id)
                    return None
            self._cancel_attack()
            return None

        if self.end_turn_button.is_clicked(pos):
            return "end_turn"

        if self.recruit_button.enabled and self.recruit_button.is_clicked(pos):
            self._open_recruit()
            return None

        if self.attack_button.enabled and self.attack_button.is_clicked(pos):
            self._start_attack_mode()
            return None

        if self.move_button.enabled and self.move_button.is_clicked(pos):
            self._start_move_mode()
            return None

        for region in self.game.regions.values():
            x, y = self._screen_pos(region)
            dx = pos[0] - x
            dy = pos[1] - y
            if dx * dx + dy * dy <= 24 * 24:
                self.selected_region = region.id
                return None

        self.selected_region = None
        return None

    def _handle_recruit_click(self, pos: tuple[int, int]) -> str | None:
        w, h = 520, 420
        x = (self.width - w) // 2
        y = (self.height - h) // 2

        me = self.game.players.get("macedonia")
        unit_list = list(UNIT_STATS.items())
        item_h = 50
        start_y = y + 120

        for i, (unit_type, stats) in enumerate(unit_list):
            item_rect = pygame.Rect(x + 30, start_y + i * (item_h + 8), w - 60, item_h)
            if item_rect.collidepoint(pos):
                if me.gold >= stats["cost"]:
                    self._execute_recruit(unit_type)
                return None

        panel = pygame.Rect(x, y, w, h)
        if not panel.collidepoint(pos):
            self._close_recruit()
        return None

    def handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            if self.attack_mode:
                self._cancel_attack()
            elif self.move_mode:
                self._cancel_move()
            elif self.recruit_mode:
                self._close_recruit()