"""Экран новеллы: фон сцены, портрет, диалоговое окно, выборы."""

from pathlib import Path

import pygame

from core.paths import resource_path
from story.engine import NovelEngine
from story.characters import get_name, get_color
from core.log import get_logger
log = get_logger(__name__)

from ui.dialogue import DialogueView


# ============================================================
# ЦВЕТА И КОНСТАНТЫ
# ============================================================
BG_COLOR = (15, 18, 28)
TITLE_COLOR = (180, 180, 180)
HINT_COLOR = (120, 120, 140)

CHOICE_BG = (40, 55, 80)
CHOICE_HOVER = (60, 85, 120)
CHOICE_BORDER = (100, 120, 160)

TRANSITION_BG = (10, 12, 20)
TRANSITION_TITLE = (220, 220, 220)
TRANSITION_LINE = (80, 90, 110)
TRANSITION_HINT = (100, 100, 120)
TRANSITION_DURATION = 1500  # мс

BACKGROUNDS_DIR = resource_path("assets/backgrounds")

BACKGROUND_OVERLAY_ALPHA = 80


class NovelView(DialogueView):
    def __init__(self, screen: pygame.Surface, engine: NovelEngine) -> None:
        super().__init__(screen, engine)

        # Кэш фонов: scene_id → Surface или None
        self.backgrounds: dict[str, pygame.Surface | None] = {}

        # Кнопки выборов
        self.choice_rects: list[pygame.Rect] = []

        # Переход между сценами
        self.transition_active = False
        self.transition_timer = 0
        self.transition_title = ""

    # ============================================================
    # ОБНОВЛЕНИЕ
    # ============================================================
    def update(self, dt: int) -> None:
        if self.transition_active:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                self.transition_active = False
                self.transition_timer = 0

    def start_transition(self, title: str) -> None:
        self.transition_active = True
        self.transition_timer = TRANSITION_DURATION
        self.transition_title = title

    # ============================================================
    # ЗАГРУЗКА АССЕТОВ
    # ============================================================
    def _load_background(self, bg_id: str) -> pygame.Surface | None:
        """Загружает фон по id. Кэширует. None — если файла нет."""
        if bg_id in self.backgrounds:
            return self.backgrounds[bg_id]

        for ext in (".jpg", ".jpeg", ".png"):
            path = BACKGROUNDS_DIR / f"{bg_id}{ext}"
            if path.exists():
                try:
                    image = pygame.image.load(str(path)).convert()
                    self.backgrounds[bg_id] = image
                    return image
                except pygame.error as e:
                    log.exception("Не удалось загрузить фон %s", path)
                    self.backgrounds[bg_id] = None
                    return None

        self.backgrounds[bg_id] = None
        return None

    # ============================================================
    # ОТРИСОВКА
    # ============================================================
    def draw(self) -> None:
        if self.transition_active:
            self._draw_transition()
            return

        scene = self.engine.current_scene()
        if scene is None:
            self.screen.fill(BG_COLOR)
            return

        # Фон сцены
        bg_id = scene.get("background")
        self._draw_background(bg_id)

        # Заголовок сцены
        title = scene.get("title", "")
        if title:
            title_surf = self.font_medium.render(title, True, TITLE_COLOR)
            title_rect = title_surf.get_rect(center=(self.width // 2, 50))
            self.screen.blit(title_surf, title_rect)

        # Диалоговое окно (из DialogueView)
        self._draw_dialogue_box()

        # Портрет — слева в диалоговом окне (из DialogueView)
        line = self.engine.current_line()
        who = line.get("who", "narrator") if line else "narrator"
        if who != "narrator":
            portrait_x = self.box_x + self.PORTRAIT_MARGIN
            portrait_y = self.box_y + (self.box_height - self.PORTRAIT_SIZE) // 2
            self._draw_portrait(who, portrait_x, portrait_y)

        # Выборы или кнопка «Далее»
        if self.engine.is_on_last_line() and self.engine.has_choices():
            self._draw_choices()
        elif not self.engine.is_on_last_line():
            self._draw_next_button()

        # Подсказка
        hint = self.font_small.render(
            "ПРОБЕЛ / ENTER / ЛКМ — далее   |   ESC — пропустить",
            True, HINT_COLOR,
        )
        hint_rect = hint.get_rect(center=(self.width // 2, self.height - 20))
        self.screen.blit(hint, hint_rect)

    def _draw_background(self, bg_id: str | None) -> None:
        """Рисует фон сцены. Если bg_id None или файл не найден — заливает BG_COLOR."""
        if bg_id is None:
            self.screen.fill(BG_COLOR)
            return

        image = self._load_background(bg_id)
        if image is None:
            self.screen.fill(BG_COLOR)
            return

        img_w, img_h = image.get_size()
        screen_w, screen_h = self.width, self.height

        # Scale to cover
        scale = max(screen_w / img_w, screen_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)

        scaled = pygame.transform.smoothscale(image, (new_w, new_h))

        offset_x = (new_w - screen_w) // 2
        offset_y = (new_h - screen_h) // 2

        self.screen.blit(scaled, (-offset_x, -offset_y))

        # Затемнение поверх
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, BACKGROUND_OVERLAY_ALPHA))
        self.screen.blit(overlay, (0, 0))

    def _draw_transition(self) -> None:
        """Титульная карточка между сценами."""
        self.screen.fill(TRANSITION_BG)

        title_surf = self.font_huge.render(
            self.transition_title, True, TRANSITION_TITLE,
        )
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(title_surf, title_rect)

        line_y = self.height // 2 + 50
        line_w = min(600, self.width // 2)
        pygame.draw.line(
            self.screen, TRANSITION_LINE,
            (self.width // 2 - line_w // 2, line_y),
            (self.width // 2 + line_w // 2, line_y),
            2,
        )

        hint = self.font_small.render(
            "ПРОБЕЛ / ЛКМ — пропустить",
            True, TRANSITION_HINT,
        )
        hint_rect = hint.get_rect(center=(self.width // 2, self.height - 60))
        self.screen.blit(hint, hint_rect)

    def _draw_choices(self) -> None:
        """Кнопки выборов над диалоговым окном."""
        scene = self.engine.current_scene()
        if scene is None:
            return
        choices = scene.get("choices", [])
        if not choices:
            return

        mouse_pos = pygame.mouse.get_pos()

        btn_w = 600
        btn_h = 50
        spacing = 12
        total_h = len(choices) * btn_h + (len(choices) - 1) * spacing

        start_y = self.box_y - total_h - 30
        start_x = (self.width - btn_w) // 2

        self.choice_rects = []
        for i, choice in enumerate(choices):
            rect = pygame.Rect(
                start_x, start_y + i * (btn_h + spacing), btn_w, btn_h,
            )
            self.choice_rects.append(rect)

            hovered = rect.collidepoint(mouse_pos)
            color = CHOICE_HOVER if hovered else CHOICE_BG
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, CHOICE_BORDER, rect, 2, border_radius=8)

            text = choice.get("text", "")
            label = self.font_medium.render(text, True, self.TEXT_COLOR)
            label_rect = label.get_rect(center=rect.center)
            self.screen.blit(label, label_rect)

    # ============================================================
    # ВВОД
    # ============================================================
    def handle_click(self, pos: tuple[int, int]) -> dict | None:
        if self.transition_active:
            self.transition_active = False
            self.transition_timer = 0
            return None

        if self.engine.is_on_last_line() and self.engine.has_choices():
            for i, rect in enumerate(self.choice_rects):
                if rect.collidepoint(pos):
                    result = self.engine.choose(i)
                    return {
                        "action": "choice",
                        "index": i,
                        "effects": result.get("effects", {}),
                        "goto": result.get("goto"),
                    }
            return None

        result = self.engine.next_line()
        return {"action": "next", "result": result}

    def handle_key(self, key: int) -> dict | None:
        if self.transition_active:
            if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                self.transition_active = False
                self.transition_timer = 0
            return None

        if key == pygame.K_SPACE or key == pygame.K_RETURN:
            if self.engine.is_on_last_line() and self.engine.has_choices():
                return None
            result = self.engine.next_line()
            return {"action": "next", "result": result}
        return None