"""Контроллер туториала: состояние, разрешения, события.

Вынесено из renderer.py. Renderer держит экземпляр и делегирует.
Сигнатуры методов Renderer НЕ меняются — обёртки сохраняют имена.
"""

from story.engine import NovelEngine


class TutorialController:
    def __init__(self, renderer) -> None:
        self.renderer = renderer
        self.active = False
        self.engine = renderer.tutorial_engine
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