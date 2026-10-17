"""Заставка при запуске: плавное появление и исчезновение иконки игры."""

from pathlib import Path

import pygame

from core.paths import resource_path


BG_COLOR = (10, 12, 20)          # почти чёрный (чуть темнее меню)
ICON_SIZE = 256                   # размер иконки на экране (256×256)

# Тайминги (в миллисекундах)
FADE_IN_MS = 1500
HOLD_MS = 800
FADE_OUT_MS = 1000
TOTAL_MS = FADE_IN_MS + HOLD_MS + FADE_OUT_MS


class SplashScreen:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.width, self.height = screen.get_size()

        self.timer = 0
        self.finished = False

        # Загружаем иконку (256×256) — если нет, ставим заглушку
        try:
            icon_path = resource_path("assets/icon.png")
            self.icon = pygame.image.load(str(icon_path)).convert_alpha()
            self.icon = pygame.transform.smoothscale(self.icon, (ICON_SIZE, ICON_SIZE))
        except (pygame.error, FileNotFoundError):
            self.icon = None
            print("Splash: иконка не найдена, показываю пустой экран")

    def update(self, dt: int) -> None:
        """Обновляет таймер. Когда время вышло — finished = True."""
        if self.finished:
            return
        self.timer += dt
        if self.timer >= TOTAL_MS:
            self.finished = True

    def draw(self) -> None:
        """Рисует заставку с текущей прозрачностью."""
        self.screen.fill(BG_COLOR)

        if self.icon is None:
            return

        alpha = self._compute_alpha()

        # Копия иконки с нужной прозрачностью
        icon_copy = self.icon.copy()
        icon_copy.set_alpha(alpha)

        # Центрируем
        x = (self.width - ICON_SIZE) // 2
        y = (self.height - ICON_SIZE) // 2
        self.screen.blit(icon_copy, (x, y))

    def _compute_alpha(self) -> int:
        """0–255: 0 — невидимо, 255 — полностью видно."""
        if self.timer < FADE_IN_MS:
            # Fade-in: 0 → 255
            return int(255 * (self.timer / FADE_IN_MS))

        if self.timer < FADE_IN_MS + HOLD_MS:
            # Держим на максимуме
            return 255

        # Fade-out: 255 → 0
        fade_progress = (self.timer - FADE_IN_MS - HOLD_MS) / FADE_OUT_MS
        return int(255 * (1.0 - fade_progress))

    def handle_key(self, key: int) -> bool:
        """Пропустить заставку по любой клавише. Возвращает True, если пропустили."""
        if key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
            self.finished = True
            return True
        return False

    def handle_click(self, pos: tuple[int, int]) -> bool:
        """Пропустить заставку кликом. Возвращает True, если пропустили."""
        self.finished = True
        return True