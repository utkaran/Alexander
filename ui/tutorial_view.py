"""Экран туториала: рисуется поверх карты, ведёт игрока за руку."""

from pathlib import Path
from core.paths import resource_path

import pygame

from story.engine import NovelEngine
from story.characters import get_name, get_color, get_flip

PORTRAITS_DIR = resource_path("assets/portraits")


# Цвета
OVERLAY_COLOR = (0, 0, 0, 120)             # затемнение карты
TEXT_COLOR = (240, 240, 240)
NARRATOR_COLOR = (180, 180, 200)
HINT_COLOR = (120, 120, 140)

# Диалоговое окно
BOX_BG = (25, 30, 45)
BOX_BG_ALPHA = 200
BOX_BORDER = (80, 90, 120)
BOX_BORDER_ALPHA = 220

# Портрет
PORTRAIT_SIZE = 120
PORTRAIT_MARGIN = 15
PORTRAIT_BG = (40, 45, 65)

# Подсветка
HIGHLIGHT_GOLD = (255, 215, 0)
HIGHLIGHT_CAPITAL = (255, 240, 120)
HIGHLIGHT_ENEMY = (255, 80, 80)
HIGHLIGHT_PULSE_SPEED = 5.0      # скорость пульсации (рад/сек)
HIGHLIGHT_THICKNESS = 4
HIGHLIGHT_PADDING = 8

# Кнопка "Далее"
NEXT_BG = (40, 55, 80)
NEXT_HOVER = (60, 85, 120)
NEXT_BORDER = (100, 120, 160)


class TutorialView:
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

        # Кэш портретов
        self.portraits: dict[str, pygame.Surface | None] = {}

        # Время для пульсации
        self.time = 0.0

        # Callback на отрисовку подсветки — его установит Renderer
        # Callback получает (highlight_list, pulse_alpha)
        self.highlight_drawer = None

    def update(self, dt: int) -> None:
        self.time += dt / 1000.0

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
                except pygame.error:
                    self.portraits[who] = None
                    return None

        self.portraits[who] = None
        return None

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

        # 3. Диалоговое окно
        self._draw_dialogue_box()

        # 4. Портрет
        line = self.engine.current_line()
        who = line.get("who", "narrator") if line else "narrator"
        if who != "narrator":
            portrait_x = self.box_x + PORTRAIT_MARGIN
            portrait_y = self.box_y + (self.box_height - PORTRAIT_SIZE) // 2
            self._draw_portrait(who, portrait_x, portrait_y)

        # 5. Кнопка "Далее" — только если не ждём события
        if self.engine.current_wait_for() is None:
            self._draw_next_button()

    def _compute_pulse(self) -> float:
        """Возвращает 0.0…1.0 — коэффициент пульсации."""
        import math
        return 0.5 + 0.5 * math.sin(self.time * HIGHLIGHT_PULSE_SPEED)

    def _draw_dialogue_box(self) -> None:
        bg_surface = pygame.Surface((self.box_w, self.box_height), pygame.SRCALPHA)
        bg_surface.fill((*BOX_BG, BOX_BG_ALPHA))
        self.screen.blit(bg_surface, (self.box_x, self.box_y))

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
            scale = max(PORTRAIT_SIZE / img_w, PORTRAIT_SIZE / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            scaled = pygame.transform.smoothscale(image, (new_w, new_h))

            crop_x = (new_w - PORTRAIT_SIZE) // 2
            crop_y = (new_h - PORTRAIT_SIZE) // 2

            portrait_surf = pygame.Surface((PORTRAIT_SIZE, PORTRAIT_SIZE), pygame.SRCALPHA)
            portrait_surf.blit(scaled, (-crop_x, -crop_y))
            self.screen.blit(portrait_surf, (x, y))

            pygame.draw.rect(
                self.screen, get_color(who),
                pygame.Rect(x, y, PORTRAIT_SIZE, PORTRAIT_SIZE),
                3, border_radius=8,
            )
        else:
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
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.next_button_rect.collidepoint(mouse_pos)

        color = NEXT_HOVER if hovered else NEXT_BG
        pygame.draw.rect(self.screen, color, self.next_button_rect, border_radius=8)
        pygame.draw.rect(self.screen, NEXT_BORDER, self.next_button_rect, 2, border_radius=8)

        label = self.font_medium.render("Далее ▶", True, TEXT_COLOR)
        label_rect = label.get_rect(center=self.next_button_rect.center)
        self.screen.blit(label, label_rect)

    # ============================================================
    # ВВОД
    # ============================================================
    def handle_click(self, pos: tuple[int, int]) -> dict | None:
        # Если ждём события — клики по экрану игнорируем
        if self.engine.current_wait_for() is not None:
            return None

        # Клик по кнопке "Далее"
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
def draw_highlight(
    screen: pygame.Surface,
    highlight_list: list[dict],
    pulse: float,
    region_pos_getter,
    region_radius: int,
    buttons: dict,
) -> None:
    """Рисует пульсирующую подсветку.

    screen — куда рисовать
    highlight_list — список подсветок из JSON
    pulse — 0.0…1.0
    region_pos_getter — функция(region_id) -> (x, y) | None
    region_radius — базовый радиус региона
    buttons — словарь {"recruit_button": Button, ...}
    """
    for h in highlight_list:
        h_type = h.get("type")
        color_name = h.get("color", "gold")

        if color_name == "capital":
            base_color = HIGHLIGHT_CAPITAL
        elif color_name == "enemy":
            base_color = HIGHLIGHT_ENEMY
        else:
            base_color = HIGHLIGHT_GOLD

        # Пульсация яркости
        alpha = int(120 + 135 * pulse)
        color = (*base_color, alpha)

        if h_type == "region":
            region_id = h.get("id")
            pos = region_pos_getter(region_id)
            if pos is None:
                continue
            _draw_region_highlight(screen, pos, region_radius, color, is_capital=(color_name == "capital"))

        elif h_type == "region_owner":
            owner = h.get("owner")
            # region_pos_getter для owner — нам нужен доступ к game. Передадим через замыкание.
            # Здесь предполагаем, что region_pos_getter умеет принимать ("owner", owner)
            # Это некрасиво, но работает.
            # В реальности лучше передать список регионов напрямую.
            # См. интеграцию — Renderer сам собирает список регионов по owner и передаёт сюда.
            pass  # Обрабатывается в Renderer

        elif h_type == "button":
            btn_id = h.get("id")
            btn = buttons.get(btn_id)
            if btn is None:
                continue
            _draw_button_highlight(screen, btn.rect, color)


def _draw_region_highlight(screen, pos, radius, color, is_capital: bool = False) -> None:
    """Пульсирующая обводка региона."""
    x, y = pos
    r = radius + HIGHLIGHT_PADDING

    # Внешняя обводка (более прозрачная, толще)
    outer_color = (*color[:3], color[3] // 2)
    pygame.draw.circle(screen, outer_color[:3], (x, y), r + 4, 2)

    # Внутренняя обводка (яркая)
    pygame.draw.circle(screen, color[:3], (x, y), r, HIGHLIGHT_THICKNESS)

    if is_capital:
        # Двойная обводка для столицы
        pygame.draw.circle(screen, color[:3], (x, y), r + 6, 2)


def _draw_button_highlight(screen, rect: pygame.Rect, color) -> None:
    """Пульсирующая рамка вокруг кнопки."""
    expanded = rect.inflate(HIGHLIGHT_PADDING, HIGHLIGHT_PADDING)
    pygame.draw.rect(screen, color[:3], expanded, HIGHLIGHT_THICKNESS, border_radius=10)