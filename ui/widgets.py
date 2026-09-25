import pygame

class Button:
    def __init__(
            self,
            x: int, y: int, width:int, height: int,
            text:str,
            font: pygame.font.Font,
            color: tuple[int, int, int] = (60, 80, 120),
            hover_color: tuple[int, int, int] = (80, 110, 160),
            text_color: tuple[int, int, int] = (240, 240, 240)
    ) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False
        self.enabled = True

    def update(self, mouse_pos: tuple[int, int]) -> None:
        self.hovered = self.rect.collidepoint(mouse_pos)

    def draw(self, screen: pygame.Surface) -> None:
        if not self.enabled:
            color = (50, 50, 50)
        elif self.hovered:
            color = self.hover_color
        else:
            color = self.color

        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (20, 20, 30), self.rect, 2, border_radius=8)

        text_color = self.text_color if self.enabled else (100, 100, 100)
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, pos: tuple[int, int]) -> bool:
        return self.enabled and self.rect.collidepoint(pos)