"""Отрисовка игрового мира на Pygame."""

import pygame

from core.game import GameState
from core.constants import UNIT_STATS
from ui.actions import ActionController
from ui.widgets import Button
from ui.novel_view import NovelView
from ui.tutorial_view import TutorialView, draw_highlight
from story.engine import NovelEngine


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
        self.ai_plan: list[dict] = []
        self.ai_action_timer = 0
        self.ai_action_delay = 700
        self.ai_log: list[str] = []

        self.act_completed_overlay_timer = 0
        self._act_overlay_shown = False

        # Новелла
        self.novel_active = False
        self.novel_engine = NovelEngine()
        self.novel_view = NovelView(screen, self.novel_engine)
        self.novel_on_finish_callback = None

        # Туториал
        self.tutorial_active = False
        self.tutorial_engine = NovelEngine()
        self.tutorial_view: TutorialView | None = None
        self.tutorial_final_overlay_timer = 0

        self.tutorial_pending_notify: dict | None = None  # отложенное событие

    def reset_state(self) -> None:
        """Сбрасывает UI-состояние при смене хода."""
        self.selected_region = None
        self._cancel_attack()
        self._cancel_move()
        self._close_recruit()
        self.battle_report = None
        self.battle_report_timer = 0
        self.ai_log = []
        self.ai_plan = []
        self.ai_turn_active = False

    def reset(self) -> None:
        """Полный сброс рендерера."""
        self.reset_state()
        self.act_completed_overlay_timer = 0
        self._act_overlay_shown = False
        self.novel_active = False
        self.novel_engine = NovelEngine()
        self.novel_view = NovelView(self.screen, self.novel_engine)
        self.novel_on_finish_callback = None
        self.tutorial_active = False
        self.tutorial_engine = NovelEngine()
        self.tutorial_view = None
        self.tutorial_final_overlay_timer = 0

    def _is_tutorial_allowed_unit(self, unit_type: str) -> bool:
        """Разрешён ли найм этого юнита в туториале."""
        if not self.tutorial_active or self.tutorial_view is None:
            return True
        allow = self.tutorial_engine.current_allow_unit
        return allow is None or allow == unit_type

    def _is_tutorial_allowed_target(self, region_id: str) -> bool:
        """Разрешена ли атака/движение в этот регион в туториале."""
        if not self.tutorial_active or self.tutorial_view is None:
            return True
        allow = self.tutorial_engine.current_allow_target
        return allow is None or allow == region_id

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
    # НОВЕЛЛА
    # ============================================================
    def start_novel(self, scene_file: str, start_scene: str, on_finish=None) -> None:
        self.novel_engine = NovelEngine()
        self.novel_engine.load_scenes(scene_file)
        self.novel_engine.start(start_scene)
        self.novel_view = NovelView(self.screen, self.novel_engine)
        self.novel_active = True
        self.novel_on_finish_callback = on_finish

    def _end_novel(self) -> None:
        self.novel_active = False
        callback = self.novel_on_finish_callback
        self.novel_on_finish_callback = None
        if callback:
            callback()

    def _handle_novel_result(self, result: dict | None) -> None:
        if result is None:
            return

        action = result.get("action")

        if action == "next":
            if result.get("result") == "next_scene":
                title = self.novel_engine.current_scene().get("title", "")
                self.novel_view.start_transition(title)
            if self.novel_engine.is_finished:
                self._end_novel()

        elif action == "choice":
            self._apply_novel_effects(result.get("effects", {}))
            goto = result.get("goto")
            if goto and not self.novel_engine.is_finished:
                title = self.novel_engine.current_scene().get("title", "")
                self.novel_view.start_transition(title)
            if self.novel_engine.is_finished:
                self._end_novel()

    def _apply_novel_effects(self, effects: dict) -> None:
        if not effects:
            return
        gold = effects.get("gold")
        if gold is not None and "macedonia" in self.game.players:
            self.game.players["macedonia"].gold += gold

    # ============================================================
    # ТУТОРИАЛ
    # ============================================================
    def start_tutorial(self, scene_file: str = "story/scenes/tutorial.json",
                       start_scene: str = "tutorial_01") -> None:
        """Запускает туториал с начала."""
        self._start_tutorial_at(scene_file, start_scene, 0)

    def start_tutorial_at(self, scene_id: str, line_index: int,
                          scene_file: str = "story/scenes/tutorial.json") -> None:
        """Запускает туториал с сохранённой позиции."""
        self._start_tutorial_at(scene_file, scene_id, line_index)

    def _start_tutorial_at(self, scene_file: str, scene_id: str, line_index: int) -> None:
        """Внутренний запуск туториала на конкретной позиции."""
        self.tutorial_engine = NovelEngine()
        self.tutorial_engine.load_scenes(scene_file)
        self.tutorial_engine.start_at(scene_id, line_index)
        self.tutorial_view = TutorialView(self.screen, self.tutorial_engine)
        self.tutorial_view.highlight_drawer = self._draw_tutorial_highlight
        self.tutorial_active = True
        self.game.tutorial_active = True
        self.tutorial_final_overlay_timer = 0

    def _end_tutorial(self) -> None:
        """Завершает туториал."""
        self.tutorial_active = False
        self.game.tutorial_active = False
        self.game.tutorial_scene_id = None
        self.game.tutorial_line_index = 0
        self.tutorial_view = None
        self.tutorial_final_overlay_timer = 2000

    def _draw_tutorial_highlight(self, highlight_list: list, pulse: float) -> None:
        """Рисует подсветку туториала на карте."""
        for h in highlight_list:
            h_type = h.get("type")
            color_name = h.get("color", "gold")

            if color_name == "capital":
                base_color = (255, 240, 120)
            elif color_name == "enemy":
                base_color = (255, 80, 80)
            else:
                base_color = (255, 215, 0)

                # Пульсация яркости: от 35% до 100%
            brightness = 0.35 + 0.65 * pulse
            color = (
                int(base_color[0] * brightness),
                int(base_color[1] * brightness),
                int(base_color[2] * brightness),
            )

            if h_type == "region_owner":
                owner = h.get("owner")
                for region in self.game.regions.values():
                    if region.owner == owner:
                        x, y = self._screen_pos(region)
                        pygame.draw.circle(self.screen, color, (x, y), 24 + 8 + 4, 2)
                        pygame.draw.circle(self.screen, color, (x, y), 24 + 8, 4)

            elif h_type == "region":
                region_id = h.get("id")
                region = self.game.regions.get(region_id)
                if region is None:
                    continue
                x, y = self._screen_pos(region)
                pygame.draw.circle(self.screen, color, (x, y), 24 + 8 + 4, 2)
                pygame.draw.circle(self.screen, color, (x, y), 24 + 8, 4)
                if color_name == "capital":
                    pygame.draw.circle(self.screen, color, (x, y), 24 + 8 + 8, 2)

            elif h_type == "button":
                btn_id = h.get("id")
                btn = self._get_button_by_id(btn_id)
                if btn is None or not btn.enabled:
                    continue

                if self.recruit_mode or self.attack_mode or self.move_mode:
                    continue
                expanded = btn.rect.inflate(16, 16)
                pygame.draw.rect(self.screen, color, expanded, 4, border_radius=10)

    def _get_button_by_id(self, btn_id: str) -> Button | None:
        """Возвращает кнопку по id."""
        mapping = {
            "recruit_button": self.recruit_button,
            "move_button": self.move_button,
            "attack_button": self.attack_button,
            "end_turn_button": self.end_turn_button,
        }
        return mapping.get(btn_id)

    def _handle_tutorial_result(self, result: dict | None) -> None:
        """Обработка результата от TutorialView."""
        self._sync_tutorial_position()

        if result is None:
            return

        action = result.get("action")
        if action == "next":
            if self.tutorial_engine.is_finished:
                self._end_tutorial()

    def _notify_tutorial(self, event: str, **kwargs) -> None:
        """Сообщает движку туториала о событии."""
        if not self.tutorial_active or self.tutorial_view is None:
            return
        self.tutorial_engine.notify(event, **kwargs)
        self._sync_tutorial_position()

    def _sync_tutorial_position(self) -> None:
        """Синхронизирует позицию туториала в GameState (для сохранения)."""
        if not self.tutorial_active:
            return
        scene_id, line_index = self.tutorial_engine.get_position()
        self.game.tutorial_scene_id = scene_id
        self.game.tutorial_line_index = line_index

    def _is_tutorial_allowed_region(self, region_id: str) -> bool:
        """Разрешён ли клик по региону в туториале."""
        if not self.tutorial_active or self.tutorial_view is None:
            return True
        allow = self.tutorial_engine.current_allow_region
        return allow is None or allow == region_id

    def _is_tutorial_allowed_action(self, action: str) -> bool:
        """Разрешено ли действие в туториале."""
        if not self.tutorial_active or self.tutorial_view is None:
            return True
        allow = self.tutorial_engine.current_allow_action
        return allow is None or allow == action

    # ============================================================
    # РЕЖИМЫ (UI)
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

        # Туториал: сообщаем о событии
        if result.get("ok") and result.get("winner") == "attacker":
            self._notify_tutorial("attack_completed", region=target_region_id)

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

            # Туториал: сообщаем о событии
            self._notify_tutorial("move_completed", to=target_region_id)

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
        if not self.recruit_region_id:
            return

        region_id = self.recruit_region_id
        strength_before = self.actions.get_army_strength_in_region(region_id)
        result = self.actions.execute_recruit(region_id, unit_type, 1)

        if result["ok"]:
            region_name = self.game.regions[region_id].name
            strength_after = self.actions.get_army_strength_in_region(region_id)
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

            # Туториал: сообщаем о событии
            self._notify_tutorial("recruit_completed", region=region_id)
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
        # Новелла полностью перекрывает игру
        if self.novel_active:
            self.novel_view.draw()
            return

        # Карта (всегда рисуется, даже под туториалом)
        self.screen.fill(BG_COLOR)
        self._draw_connections()
        self._draw_regions()
        if self.selected_region and not self.attack_mode and not self.move_mode:
            self._draw_info_panel()
        self._draw_top_bar()

        mouse_pos = pygame.mouse.get_pos()
        self.end_turn_button.update(mouse_pos)
        self.end_turn_button.enabled = (
            not self.ai_turn_active
            and not self.game.game_over
            and self._is_tutorial_allowed_action("end_turn")
        )
        self.end_turn_button.draw(self.screen)

        # Кнопки действий
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

            # Кнопка "НАНЯТЬ" — только если разрешено
            show_recruit = (is_mine and self._is_tutorial_allowed_action("recruit"))
            if show_recruit:
                self.recruit_button.rect.x = btn_x
                self.recruit_button.rect.y = btn_y
                self.recruit_button.enabled = True
                self.recruit_button.update(mouse_pos)
                self.recruit_button.draw(self.screen)
                btn_y += 55
            else:
                self.recruit_button.enabled = False

            # Кнопка "АТАКОВАТЬ" — только если разрешено
            show_attack = (army_id and not self.attack_mode and not self.move_mode
                           and self._is_tutorial_allowed_action("attack"))
            if show_attack:
                self.attack_button.rect.x = btn_x
                self.attack_button.rect.y = btn_y
                self.attack_button.enabled = True
                self.attack_button.update(mouse_pos)
                self.attack_button.draw(self.screen)
                btn_y += 55
            else:
                self.attack_button.enabled = False

            # Кнопка "ДВИГАТЬСЯ" — только если разрешено
            show_move = (army_id and not self.attack_mode and not self.move_mode
                         and self._is_tutorial_allowed_action("move"))
            if show_move:
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

        # Туториал — поверх всего (кроме game over)
        if self.tutorial_active and self.tutorial_view is not None:
            self.tutorial_view.draw()

        # Оверлей завершения обучения
        if self.tutorial_final_overlay_timer > 0:
            self._draw_tutorial_complete_overlay()

    def _draw_tutorial_complete_overlay(self) -> None:
        """Оверлей «ОБУЧЕНИЕ ЗАВЕРШЕНО»."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 30, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title = self.font_huge.render("ОБУЧЕНИЕ ЗАВЕРШЕНО", True, (100, 255, 100))
        title_rect = title.get_rect(center=(self.width // 2, self.height // 2 - 20))
        self.screen.blit(title, title_rect)

        subtitle = self.font_medium.render(
            "Теперь ты готов покорить мир. Удачи, завоеватель!",
            True, (200, 255, 200),
        )
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, self.height // 2 + 30))
        self.screen.blit(subtitle, subtitle_rect)

    def _draw_act_completed_overlay(self) -> None:
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
        else:
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
                # Туториал: выделить разрешённую цель толще
                if self.tutorial_active and self.tutorial_engine.current_allow_target == region.id:
                    pygame.draw.circle(self.screen, (255, 255, 100), (x, y), radius + 12, 3)

            if self.move_mode and self.actions.is_valid_move_target(self.moving_army_id, region.id):
                pygame.draw.circle(self.screen, (100, 180, 255), (x, y), radius + 6, 4)
                if self.tutorial_active and self.tutorial_engine.current_allow_target == region.id:
                    pygame.draw.circle(self.screen, (255, 255, 100), (x, y), radius + 12, 3)

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
        hint_rect = hint.get_rect(topright=(self.width - 20, 20))
        self.screen.blit(hint, hint_rect)

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
        if not self.ai_log:
            return

        line_height = 22
        padding = 10
        panel_w = 400
        panel_h = len(self.ai_log) * line_height + padding * 2
        panel_x = self.width - panel_w - 20
        panel_y = self.height - panel_h - 20

        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        self.screen.blit(bg, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (80, 90, 110), panel, 1)

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

        player_name = self.game.current_player().name
        log_line = f"[{player_name}] {result['text']}"
        self.ai_log.append(log_line)
        if len(self.ai_log) > 8:
            self.ai_log.pop(0)

        if self.game.game_over:
            self.ai_turn_active = False
            self.ai_plan = []
            return

        if result.get("type") == "attack" and result.get("battle"):
            self.ai_action_delay = 2200
        else:
            self.ai_action_delay = 700

    def _finish_ai_turn(self) -> None:
        self.ai_turn_active = False
        self.ai_plan = []
        self.game.end_turn()

        next_player = self.game.current_player()
        if next_player.is_ai:
            self.start_ai_turn(self.game)
        else:
            # Ход вернулся к игроку — применяем отложенный notify
            if self.tutorial_pending_notify is not None:
                event = self.tutorial_pending_notify.get("event")
                kwargs = {k: v for k, v in self.tutorial_pending_notify.items() if k != "event"}
                self.tutorial_pending_notify = None
                self._notify_tutorial(event, **kwargs)

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
            allowed = self._is_tutorial_allowed_unit(unit_type)
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

            pygame.draw.rect(self.screen, bg, item_rect, border_radius=8)

            show_highlight = (
                    self.tutorial_active
                    and self.tutorial_engine.current_allow_unit == unit_type
                    and not hovered
            )
            if show_highlight:
                pygame.draw.rect(self.screen, (255, 215, 0), item_rect, 3, border_radius=8)

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
        if self.novel_active:
            self.novel_view.update(dt)
            return

        if self.tutorial_final_overlay_timer > 0:
            self.tutorial_final_overlay_timer -= dt

        if self.battle_report:
            self.battle_report_timer -= dt
            if self.battle_report_timer <= 0:
                self.battle_report = None

        if self.act_completed_overlay_timer > 0:
            self.act_completed_overlay_timer -= dt

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

        if self.tutorial_active and self.tutorial_view is not None:
            self.tutorial_view.update(dt)

    # ============================================================
    # ОБРАБОТКА КЛИКОВ
    # ============================================================
    def handle_click(self, pos: tuple[int, int]) -> str | None:
        # Новелла — обрабатывается первой
        if self.novel_active:
            result = self.novel_view.handle_click(pos)
            self._handle_novel_result(result)
            return None

        if self.game.game_over:
            return None

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
                    if not self._is_tutorial_allowed_target(region.id):
                        return None
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
                    if not self._is_tutorial_allowed_target(region.id):
                        return None
                    if self.actions.is_valid_attack_target(self.attacker_army_id, region.id):
                        self._execute_attack(region.id)
                    return None
            self._cancel_attack()
            return None

            # Туториал — обрабатывает клики по карте и кнопкам
        if self.tutorial_active and self.tutorial_view is not None:
            result = self.tutorial_view.handle_click(pos)
            if result is not None:
                self._handle_tutorial_result(result)
                return None

            if self.tutorial_engine.current_wait_for() is not None:
                return self._handle_tutorial_map_click(pos)

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

    def _handle_tutorial_map_click(self, pos: tuple[int, int]) -> str | None:
        """Обработка кликов по карте в туториале (когда ждём события)."""
        if self.recruit_button.enabled and self.recruit_button.is_clicked(pos):
            if self._is_tutorial_allowed_action("recruit"):
                self._open_recruit()
            return None

        if self.attack_button.enabled and self.attack_button.is_clicked(pos):
            if self._is_tutorial_allowed_action("attack"):
                self._start_attack_mode()
            return None

        if self.move_button.enabled and self.move_button.is_clicked(pos):
            if self._is_tutorial_allowed_action("move"):
                self._start_move_mode()
            return None

        if self.end_turn_button.is_clicked(pos):
            if self._is_tutorial_allowed_action("end_turn"):
                return "end_turn"
            return None

        for region in self.game.regions.values():
            x, y = self._screen_pos(region)
            dx = pos[0] - x
            dy = pos[1] - y
            if dx * dx + dy * dy <= 24 * 24:
                if self._is_tutorial_allowed_region(region.id):
                    self.selected_region = region.id
                return None

        self.selected_region = None
        return None

    def _skip_novel(self) -> None:
        """Проматывает новеллу до конца (до choices или до финала)."""
        # Проматываем строки, пока можно. Если упираемся в выборы — останавливаемся.
        while True:
            if self.novel_engine.is_finished:
                self._end_novel()
                return
            if self.novel_engine.is_on_last_line() and self.novel_engine.has_choices():
                # Дошли до выборов — скип невозможен, пусть игрок выберет.
                return
            result = self.novel_engine.next_line()
            if result == "final":
                self._end_novel()
                return
            if result == "next_scene":
                # Переход к следующей сцене — продолжаем проматывать.
                continue
            if result == "choices":
                # Строки кончились, есть выборы — останавливаемся.
                return

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
                if not self._is_tutorial_allowed_unit(unit_type):
                    return None
                if me.gold >= stats['cost']:
                    self._execute_recruit(unit_type)
                return None

        panel = pygame.Rect(x, y, w, h)
        if not panel.collidepoint(pos):
            self._close_recruit()
        return None

    def handle_key(self, key: int) -> None:
        if self.novel_active:
            if key == pygame.K_ESCAPE:
                self._skip_novel()
                return
            result = self.novel_view.handle_key(key)
            self._handle_novel_result(result)
            return

        # Туториал: ESC игнорируется, пробел/enter — "Далее"
        if self.tutorial_active and self.tutorial_view is not None:
            if key == pygame.K_ESCAPE:
                return 'pause'
            result = self.tutorial_view.handle_key(key)
            self._handle_tutorial_result(result)
            return

        if key == pygame.K_ESCAPE:
            if self.attack_mode:
                self._cancel_attack()
            elif self.move_mode:
                self._cancel_move()
            elif self.recruit_mode:
                self._close_recruit()