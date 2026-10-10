"""Экран новеллы: фон сцены, портрет, диалоговое окно, выборы."""

from pathlib import Path
from core.paths import resource_path

import pygame

from story.engine import NovelEngine
from story.characters import get_name, get_color, get_flip


# ============================================================
# ЦВЕТА И КОНСТАНТЫ
# ============================================================
BG_COLOR = (15, 18, 28)
TITLE_COLOR = (180, 180, 180)
TEXT_COLOR = (240, 240, 240)
NARRATOR_COLOR = (180, 180, 200)
HINT_COLOR = (120, 120, 140)

# Диалоговое окно
BOX_BG = (25, 30, 45)
BOX_BG_ALPHA = 180
BOX_BORDER = (80, 90, 120)
BOX_BORDER_ALPHA = 200

# Портрет
PORTRAIT_BG = (40, 45, 65)

# Выборы
CHOICE_BG = (40, 55, 80)
CHOICE_HOVER = (60, 85, 120)
CHOICE_BORDER = (100, 120, 160)

# Переход между сценами
TRANSITION_BG = (10, 12, 20)
TRANSITION_TITLE = (220, 220, 220)
TRANSITION_LINE = (80, 90, 110)
TRANSITION_HINT = (100, 100, 120)
TRANSITION_DURATION = 1500  # мс

# Пути к ассетам

BACKGROUNDS_DIR = resource_path("assets/backgrounds")
PORTRAITS_DIR = resource_path("assets/portraits")

# Затемнение поверх фона
BACKGROUND_OVERLAY_ALPHA = 80

# Размер портрета в диалоговом окне
PORTRAIT_SIZE = 120
PORTRAIT_MARGIN = 15


class NovelView:
    def __init__(self, screen: pygame.Surface, engine: NovelEngine) -> None:
        self.screen = screen
        self.engine = engine
        self.width, self.height = screen.get_size()

        self.font_small = pygame.font.SysFont("arial", 16)
        self.font_medium = pygame.font.SysFont("arial", 22)
        self.font_large = pygame.font.SysFont("arial", 28, bold=True)
        self.font_huge = pygame.font.SysFont("arial", 36, bold=True)

        # Диалоговое окно
        self.box_margin = 60
        self.box_height = 220
        self.box_x = self.box_margin
        self.box_y = self.height - self.box_height - self.box_margin
        self.box_w = self.width - self.box_margin * 2

        # Кнопка "Далее"
        self.next_button_rect = pygame.Rect(
            self.box_x + self.box_w - 160,
            self.box_y + self.box_height - 60,
            140,
            44,
        )

        # Кнопки выборов
        self.choice_rects: list[pygame.Rect] = []

        # Кэш фонов: scene_id → Surface или None
        self.backgrounds: dict[str, pygame.Surface | None] = {}

        # Кэш портретов: who → Surface или None
        self.portraits: dict[str, pygame.Surface | None] = {}

        # Переход между сценами
        self.transition_active = False
        self.transition_timer = 0
        self.transition_title = ""

    # ============================================================
    # ОБНОВЛЕНИЕ
    # ============================================================
    def update(self, dt: int) -> None:
        """Обновляет таймеры."""
        if self.transition_active:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                self.transition_active = False
                self.transition_timer = 0

    def start_transition(self, title: str) -> None:
        """Запускает карточку перехода к новой сцене."""
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
                    print(f"Не удалось загрузить фон {path}: {e}")
                    self.backgrounds[bg_id] = None
                    return None

        self.backgrounds[bg_id] = None
        return None

    def _load_portrait(self, who: str) -> pygame.Surface | None:
        """Загружает портрет персонажа. Кэширует. None — если файла нет."""
        if who in self.portraits:
            return self.portraits[who]

        for ext in (".png", ".jpg", ".jpeg"):
            path = PORTRAITS_DIR / f"{who}{ext}"
            if path.exists():
                try:
                    image = pygame.image.load(str(path)).convert_alpha()
                    self.portraits[who] = image
                    return image
                except pygame.error as e:
                    print(f"Не удалось загрузить портрет {path}: {e}")
                    self.portraits[who] = None
                    return None

        self.portraits[who] = None
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

        # Диалоговое окно
        self._draw_dialogue_box()

        # Портрет — слева в диалоговом окне
        line = self.engine.current_line()
        who = line.get("who", "narrator") if line else "narrator"
        if who != "narrator":
            portrait_x = self.box_x + PORTRAIT_MARGIN
            portrait_y = self.box_y + (self.box_height - PORTRAIT_SIZE) // 2
            self._draw_portrait(who, portrait_x, portrait_y)

        # Выборы или кнопка "Далее"
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

        title_surf = self.font_huge.render(self.transition_title, True, TRANSITION_TITLE)
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

    def _draw_dialogue_box(self) -> None:
        """Диалоговое окно с именем и текстом. Полупрозрачное."""
        box_rect = pygame.Rect(
            self.box_x, self.box_y,
            self.box_w, self.box_height,
        )

        # Полупрозрачный фон
        bg_surface = pygame.Surface((self.box_w, self.box_height), pygame.SRCALPHA)
        bg_surface.fill((*BOX_BG, BOX_BG_ALPHA))
        self.screen.blit(bg_surface, (self.box_x, self.box_y))

        # Полупрозрачная рамка
        border_surface = pygame.Surface((self.box_w, self.box_height), pygame.SRCALPHA)
        pygame.draw.rect(
            border_surface,
            (*BOX_BORDER, BOX_BORDER_ALPHA),
            pygame.Rect(0, 0, self.box_w, self.box_height),
            2,
            border_radius=12,
        )
        self.screen.blit(border_surface, (self.box_x, self.box_y))

        line = self.engine.current_line()
        if line is None:
            return

        who = line.get("who", "narrator")
        text = line.get("text", "")

        # Если есть портрет — текст сдвигается вправо
        has_portrait = (who != "narrator")
        text_x_offset = PORTRAIT_SIZE + PORTRAIT_MARGIN * 2 if has_portrait else 30

        y = self.box_y + 25

        if who != "narrator":
            name = get_name(who)
            color = get_color(who)
            name_surf = self.font_large.render(name, True, color)
            self.screen.blit(name_surf, (self.box_x + text_x_offset, y))
            y += 45

        text_color = NARRATOR_COLOR if who == "narrator" else TEXT_COLOR
        self._draw_wrapped_text(
            text,
            self.font_medium,
            text_color,
            self.box_x + text_x_offset,
            y,
            self.box_w - text_x_offset - 30,
        )

    def _draw_wrapped_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        x: int, y: int, max_width: int,
    ) -> None:
        """Рисует текст с переносом по словам."""
        words = text.split(" ")
        line_words: list[str] = []
        current_y = y

        for word in words:
            test_line = " ".join(line_words + [word])
            if font.size(test_line)[0] <= max_width:
                line_words.append(word)
            else:
                if line_words:
                    line_surf = font.render(" ".join(line_words), True, color)
                    self.screen.blit(line_surf, (x, current_y))
                    current_y += font.get_height() + 4
                line_words = [word]

        if line_words:
            line_surf = font.render(" ".join(line_words), True, color)
            self.screen.blit(line_surf, (x, current_y))

    def _draw_portrait(self, who: str, x: int, y: int) -> None:
        """Рисует портрет персонажа в квадрате PORTRAIT_SIZE×PORTRAIT_SIZE.

        Если картинки нет — fallback: квадрат с цветом персонажа и буквой.
        """
        image = self._load_portrait(who)

        if image is not None:
            # Отражаем по горизонтали, если надо
            if get_flip(who):
                image = pygame.transform.flip(image, True, False)

            # Масштабируем под нужный размер, сохраняя пропорции
            img_w, img_h = image.get_size()
            scale = max(PORTRAIT_SIZE / img_w, PORTRAIT_SIZE / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            scaled = pygame.transform.smoothscale(image, (new_w, new_h))

            # Обрезаем до квадрата PORTRAIT_SIZE
            crop_x = (new_w - PORTRAIT_SIZE) // 2
            crop_y = (new_h - PORTRAIT_SIZE) // 2

            portrait_surf = pygame.Surface((PORTRAIT_SIZE, PORTRAIT_SIZE), pygame.SRCALPHA)
            portrait_surf.blit(scaled, (-crop_x, -crop_y))

            self.screen.blit(portrait_surf, (x, y))

            # Рамка
            pygame.draw.rect(
                self.screen, get_color(who),
                pygame.Rect(x, y, PORTRAIT_SIZE, PORTRAIT_SIZE),
                3, border_radius=8,
            )
        else:
            # Fallback — квадрат с буквой
            color = get_color(who)
            name = get_name(who)
            letter = name[0] if name else "?"

            rect = pygame.Rect(x, y, PORTRAIT_SIZE, PORTRAIT_SIZE)
            pygame.draw.rect(self.screen, PORTRAIT_BG, rect, border_radius=8)
            pygame.draw.rect(self.screen, color, rect, 3, border_radius=8)

            letter_surf = self.font_huge.render(letter, True, color)
            letter_rect = letter_surf.get_rect(center=rect.center)
            self.screen.blit(letter_surf, letter_rect)

    def _draw_next_button(self) -> None:
        """Кнопка "Далее"."""
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.next_button_rect.collidepoint(mouse_pos)

        color = CHOICE_HOVER if hovered else CHOICE_BG
        pygame.draw.rect(self.screen, color, self.next_button_rect, border_radius=8)
        pygame.draw.rect(self.screen, CHOICE_BORDER, self.next_button_rect, 2, border_radius=8)

        label = self.font_medium.render("Далее ▶", True, TEXT_COLOR)
        label_rect = label.get_rect(center=self.next_button_rect.center)
        self.screen.blit(label, label_rect)

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
            rect = pygame.Rect(start_x, start_y + i * (btn_h + spacing), btn_w, btn_h)
            self.choice_rects.append(rect)

            hovered = rect.collidepoint(mouse_pos)
            color = CHOICE_HOVER if hovered else CHOICE_BG
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            pygame.draw.rect(self.screen, CHOICE_BORDER, rect, 2, border_radius=8)

            text = choice.get("text", "")
            label = self.font_medium.render(text, True, TEXT_COLOR)
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