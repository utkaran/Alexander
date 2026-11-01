"""Базовый экран диалога: портрет, окно с текстом, кнопка «Далее».

Общий предок NovelView и TutorialView. Содержит только то, что
действительно дублировалось. Специфика (фон, выборы, переходы,
подсветка) остаётся в наследниках.
"""

from pathlib import Path

import pygame

from core.paths import resource_path
from story.characters import get_name, get_color, get_flip


PORTRAITS_DIR = resource_path("assets/portraits")


class DialogueView:
    # Цвета и размеры — переопределяются в наследниках при необходимости
    BOX_BG = (25, 30, 45)
    BOX_BG_ALPHA = 180
    BOX_BORDER = (80, 90, 120)
    BOX_BORDER_ALPHA = 200

    PORTRAIT_SIZE = 120
    PORTRAIT_MARGIN = 15
    PORTRAIT_BG = (40, 45, 65)

    TEXT_COLOR = (240, 240, 240)
    NARRATOR_COLOR = (180, 180, 200)

    NEXT_BG = (40, 55, 80)
    NEXT_HOVER = (60, 85, 120)
    NEXT_BORDER = (100, 120, 160)

    def __init__(self, screen: pygame.Surface, engine) -> None:
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

        # Кнопка «Далее»
        self.next_button_rect = pygame.Rect(
            self.box_x + self.box_w - 160,
            self.box_y + self.box_height - 60,
            140,
            44,
        )

        # Кэш портретов
        self.portraits: dict[str, pygame.Surface | None] = {}

    # ============================================================
    # ЗАГРУЗКА
    # ============================================================
    def _load_portrait(self, who: str) -> pygame.Surface | None:
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
    def _draw_dialogue_box(self) -> None:
        bg_surface = pygame.Surface(
            (self.box_w, self.box_height), pygame.SRCALPHA,
        )
        bg_surface.fill((*self.BOX_BG, self.BOX_BG_ALPHA))
        self.screen.blit(bg_surface, (self.box_x, self.box_y))

        border_surface = pygame.Surface(
            (self.box_w, self.box_height), pygame.SRCALPHA,
        )
        pygame.draw.rect(
            border_surface,
            (*self.BOX_BORDER, self.BOX_BORDER_ALPHA),
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

        has_portrait = (who != "narrator")
        text_x_offset = (
            self.PORTRAIT_SIZE + self.PORTRAIT_MARGIN * 2
            if has_portrait else 30
        )

        y = self.box_y + 25

        if who != "narrator":
            name = get_name(who)
            color = get_color(who)
            name_surf = self.font_large.render(name, True, color)
            self.screen.blit(name_surf, (self.box_x + text_x_offset, y))
            y += 45

        text_color = self.NARRATOR_COLOR if who == "narrator" else self.TEXT_COLOR
        self._draw_wrapped_text(
            text,
            self.font_medium,
            text_color,
            self.box_x + text_x_offset,
            y,
            self.box_w - text_x_offset - 30,
        )

    def _draw_wrapped_text(self, text, font, color, x, y, max_width) -> None:
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
        image = self._load_portrait(who)

        if image is not None:
            if get_flip(who):
                image = pygame.transform.flip(image, True, False)

            img_w, img_h = image.get_size()
            scale = max(self.PORTRAIT_SIZE / img_w, self.PORTRAIT_SIZE / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            scaled = pygame.transform.smoothscale(image, (new_w, new_h))

            crop_x = (new_w - self.PORTRAIT_SIZE) // 2
            crop_y = (new_h - self.PORTRAIT_SIZE) // 2

            portrait_surf = pygame.Surface(
                (self.PORTRAIT_SIZE, self.PORTRAIT_SIZE), pygame.SRCALPHA,
            )
            portrait_surf.blit(scaled, (-crop_x, -crop_y))
            self.screen.blit(portrait_surf, (x, y))

            pygame.draw.rect(
                self.screen, get_color(who),
                pygame.Rect(x, y, self.PORTRAIT_SIZE, self.PORTRAIT_SIZE),
                3, border_radius=8,
            )
        else:
            color = get_color(who)
            name = get_name(who)
            letter = name[0] if name else "?"

            rect = pygame.Rect(x, y, self.PORTRAIT_SIZE, self.PORTRAIT_SIZE)
            pygame.draw.rect(self.screen, self.PORTRAIT_BG, rect, border_radius=8)
            pygame.draw.rect(self.screen, color, rect, 3, border_radius=8)

            letter_surf = self.font_huge.render(letter, True, color)
            letter_rect = letter_surf.get_rect(center=rect.center)
            self.screen.blit(letter_surf, letter_rect)

    def _draw_next_button(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.next_button_rect.collidepoint(mouse_pos)

        color = self.NEXT_HOVER if hovered else self.NEXT_BG
        pygame.draw.rect(self.screen, color, self.next_button_rect, border_radius=8)
        pygame.draw.rect(
            self.screen, self.NEXT_BORDER, self.next_button_rect, 2, border_radius=8,
        )

        label = self.font_medium.render("Далее ▶", True, self.TEXT_COLOR)
        label_rect = label.get_rect(center=self.next_button_rect.center)
        self.screen.blit(label, label_rect)