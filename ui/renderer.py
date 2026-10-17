"""Отрисовка игрового мира на Pygame."""

import pygame

from core.game import GameState
from core.constants import UNIT_STATS
from ui.actions import ActionController
from ui.widgets import Button
from ui.novel_view import NovelView
from ui.tutorial_view import TutorialView
from story.engine import NovelEngine
from ui.geometry import compute_scale, screen_pos
from ui.modes import AttackMode, MoveMode, RecruitMode
from ui.map_view import draw_connections, draw_regions, draw_forced_objective_highlight
from ui.hud import draw_info_panel, draw_ai_log, draw_top_bar
from ui.overlays import (
    draw_battle_report,
    draw_recruit_window,
    draw_game_over_overlay,
    draw_act_completed_overlay,
    draw_tutorial_complete_overlay
)


BG_COLOR = (20, 25, 35)
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

        self.attack = AttackMode()
        self.move = MoveMode()
        self.recruit = RecruitMode()

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

        # Сюжетные сцены Акта I
        self.story_scene_active = False
        self.story_scene_id: str | None = None

        # Туториал
        self.tutorial_active = False
        self.tutorial_engine = NovelEngine()
        self.tutorial_view: TutorialView | None = None
        self.tutorial_final_overlay_timer = 0

        self.tutorial_pending_notify: dict | None = None  # отложенное событие
        self._pending_thebes_revolt = False

    def set_game(self, game: GameState) -> None:
        self.game = game
        self.actions = ActionController(game)
        self.scale_x, self.scale_y = self._compute_scale()
        self.reset_state()

    def reset_state(self) -> None:
        """Сбрасывает UI-состояние при смене хода."""
        self.selected_region = None
        self.attack.cancel()
        self.move.cancel()
        self.recruit.cancel()
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
        return compute_scale(self.game, self.width, self.height)

    def _screen_pos(self, region) -> tuple[int, int]:
        return screen_pos(self.game, region, self.scale_x, self.scale_y)

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

    def start_story_scene(self, scene_id: str) -> None:
        """Запускает сюжетную сцену из act1.json."""
        self.novel_engine = NovelEngine()
        self.novel_engine.load_scenes('story/scenes/act1.json')
        self.novel_engine.start(scene_id)
        self.novel_view = NovelView(self.screen, self.novel_engine)
        self.novel_active = True
        self.story_scene_active = True
        self.story_scene_id = scene_id
        self.novel_on_finish_callback = self._on_story_scene_finished

    def _on_story_scene_finished(self) -> None:
        finished_scene = self.story_scene_id
        self.story_scene_active = False
        self.story_scene_id = None

        if finished_scene == 'act1_thebes_burn':
            self.game.forced_objective = None
            return

        # Если закончилась сцена Геллеспонта — открываем карту Акта II
        if finished_scene == 'act1_hellespont':
            self.game.load_map_additive('data/map_act2.json')
            self.game.current_act = 2
            self.scale_x, self.scale_y = self._compute_scale()
            self.selected_region = None
            self.game.unlock_scenario('granicus')
            return

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
        self._pending_thebes_revolt = True

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

                if self.recruit.is_active() or self.attack.is_active() or self.move.is_active():
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
        self.sync_tutorial_position()

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
        self.sync_tutorial_position()

        if self.tutorial_engine.is_finished:
            self._end_tutorial()
            return

        if self.game.tutorial_active:
            for army in self.game.armies.values():
                if army.owner == self.game.current_player_id:
                    army.has_acted = False

    def sync_tutorial_position(self) -> None:
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

    def _execute_attack(self, target_region_id: str) -> None:
        result = self.actions.execute_attack(self.attack.army_id, target_region_id)
        self.battle_report = result
        self.battle_report_timer = 3000
        self.attack.cancel()
        self.selected_region = target_region_id

        # Туториал: сообщаем о событии
        if result.get("ok") and result.get("winner") == "attacker":
            self._notify_tutorial("attack_completed", region=target_region_id)

    def _execute_move(self, target_region_id: str) -> None:
        result = self.actions.execute_move(self.move.army_id, target_region_id)
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

        self.move.cancel()
        self.selected_region = target_region_id

    def _open_recruit(self) -> None:
        if not self.selected_region:
            return
        if not self.actions.can_recruit_in(self.selected_region):
            return
        self.recruit.start(self.selected_region)

    def _execute_recruit(self, unit_type: str) -> None:
        if not self.recruit.is_active() or not self.recruit.region_id:
            return

        region_id = self.recruit.region_id
        strength_before = self.actions.get_army_strength_in_region(region_id)
        result = self.actions.execute_recruit(region_id, unit_type, 1)

        if result["ok"]:
            region_name = self.game.regions[region_id].name
            strength_after = self.actions.get_army_strength_in_region(region_id)
            delta = strength_after - strength_before

            self.recruit.cancel()
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
        if self.selected_region and not self.attack.is_active() and not self.move.is_active():
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
                and not self.recruit.is_active()
                and not self.attack.is_active()
                and not self.move.is_active()):
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

            army = self.game.armies.get(army_id) if army_id else None
            already_acted = army is not None and army.has_acted

            # Кнопка "АТАКОВАТЬ" — только если разрешено
            show_attack = (army_id and not already_acted and not self.attack.is_active() and not self.move.is_active()
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
            show_move = (army_id and not already_acted and not self.attack.is_active() and not self.move.is_active()
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

        if self.attack.is_active():
            text = self.font_medium.render(
                "Выберите цель атаки (клик по красному региону). ESC — отмена",
                True, TARGET_COLOR
            )
            text_rect = text.get_rect(center=(self.width // 2, 70))
            self.screen.blit(text, text_rect)

        if self.move.is_active():
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

        if self.recruit.is_active():
            self._draw_recruit_window()

        if self.act_completed_overlay_timer > 0 and not self.game.game_over:
            self._draw_act_completed_overlay()

        if self.game.game_over:
            self._draw_game_over_overlay()

        if self.ai_log and self.ai_turn_active:
            self._draw_ai_log()

        if self.game.forced_objective == 'thebes':
            self._draw_forced_objective_highlight()

        # Туториал — поверх всего (кроме game over)
        if self.tutorial_active and self.tutorial_view is not None:
            self.tutorial_view.draw()

        # Оверлей завершения обучения
        if self.tutorial_final_overlay_timer > 0:
            self._draw_tutorial_complete_overlay()

    def _draw_connections(self) -> None:
        draw_connections(self.screen, self.game, self.scale_x, self.scale_y)
    def _draw_forced_objective_highlight(self) -> None:
        draw_forced_objective_highlight(self.screen, self.game, self.scale_x, self.scale_y)

    def _draw_tutorial_complete_overlay(self) -> None:
        draw_tutorial_complete_overlay(self.screen, self.width, self.height, self)

    def _draw_act_completed_overlay(self) -> None:
        draw_act_completed_overlay(self.screen, self.width, self.height, self)

    def _draw_game_over_overlay(self) -> None:
        draw_game_over_overlay(self.screen, self.game, self.width, self.height, self)

    def _draw_regions(self) -> None:
        draw_regions(self.screen, self.game, self, self.scale_x, self.scale_y)

    def _draw_top_bar(self) -> None:
        draw_top_bar(self.screen, self.game, self)

    def _draw_info_panel(self) -> None:
        draw_info_panel(self.screen, self.game, self)

    def _draw_ai_log(self) -> None:
        draw_ai_log(self.screen, self.ai_log, self.width, self.height, self.font_small)

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
        base_h += (self.font_large.get_height() + 4) * 2
        base_h += (self.font_medium.get_height() + 6) * 4

        for army in self.game.armies.values():
            if army.location == region.id and not army.is_empty():
                base_h += 12
                base_h += self.font_medium.get_height() + 6
                base_h += (self.font_small.get_height() + 4) * 2  # Атака + Защита
                base_h += len(army.units) * (self.font_small.get_height() + 4)
                if army.alexander_attached:
                    base_h += self.font_small.get_height() + 9
                break

        base_h += 15
        return base_h

    def _draw_recruit_window(self) -> None:
        draw_recruit_window(self.screen, self.game, self)

    def _draw_battle_report(self) -> None:
        draw_battle_report(self.screen, self.battle_report, self.width, self.height, self)

    def update(self, dt: int) -> None:
        if (not self.novel_active
                and not self.tutorial_active
                and not self.ai_turn_active
                and not self.battle_report
                and self.game.has_pending_scene()):
            scene_id = self.game.pop_scene()
            if scene_id is not None:
                self.start_story_scene(scene_id)
                return
        if self.novel_active:
            self.novel_view.update(dt)
            return

        if self.tutorial_final_overlay_timer > 0:
            self.tutorial_final_overlay_timer -= dt
            if self.tutorial_final_overlay_timer <= 0 and self._pending_thebes_revolt:
                self._pending_thebes_revolt = False
                self.game.spawn_thebes_revolt()

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

        if self.recruit.is_active():
            return self._handle_recruit_click(pos)

        if self.battle_report:
            self.battle_report = None
            return None

        if self.move.is_active():
            for region in self.game.regions.values():
                x, y = self._screen_pos(region)
                dx = pos[0] - x
                dy = pos[1] - y
                if dx * dx + dy * dy <= 24 * 24:
                    if not self._is_tutorial_allowed_target(region.id):
                        return None
                    if self.actions.is_valid_move_target(self.move.army_id, region.id):
                        self._execute_move(region.id)
                    return None
            self.move.cancel()
            return None

        if self.attack.is_active():
            for region in self.game.regions.values():
                x, y = self._screen_pos(region)
                dx = pos[0] - x
                dy = pos[1] - y
                if dx * dx + dy * dy <= 24 * 24:
                    if not self._is_tutorial_allowed_target(region.id):
                        return None
                    if (self.game.forced_objective is not None
                            and region.id != self.game.forced_objective):
                        return None
                    if self.actions.is_valid_attack_target(self.attack.army_id, region.id):
                        self._execute_attack(region.id)
                    return None
            self.attack.cancel()
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
            army_id = self.actions.get_army_in_region(self.selected_region)
            if army_id:
                self.attack.start(army_id)
            return None

        if self.move_button.enabled and self.move_button.is_clicked(pos):
            army_id = self.actions.get_army_in_region(self.selected_region)
            if army_id:
                self.move.start(army_id)
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
                army_id = self.actions.get_army_in_region(self.selected_region)
                if army_id:
                    self.attack.start(army_id)
            return None

        if self.move_button.enabled and self.move_button.is_clicked(pos):
            if self._is_tutorial_allowed_action("move"):
                army_id = self.actions.get_army_in_region(self.selected_region)
                if army_id:
                    self.move.start(army_id)
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
            self.recruit.cancel()
        return None

    def handle_key(self, key: int) -> None:
        if self.novel_active:
            if key == pygame.K_ESCAPE:
                self._skip_novel()
                return None
            result = self.novel_view.handle_key(key)
            self._handle_novel_result(result)
            return None

        if self.tutorial_active and self.tutorial_view is not None:
            if key == pygame.K_ESCAPE:
                return 'pause'
            result = self.tutorial_view.handle_key(key)
            self._handle_tutorial_result(result)
            return None

        if key == pygame.K_ESCAPE:
            if self.attack.is_active():
                self.attack.cancel()
                return None
            elif self.move.is_active():
                self.move.cancel()
                return None
            elif self.recruit.is_active():
                self.recruit.cancel()
                return None
            return 'pause'
        return None