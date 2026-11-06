"""Менеджер звука: музыка, эмбиент, SFX."""
import pygame
from core.paths import resource_path
from core.log import get_logger

log = get_logger(__name__)


class AudioManager:
    def __init__(self) -> None:
        # Инициализируем микшер (можно 44100, -16, 2, 512 для меньшей задержки)
        try:
            pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
        except pygame.error as e:
            log.error("Не удалось инициализировать звук: %s", e)
            self.enabled = False
            return
        self.enabled = True

        self.current_music = None
        self.music_volume = 0.5
        self.sfx_volume = 0.7

        # Кэш загруженных звуков
        self.sounds = {}

    def play_music(self, track_name: str, loops: int = -1, fade_ms: int = 1000) -> None:
        if not self.enabled or self.current_music == track_name:
            return

        path = resource_path(f"assets/audio/music/{track_name}.ogg")
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(loops, fade_ms=fade_ms)
            self.current_music = track_name
        except pygame.error as e:
            log.error("Не удалось загрузить музыку %s: %s", path, e)

    def stop_music(self, fade_ms: int = 1000) -> None:
        if not self.enabled:
            return
        pygame.mixer.music.fadeout(fade_ms)
        self.current_music = None

    def play_sfx(self, sfx_name: str) -> None:
        if not self.enabled:
            return

        if sfx_name not in self.sounds:
            path = resource_path(f"assets/audio/sfx/{sfx_name}.ogg")
            try:
                self.sounds[sfx_name] = pygame.mixer.Sound(str(path))
            except pygame.error as e:
                log.error("Не удалось загрузить звук %s: %s", path, e)
                return

        sound = self.sounds[sfx_name]
        sound.set_volume(self.sfx_volume)
        sound.play()