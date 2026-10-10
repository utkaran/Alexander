"""Главное меню игры: Новая игра / Загрузить / Выход."""

from pathlib import Path
from core.paths import save_dir

import pygame


BG_TOP = (15, 20, 35)
BG_BOTTOM = (25, 30, 50)
TITLE_COLOR = (255, 215, 0)
SUBTITLE_COLOR = (180, 180, 200)
BUTTON_BG = (40, 55, 80)
BUTTON_HOVER = (60, 85, 120)
BUTTON_BORDER = (100, 120, 160)
BUTTON_TEXT = (240, 240, 240)
BUTTON_DISABLED_BG = (35, 35, 40)
BUTTON_DISABLED_TEXT = (100, 100, 100)
VERSION_COLOR = (80, 80, 100)


SAVE_PATH = save_dir() / "slot1.json"


class MainMenu:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.width, self.height = screen.get_size()

        self.font_title = pygame.font.SysFont("arial", 64, bold=True)
        self.font_subtitle = pygame.font.SysFont("arial", 22)
        self.font_button = pygame.font.SysFont("arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("arial", 14)

        btn_w = 320
        btn_h = 60
        btn_x = (self.width - btn_w) // 2
        start_y = self.height // 2 - 20
        spacing = 20

        self.buttons = [
            {
                "id": "new_game",
                "text": "НОВАЯ ИГРА",
                "rect": pygame.Rect(btn_x, start_y, btn_w, btn_h),
                "enabled": True,
            },
            {
                "id": "load_game",
                "text": "ЗАГРУЗИТЬ",
                "rect": pygame.Rect(btn_x, start_y + btn_h + spacing, btn_w, btn_h),
                "enabled": SAVE_PATH.exists(),
            },
            {
                "id": "quit",
                "text": "ВЫХОД",
                "rect": pygame.Rect(btn_x, start_y + (btn_h + spacing) * 2, btn_w, btn_h),
                "enabled": True,
            },
        ]

    def refresh_save_state(self) -> None:
        """Обновляет состояние кнопки «Загрузить» (после сохранения)."""
        for btn in self.buttons:
            if btn["id"] == "load_game":
                btn["enabled"] = SAVE_PATH.exists()

    # ============================================================
    # ОТРИСОВКА
    # ============================================================
    def draw(self) -> None:
        self._draw_background()

        title_surf = self.font_title.render("ФАЛАНГА", True, TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 3 - 40))
        self.screen.blit(title_surf, title_rect)

        sub_surf = self.font_subtitle.render(
            "Путь Александра", True, SUBTITLE_COLOR,
        )
        sub_rect = sub_surf.get_rect(center=(self.width // 2, self.height // 3 + 30))
        self.screen.blit(sub_surf, sub_rect)

        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            self._draw_button(btn, mouse_pos)

        version = self.font_small.render("v0.1 — прототип", True, VERSION_COLOR)
        version_rect = version.get_rect(bottomright=(self.width - 15, self.height - 10))
        self.screen.blit(version, version_rect)

    def _draw_background(self) -> None:
        for y in range(self.height):
            ratio = y / self.height
            r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * ratio)
            g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * ratio)
            b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))

    def _draw_button(self, btn: dict, mouse_pos: tuple[int, int]) -> None:
        rect = btn["rect"]
        hovered = rect.collidepoint(mouse_pos) and btn["enabled"]

        if not btn["enabled"]:
            color = BUTTON_DISABLED_BG
            text_color = BUTTON_DISABLED_TEXT
            border_color = (60, 60, 70)
        elif hovered:
            color = BUTTON_HOVER
            text_color = BUTTON_TEXT
            border_color = BUTTON_BORDER
        else:
            color = BUTTON_BG
            text_color = BUTTON_TEXT
            border_color = BUTTON_BORDER

        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=10)

        label = self.font_button.render(btn["text"], True, text_color)
        label_rect = label.get_rect(center=rect.center)
        self.screen.blit(label, label_rect)

    # ============================================================
    # ВВОД
    # ============================================================
    def handle_click(self, pos: tuple[int, int]) -> str | None:
        for btn in self.buttons:
            if btn["enabled"] and btn["rect"].collidepoint(pos):
                return btn["id"]
        return None

    def handle_key(self, key: int) -> str | None:
        if key == pygame.K_ESCAPE:
            return "quit"
        return None