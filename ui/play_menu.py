"""Подменю «Играть»: выбор режима (Кампания / Альтернатива / Песочница)."""

import pygame

from core.profile import load_profile


BG_TOP = (15, 20, 35)
BG_BOTTOM = (25, 30, 50)
TITLE_COLOR = (255, 215, 0)
BUTTON_BG = (40, 55, 80)
BUTTON_HOVER = (60, 85, 120)
BUTTON_BORDER = (100, 120, 160)
BUTTON_TEXT = (240, 240, 240)
BUTTON_DISABLED_BG = (35, 35, 40)
BUTTON_DISABLED_TEXT = (100, 100, 100)
HINT_COLOR = (150, 150, 150)
BACK_BG = (60, 40, 40)
BACK_HOVER = (90, 60, 60)


class PlayMenu:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.width, self.height = screen.get_size()

        self.font_title = pygame.font.SysFont("arial", 42, bold=True)
        self.font_button = pygame.font.SysFont("arial", 26, bold=True)
        self.font_small = pygame.font.SysFont("arial", 14)

        self.profile = load_profile()

        btn_w = 420
        btn_h = 64
        btn_x = (self.width - btn_w) // 2
        start_y = self.height // 2 - 180
        self.start_y = start_y
        spacing = 18

        self.buttons = [
            {
                "id": "campaign",
                "text": "КАМПАНИЯ",
                "rect": pygame.Rect(btn_x, start_y, btn_w, btn_h),
                "enabled": True,
                "hint": "Сюжетное прохождение по актам",
            },
            {
                "id": "alternate",
                "text": "АЛЬТЕРНАТИВА",
                "rect": pygame.Rect(btn_x, start_y + (btn_h + spacing), btn_w, btn_h),
                "enabled": self.profile.get("alternate_unlocked", False),
                "hint": "Откроется после исторической концовки",
            },
            {
                "id": "scenarios",
                "text": "СЦЕНАРИИ",
                "rect": pygame.Rect(btn_x, start_y + (btn_h + spacing) * 2, btn_w, btn_h),
                "enabled": False,  # ← пока False (нет сценариев)
                "hint": "Скоро: Граник, Исс, Тир, Гавгамелы, Гидасп",
            },
            {
                "id": "sandbox",
                "text": "ПЕСОЧНИЦА",
                "rect": pygame.Rect(btn_x, start_y + (btn_h + spacing) * 3, btn_w, btn_h),
                "enabled": False,
                "hint": "Скоро: свободная игра на полной карте",
            },
        ]

        # Кнопка «Назад»
        back_w = 200
        back_h = 50
        self.back_rect = pygame.Rect(
            (self.width - back_w) // 2,
            self.height - 80,
            back_w,
            back_h,
        )

    def refresh(self) -> None:
        """Перечитывает профиль (после разблокировки)."""
        self.profile = load_profile()
        unlocked = self.profile.get("scenarios_unlocked", [])
        for btn in self.buttons:
            if btn["id"] == "alternate":
                btn["enabled"] = self.profile.get("alternate_unlocked", False)
            elif btn["id"] == "scenarios":
                btn["enabled"] = bool(unlocked)
                btn["hint"] = (
                    "Отдельные исторические битвы"
                    if unlocked
                    else "Откроются по ходу сюжета"
                )

    # ОТРИСОВКА

    def draw(self) -> None:
        self._draw_background()

        title_surf = self.font_title.render("ВЫБОР РЕЖИМА", True, TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.start_y - 60))
        self.screen.blit(title_surf, title_rect)

        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            self._draw_button(btn, mouse_pos)

        self._draw_back(mouse_pos)

        hint = self.font_small.render(
            "ESC — назад в главное меню",
            True, HINT_COLOR,
        )
        hint_rect = hint.get_rect(center=(self.width // 2, self.height - 20))
        self.screen.blit(hint, hint_rect)

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
        label_rect = label.get_rect(center=(rect.centerx, rect.centery - 8))
        self.screen.blit(label, label_rect)

        if not btn["enabled"]:
            hint = self.font_small.render(btn["hint"], True, BUTTON_DISABLED_TEXT)
            hint_rect = hint.get_rect(center=(rect.centerx, rect.centery + 16))
            self.screen.blit(hint, hint_rect)

    def _draw_back(self, mouse_pos: tuple[int, int]) -> None:
        hovered = self.back_rect.collidepoint(mouse_pos)
        color = BACK_HOVER if hovered else BACK_BG
        pygame.draw.rect(self.screen, color, self.back_rect, border_radius=10)
        pygame.draw.rect(self.screen, BUTTON_BORDER, self.back_rect, 2, border_radius=10)
        label = self.font_button.render("НАЗАД", True, BUTTON_TEXT)
        label_rect = label.get_rect(center=self.back_rect.center)
        self.screen.blit(label, label_rect)

    # ВВОД

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        if self.back_rect.collidepoint(pos):
            return "back"
        for btn in self.buttons:
            if btn["enabled"] and btn["rect"].collidepoint(pos):
                return btn["id"]
        return None

    def handle_key(self, key: int) -> str | None:
        if key == pygame.K_ESCAPE:
            return "back"
        return None