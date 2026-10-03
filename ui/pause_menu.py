import pygame

# Цвета
OVERLAY_COLOR = (0, 0, 0, 180)
PANEL_BG = (30, 35, 50)
PANEL_BORDER = (80, 90, 120)
BUTTON_BG = (45, 60, 85)
BUTTON_HOVER = (65, 90, 125)
BUTTON_BORDER = (100, 120, 160)
BUTTON_TEXT = (240, 240, 240)
BUTTON_DANGER_BG = (100, 40, 40)
BUTTON_DANGER_HOVER = (140, 55, 55)

# Подтверждение
CONFIRM_BG = (40, 30, 40)
CONFIRM_BORDER = (160, 80, 80)
CONFIRM_TEXT = (255, 200, 200)
CONFIRM_YES_BG = (140, 50, 50)
CONFIRM_YES_HOVER = (180, 70, 70)
CONFIRM_NO_BG = (50, 60, 80)
CONFIRM_NO_HOVER = (70, 90, 120)

class PauseMenu:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.width, self.height = screen.get_size()

        self.font_title = pygame.font.SysFont("arial", 42, bold=True)
        self.font_button = pygame.font.SysFont("arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("arial", 16)

        # Кнопки главного экрана паузы
        btn_w = 320
        btn_h = 56
        btn_x = (self.width - btn_w) // 2
        start_y = self.height // 2 - 120
        spacing = 14

        self.buttons = [
            {
                "id": "resume",
                "text": "ПРОДОЛЖИТЬ",
                "rect": pygame.Rect(btn_x, start_y, btn_w, btn_h),
                "danger": False,
            },
            {
                "id": "save",
                "text": "СОХРАНИТЬ",
                "rect": pygame.Rect(btn_x, start_y + (btn_h + spacing), btn_w, btn_h),
                "danger": False,
            },
            {
                "id": "load",
                "text": "ЗАГРУЗИТЬ",
                "rect": pygame.Rect(btn_x, start_y + (btn_h + spacing) * 2, btn_w, btn_h),
                "danger": False,
            },
            {
                "id": "exit_to_main",
                "text": "ВЫЙТИ В ГЛАВНОЕ МЕНЮ",
                "rect": pygame.Rect(btn_x, start_y + (btn_h + spacing) * 3, btn_w, btn_h),
                "danger": True,
            },
        ]

        # Подтверждение выхода
        self.confirm_shown = False

        # Кнопки подтверждения
        cw, ch = 160, 50
        cx = (self.width - cw * 2 - 20) // 2
        cy = self.height // 2 + 60
        self.confirm_yes_rect = pygame.Rect(cx, cy, cw, ch)
        self.confirm_no_rect = pygame.Rect(cx + cw + 20, cy, cw, ch)

    def reset(self) -> None:
        self.confirm_shown = False

    # ОТРИСОВКА
    def draw(self) -> None:
        # Оверлей затемнения
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

        if self.confirm_shown:
            self._draw_confirm()
        else:
            self._draw_main()

    def _draw_main(self) -> None:
        # Заголовок
        title_surf = self.font_title.render("ПАУЗА", True, BUTTON_TEXT)
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 2 - 200))
        self.screen.blit(title_surf, title_rect)

        # Кнопки
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            self._draw_button(btn, mouse_pos)

        # Подсказка снизу
        hint = self.font_small.render(
            "ESC или клик мимо — продолжить игру",
            True, (140, 140, 160),
        )
        hint_rect = hint.get_rect(center=(self.width // 2, self.height - 40))
        self.screen.blit(hint, hint_rect)

    def _draw_button(self, btn: dict, mouse_pos: tuple[int, int]) -> None:
        rect = btn["rect"]
        hovered = rect.collidepoint(mouse_pos)
        is_danger = btn.get("danger", False)

        if is_danger:
            color = BUTTON_DANGER_HOVER if hovered else BUTTON_DANGER_BG
        else:
            color = BUTTON_HOVER if hovered else BUTTON_BG

        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        pygame.draw.rect(self.screen, BUTTON_BORDER, rect, 2, border_radius=10)

        label = self.font_button.render(btn["text"], True, BUTTON_TEXT)
        label_rect = label.get_rect(center=rect.center)
        self.screen.blit(label, label_rect)

    def _draw_confirm(self) -> None:
        # Панель
        panel_w = 560
        panel_h = 200
        panel_x = (self.width - panel_w) // 2
        panel_y = (self.height - panel_h) // 2
        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

        pygame.draw.rect(self.screen, CONFIRM_BG, panel, border_radius=12)
        pygame.draw.rect(self.screen, CONFIRM_BORDER, panel, 2, border_radius=12)

        # Текст вопроса
        text = "Выйти в главное меню без сохранения?"
        text_surf = self.font_button.render(text, True, CONFIRM_TEXT)
        text_rect = text_surf.get_rect(center=(self.width // 2, panel_y + 60))
        self.screen.blit(text_surf, text_rect)

        # Кнопки Да / Нет
        mouse_pos = pygame.mouse.get_pos()

        # Да
        yes_hovered = self.confirm_yes_rect.collidepoint(mouse_pos)
        yes_color = CONFIRM_YES_HOVER if yes_hovered else CONFIRM_YES_BG
        pygame.draw.rect(self.screen, yes_color, self.confirm_yes_rect, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BORDER, self.confirm_yes_rect, 2, border_radius=8)
        yes_label = self.font_button.render("ДА", True, BUTTON_TEXT)
        yes_rect = yes_label.get_rect(center=self.confirm_yes_rect.center)
        self.screen.blit(yes_label, yes_rect)

        # Нет
        no_hovered = self.confirm_no_rect.collidepoint(mouse_pos)
        no_color = CONFIRM_NO_HOVER if no_hovered else CONFIRM_NO_BG
        pygame.draw.rect(self.screen, no_color, self.confirm_no_rect, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BORDER, self.confirm_no_rect, 2, border_radius=8)
        no_label = self.font_button.render("НЕТ", True, BUTTON_TEXT)
        no_rect = no_label.get_rect(center=self.confirm_no_rect.center)
        self.screen.blit(no_label, no_rect)

    # ВВОД

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        if self.confirm_shown:
            if self.confirm_yes_rect.collidepoint(pos):
                self.confirm_shown = False
                return 'exit_to_main'
            if self.confirm_no_rect.collidepoint(pos):
                self.confirm_shown = False
                return None
            return None

        for btn in self.buttons:
            if btn['rect'].collidepoint(pos):
                if btn['id'] == 'exit_to_main':
                    self.confirm_shown = True
                    return None
                return btn['id']

        return 'resume'

    def handle_key(self, key: int) -> str | None:
        if key == pygame.K_ESCAPE:
            if self.confirm_shown:
                self.confirm_shown = False
                return None
            return 'resume'
        return None