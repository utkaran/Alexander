"""Контроллер туториала: состояние, разрешения, события.

Вынесено из renderer.py. Renderer держит экземпляр и делегирует.
Сигнатуры методов Renderer НЕ меняются — обёртки сохраняют имена.
"""

from story.engine import NovelEngine
from ui.tutorial_view import TutorialView


class TutorialController:
    def __init__(self, renderer) -> None:
        self.renderer = renderer
        self.active = False
        self.view = None
        self.final_overlay_timer = 0
        self.pending_notify = None
        self.pending_thebes_revolt = False

    # ============================================================
    # РАЗРЕШЕНИЯ (чистые, только читают)
    # ============================================================
    def is_allowed_unit(self, unit_type: str) -> bool:
        """Разрешён ли найм этого юнита в туториале."""
        if not self.active or self.view is None:
            return True
        allow = self.engine.current_allow_unit
        return allow is None or allow == unit_type

    def is_allowed_region(self, region_id: str) -> bool:
        if not self.active or self.view is None:
            return True
        allow = self.engine.current_allow_region
        return allow is None or allow == region_id

    def is_allowed_action(self, action: str) -> bool:
        if not self.active or self.view is None:
            return True
        allow = self.engine.current_allow_action
        return allow is None or allow == action

    def is_allowed_target(self, region_id: str) -> bool:
        if not self.active or self.view is None:
            return True
        allow = self.engine.current_allow_target
        return allow is None or allow == region_id

    def start(self, scene_file: str = "story/scenes/tutorial.json",
              start_scene: str = "tutorial_01") -> None:
        self._start_at(scene_file, start_scene, 0)

    def start_at(self, scene_id: str, line_index: int,
                 scene_file: str = "story/scenes/tutorial.json") -> None:
        self._start_at(scene_file, scene_id, line_index)

    def _start_at(self, scene_file: str, scene_id: str, line_index: int) -> None:
        self.engine = NovelEngine()
        self.engine.load_scenes(scene_file)
        self.engine.start_at(scene_id, line_index)
        self.view = TutorialView(self.renderer.screen, self.engine)
        self.view.highlight_drawer = self.renderer._draw_tutorial_highlight
        self.active = True
        self.renderer.game.tutorial_active = True
        self.final_overlay_timer = 0

    def end(self) -> None:
        self.active = False
        self.renderer.game.tutorial_active = False
        self.renderer.game.tutorial_scene_id = None
        self.renderer.game.tutorial_line_index = 0
        self.view = None
        self.final_overlay_timer = 2000
        self.pending_thebes_revolt = True

    # ============================================================
    # СИНХРОНИЗАЦИЯ ПОЗИЦИИ (для сохранения)
    # ============================================================
    def sync_position(self) -> None:
        """Пишет scene_id + line_index в GameState для сейва."""
        if not self.active:
            return
        scene_id, line_index = self.engine.get_position()
        self.renderer.game.tutorial_scene_id = scene_id
        self.renderer.game.tutorial_line_index = line_index