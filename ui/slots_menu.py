from pathlib import Path
import pygame
from core.save_load import get_save_info

# Цвета
OVERLAY_COLOR = (0, 0, 0, 200)
PANEL_BG = (25, 30, 45)
PANEL_BORDER = (80, 90, 120)
SLOT_BG = (40, 50, 70)
SLOT_HOVER = (60, 80, 110)
SLOT_BORDER = (90, 110, 150)
SLOT_EMPTY_BG = (30, 35, 45)
SLOT_EMPTY_BORDER = (60, 70, 90)
SLOT_TEXT = (240, 240, 240)
SLOT_INFO = (180, 180, 200)
SLOT_EMPTY_TEXT = (100, 100, 120)

# Режим
MODE_SAVE = "save"
MODE_LOAD = "load"

class SlotsMenu:
    def __init__(self, screen: pygame.Surface, mode: str) -> None:
        self.screen = screen
        self.mode = mode  # MODE_SAVE | MODE_LOAD
        self.width, self.height = screen.get_size()

        self.font_title = pygame.font.SysFont("arial", 36, bold=True)
        self.font_slot_num = pygame.font.SysFont("arial", 28, bold=True)
        self.font_slot_info = pygame.font.SysFont("arial", 16)
        self.font_small = pygame.font.SysFont("arial", 14)

        # 5 слотов — вертикальный список или сетка?
        # Сделаем сетку: 5 слотов в ряд (или 3+2).
        # Пойдём простым путём: 5 карточек в ряд.
        slot_w = 200
        slot_h = 240
        spacing = 20
        total_w = 5 * slot_w + 4 * spacing
        start_x = (self.width - total_w) // 2
        start_y = (self.height - slot_h) // 2

        self.slots: list[dict] = []
        for i in range(5):
            slot_num = i + 1
            rect = pygame.Rect(start_x + i * (slot_w + spacing), start_y, slot_w, slot_h)
            save_path = f"data/saves/slot{slot_num}.json"
            info = get_save_info(save_path)

            self.slots.append({
                "num": slot_num,
                "rect": rect,
                "path": save_path,
                "info": info,
                "exists": info is not None,
            })

    def refresh(self) -> None:
        """Обновляет информацию о слотах (после сохранения)."""
        for slot in self.slots:
            info = get_save_info(slot["path"])
            slot["info"] = info
            slot["exists"] = info is not None

    # ОТРИСОВКА
    def draw(self) -> None:
        # Оверлей
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

        # Заголовок
        title_text = "СОХРАНИТЬ ИГРУ" if self.mode == MODE_SAVE else "ЗАГРУЗИТЬ ИГРУ"
        title_surf = self.font_title.render(title_text, True, (240, 240, 240))
        title_rect = title_surf.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title_surf, title_rect)

        # Слоты
        mouse_pos = pygame.mouse.get_pos()
        for slot in self.slots:
            self._draw_slot(slot, mouse_pos)

        # Подсказка
        hint = self.font_small.render(
            "ESC или клик мимо — назад",
            True, (140, 140, 160),
        )
        hint_rect = hint.get_rect(center=(self.width // 2, self.height - 40))
        self.screen.blit(hint, hint_rect)

    def _draw_slot(self, slot: dict, mouse_pos: tuple[int, int]) -> None:
        rect = slot["rect"]
        exists = slot["exists"]
        hovered = rect.collidepoint(mouse_pos)

        # Цвета в зависимости от состояния
        if not exists:
            # Пустой слот
            bg = SLOT_EMPTY_BG
            border = SLOT_EMPTY_BORDER
            text_color = SLOT_EMPTY_TEXT
            info_color = SLOT_EMPTY_TEXT
        elif hovered:
            bg = SLOT_HOVER
            border = SLOT_BORDER
            text_color = SLOT_TEXT
            info_color = SLOT_INFO
        else:
            bg = SLOT_BG
            border = SLOT_BORDER
            text_color = SLOT_TEXT
            info_color = SLOT_INFO

        pygame.draw.rect(self.screen, bg, rect, border_radius=12)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=12)

        # Номер слота
        num_surf = self.font_slot_num.render(f"СЛОТ {slot['num']}", True, text_color)
        num_rect = num_surf.get_rect(center=(rect.centerx, rect.y + 50))
        self.screen.blit(num_surf, num_rect)

        # Разделитель
        line_y = rect.y + 90
        pygame.draw.line(
            self.screen, border,
            (rect.x + 20, line_y), (rect.right - 20, line_y), 1,
        )

        # Информация
        if exists:
            info = slot["info"]
            line1 = f"Ход: {info['turn']}"
            line2 = f"Игрок: {info['player']}"

            l1_surf = self.font_slot_info.render(line1, True, info_color)
            l1_rect = l1_surf.get_rect(center=(rect.centerx, rect.y + 130))
            self.screen.blit(l1_surf, l1_rect)

            l2_surf = self.font_slot_info.render(line2, True, info_color)
            l2_rect = l2_surf.get_rect(center=(rect.centerx, rect.y + 160))
            self.screen.blit(l2_surf, l2_rect)

            # Для save-режима: подсказка «перезаписать»
            if self.mode == MODE_SAVE:
                hint_surf = self.font_small.render("нажми — перезаписать", True, (150, 150, 170))
                hint_rect = hint_surf.get_rect(center=(rect.centerx, rect.bottom - 30))
                self.screen.blit(hint_surf, hint_rect)
        else:
            empty_surf = self.font_slot_info.render("Пусто", True, info_color)
            empty_rect = empty_surf.get_rect(center=(rect.centerx, rect.y + 130))
            self.screen.blit(empty_surf, empty_rect)

            if self.mode == MODE_SAVE:
                hint_surf = self.font_small.render("нажми — сохранить", True, (150, 150, 170))
                hint_rect = hint_surf.get_rect(center=(rect.centerx, rect.bottom - 30))
                self.screen.blit(hint_surf, hint_rect)

    # ВВОД
    def handle_click(self, pos: tuple[int, int]) -> dict | None:
        """Возвращает {'action': 'slot', 'num': N} или None (клик мимо)."""
        for slot in self.slots:
            if slot["rect"].collidepoint(pos):
                # В save-режиме можно кликнуть в любой слот (пустой или занятый).
                # В load-режиме — только в занятый.
                if self.mode == MODE_SAVE:
                    return {"action": "slot", "num": slot["num"]}
                else:
                    if slot["exists"]:
                        return {"action": "slot", "num": slot["num"]}
                    return None
        return None

    def handle_key(self, key: int) -> str | None:
        if key == pygame.K_ESCAPE:
            return "back"
        return None