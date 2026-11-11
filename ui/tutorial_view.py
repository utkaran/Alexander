"""Экран туториала: рисуется поверх карты, ведёт игрока за руку."""

import pygame

from story.engine import NovelEngine

from ui.dialogue import DialogueView


# Цвета, уникальные для туториала
OVERLAY_COLOR = (0, 0, 0, 120)             # затемнение карты
HINT_COLOR = (120, 120, 140)

# Подсветка
HIGHLIGHT_GOLD = (255, 215, 0)
HIGHLIGHT_CAPITAL = (255, 240, 120)
HIGHLIGHT_ENEMY = (255, 80, 80)
HIGHLIGHT_PULSE_SPEED = 5.0      # скорость пульсации (рад/сек)
HIGHLIGHT_THICKNESS = 4
HIGHLIGHT_PADDING = 8


class TutorialView(DialogueView):
    # Переопределяем прозрачность окна — в туториале оно плотнее
    BOX_BG_ALPHA = 200
    BOX_BORDER_ALPHA = 220

    def __init__(self, screen: pygame.Surface, engine: NovelEngine, audio=None) -> None:
        super().__init__(screen, engine)

        self.audio = audio
        # Время для пульсации
        self.time = 0.0

        # Callback на отрисовку подсветки — его установит Renderer.
        # Получает (highlight_list, pulse_alpha)
        self.highlight_drawer = None

    def update(self, dt: int) -> None:
        self.time += dt / 1000.0

    # ============================================================
    # ОТРИСОВКА
    # ============================================================
    def draw(self) -> None:
        # 1. Затемнение карты
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

        # 2. Подсветка (через callback из Renderer)
        if self.highlight_drawer is not None:
            line = self.engine.current_line()
            highlight = line.get("highlight") if line else None
            if highlight:
                pulse = self._compute_pulse()
                self.highlight_drawer(highlight, pulse)

        # 3. Диалоговое окно (из DialogueView)
        self._draw_dialogue_box()

        # 4. Портрет (из DialogueView)
        line = self.engine.current_line()
        who = line.get("who", "narrator") if line else "narrator"
        if who != "narrator":
            portrait_x = self.box_x + self.PORTRAIT_MARGIN
            portrait_y = self.box_y + (self.box_height - self.PORTRAIT_SIZE) // 2
            self._draw_portrait(who, portrait_x, portrait_y)

        # 5. Кнопка «Далее» — только если не ждём события
        if self.engine.current_wait_for() is None:
            self._draw_next_button()

    def _compute_pulse(self) -> float:
        """Возвращает 0.0…1.0 — коэффициент пульсации."""
        import math
        return 0.5 + 0.5 * math.sin(self.time * HIGHLIGHT_PULSE_SPEED)

    # ============================================================
    # ВВОД
    # ============================================================
    def handle_click(self, pos: tuple[int, int]) -> dict | None:
        # Если ждём события — клики по экрану игнорируем
        if self.engine.current_wait_for() is not None:
            return None

        # Клик по кнопке «Далее»
        if self.next_button_rect.collidepoint(pos):
            result = self.engine.next_line()
            return {"action": "next", "result": result}

        return None

    def handle_key(self, key: int) -> dict | None:
        if self.engine.current_wait_for() is not None:
            return None

        if key in (pygame.K_SPACE, pygame.K_RETURN):
            result = self.engine.next_line()
            return {"action": "next", "result": result}

        return None


# ============================================================
# ФУНКЦИЯ ПОДСВЕТКИ (используется Renderer)
# ============================================================
# ... draw_highlight, _draw_region_highlight, _draw_button_highlight
# остаются как были — они не относятся к диалоговому окну.