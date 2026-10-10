"""Точка входа. Управляет состояниями приложения через класс App."""

import sys
import pygame

from core.game import GameState
from core.army import Army
from core.save_load import save_game, load_game
from ui.renderer import Renderer
from ui.main_menu import MainMenu
from ui.pause_menu import PauseMenu
from ui.slots_menu import SlotsMenu, MODE_SAVE, MODE_LOAD


# ============================================================
# СОЗДАНИЕ ИГРЫ
# ============================================================
def _create_new_game() -> GameState:
    """Создаёт новую игру."""
    game = GameState()
    game.load_map('data/map_act1.json')

    army = Army(id='army1', owner='macedonia', location='pella')
    army.add_units('Фаланга', 5)
    army.add_units('Гетайры', 2)
    army.alexander_attached = True
    game.armies[army.id] = army
    game.players['macedonia'].armies.append(army.id)

    garrison = Army(id='army_thessaly', owner='macedonia', location='thessaly')
    garrison.add_units('Фаланга', 3)
    game.armies[garrison.id] = garrison
    game.players['macedonia'].armies.append(garrison.id)

    game.start('macedonia')
    return game


def _copy_game_state(target: GameState, source: GameState) -> None:
    """Копирует поля из source в target, сохраняя id(target)."""
    target.regions = source.regions
    target.players = source.players
    target.armies = source.armies
    target.current_player_id = source.current_player_id
    target.turn = source.turn
    target._army_counter = source._army_counter
    target.alexander_died = source.alexander_died
    target.game_over = source.game_over
    target.game_over_reason = source.game_over_reason
    target.act1_completed = source.act1_completed
    target.act2_completed = source.act2_completed
    target.act1_goal_regions = source.act1_goal_regions
    target.act2_goal_regions = source.act2_goal_regions
    target.tutorial_active = source.tutorial_active
    target.tutorial_scene_id = source.tutorial_scene_id
    target.tutorial_line_index = source.tutorial_line_index

    target.current_act = source.current_act
    target.pending_scenes = source.pending_scenes
    target.played_scenes = source.played_scenes


# ============================================================
# СОСТОЯНИЯ
# ============================================================
STATE_MENU = "menu"
STATE_GAME = "game"
STATE_PAUSE = "pause"
STATE_SLOTS_SAVE = "slots_save"
STATE_SLOTS_LOAD = "slots_load"


# ============================================================
# КЛАСС ПРИЛОЖЕНИЯ
# ============================================================
class App:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.width, self.height = screen.get_size()

        self.state = STATE_MENU
        self.running = True

        # Меню
        self.menu = MainMenu(screen)
        self.pause = PauseMenu(screen)
        self.slots: SlotsMenu | None = None

        # Игра
        self.game: GameState | None = None
        self.renderer: Renderer | None = None

    # ============================================================
    # ГЛАВНЫЙ ЦИКЛ
    # ============================================================
    def run(self, clock: pygame.time.Clock) -> None:
        while self.running:
            dt = clock.tick(60)
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _update(self, dt: int) -> None:
        if self.state in (STATE_GAME, STATE_PAUSE,
                          STATE_SLOTS_SAVE, STATE_SLOTS_LOAD):
            if self.renderer is not None:
                self.renderer.update(dt)

    def _draw(self) -> None:
        if self.state == STATE_MENU:
            self.menu.draw()
            return

        # Игра рисуется во всех остальных состояниях
        if self.renderer is not None:
            self.renderer.draw()

        if self.state == STATE_PAUSE:
            self.pause.draw()
        elif self.state in (STATE_SLOTS_SAVE, STATE_SLOTS_LOAD):
            if self.slots is not None:
                self.slots.draw()

    # ============================================================
    # КЛАВИАТУРА
    # ============================================================
    def _handle_key(self, key: int) -> None:
        if self.state == STATE_MENU:
            self._key_menu(key)
        elif self.state == STATE_GAME:
            self._key_game(key)
        elif self.state == STATE_PAUSE:
            self._key_pause(key)
        elif self.state in (STATE_SLOTS_SAVE, STATE_SLOTS_LOAD):
            self._key_slots(key)

    def _key_menu(self, key: int) -> None:
        action = self.menu.handle_key(key)
        if action == "quit":
            self.running = False

    def _key_game(self, key: int) -> None:
        if self.renderer is None or self.game is None:
            return

        if key == pygame.K_ESCAPE:
            if self.renderer.novel_active:
                self.renderer.handle_key(key)
            elif self.renderer.tutorial_active:
                # ESC во время туториала игнорируется
                self.pause.reset()
                self.state = STATE_PAUSE
            elif (self.renderer.recruit_mode
                  or self.renderer.attack_mode
                  or self.renderer.move_mode):
                self.renderer.handle_key(key)
            else:
                self.pause.reset()
                self.state = STATE_PAUSE
        elif key == pygame.K_F1:
            _print_dump(self.game)
        else:
            self.renderer.handle_key(key)

    def _key_pause(self, key: int) -> None:
        action = self.pause.handle_key(key)
        if action == "resume":
            self.state = STATE_GAME

    def _key_slots(self, key: int) -> None:
        if self.slots is None:
            return
        action = self.slots.handle_key(key)
        if action == "back":
            if self.state == STATE_SLOTS_SAVE:
                self.state = STATE_PAUSE
            else:
                self.state = STATE_MENU

    # ============================================================
    # МЫШЬ
    # ============================================================
    def _handle_click(self, pos: tuple[int, int]) -> None:
        if self.state == STATE_MENU:
            self._click_menu(pos)
        elif self.state == STATE_GAME:
            self._click_game(pos)
        elif self.state == STATE_PAUSE:
            self._click_pause(pos)
        elif self.state in (STATE_SLOTS_SAVE, STATE_SLOTS_LOAD):
            self._click_slots(pos)

    def _click_menu(self, pos: tuple[int, int]) -> None:
        action = self.menu.handle_click(pos)
        if action == "new_game":
            self._start_new_game()
        elif action == "load_game":
            self._open_slots(MODE_LOAD)
        elif action == "quit":
            self.running = False

    def _click_game(self, pos: tuple[int, int]) -> None:
        if self.renderer is None or self.game is None:
            return

        action = self.renderer.handle_click(pos)
        if action == 'end_turn' and not self.renderer.ai_turn_active:
            self._end_player_turn()

    def _click_pause(self, pos: tuple[int, int]) -> None:
        action = self.pause.handle_click(pos)
        if action == "resume":
            self.state = STATE_GAME
        elif action == "save":
            self._open_slots(MODE_SAVE)
        elif action == "load":
            self._open_slots(MODE_LOAD)
        elif action == "exit_to_main":
            self._exit_to_main_menu()

    def _click_slots(self, pos: tuple[int, int]) -> None:
        if self.slots is None:
            return

        result = self.slots.handle_click(pos)

        # Клик мимо слотов — назад
        if result is None:
            if self.state == STATE_SLOTS_SAVE:
                self.state = STATE_PAUSE
            else:
                self.state = STATE_MENU
            return

        if result.get("action") != "slot":
            return

        slot_num = result["num"]
        save_path = f"data/saves/slot{slot_num}.json"

        if self.state == STATE_SLOTS_SAVE:
            self._save_to_slot(save_path)
            self.state = STATE_PAUSE
        else:  # STATE_SLOTS_LOAD
            self._load_from_slot(save_path)
            if self.game is not None and self.renderer is not None:
                self.state = STATE_GAME
            else:
                self.state = STATE_MENU

    # ============================================================
    # ДЕЙСТВИЯ
    # ============================================================
    def _start_new_game(self) -> None:
        """Новая игра: Пролог → Туториал."""
        self.game = _create_new_game()
        self.renderer = Renderer(self.screen, self.game)

        def on_prologue_finish():
            if self.renderer is not None:
                self.renderer.start_tutorial()

        self.renderer.start_novel(
            "story/scenes/prologue.json",
            "prologue_01",
            on_finish=on_prologue_finish,
        )
        self.state = STATE_GAME

    def _open_slots(self, mode: str) -> None:
        self.slots = SlotsMenu(self.screen, mode)
        if mode == MODE_SAVE:
            self.state = STATE_SLOTS_SAVE
        else:
            self.state = STATE_SLOTS_LOAD

    def _save_to_slot(self, save_path: str) -> None:
        if self.game is None or self.slots is None:
            return
        if self.renderer is not None:
            self.renderer._sync_tutorial_position()
        try:
            save_game(self.game, save_path)
            self.slots.refresh()
            print(f"Сохранено: {save_path}")
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def _load_from_slot(self, save_path: str) -> None:
        try:
            loaded = load_game(save_path)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return

        if self.renderer is None:
            # Игра ещё не создана — создаём заново
            self.game = loaded
            self.renderer = Renderer(self.screen, self.game)
        else:
            # Игра уже есть — копируем поля
            _copy_game_state(self.game, loaded)
            self.renderer.game = self.game
            self.renderer.actions.game = self.game

        # Туториал: восстановить позицию
        if loaded.tutorial_active:
            self.renderer.start_tutorial_at(
                loaded.tutorial_scene_id or "tutorial_01",
                loaded.tutorial_line_index,
            )
        else:
            self.renderer.tutorial_active = False
            self.renderer.game.tutorial_active = False

    def _exit_to_main_menu(self) -> None:
        """Выход в главное меню без сохранения."""
        self.game = None
        self.renderer = None
        self.slots = None
        self.menu.refresh_save_state()
        self.state = STATE_MENU

    def _end_player_turn(self) -> None:
        if self.game is None or self.renderer is None:
            return

        if self.renderer.tutorial_active and self.renderer.tutorial_view is not None:
            self.renderer.tutorial_pending_notify = {"event": "end_turn_clicked"}

        self.game.end_turn()
        self.renderer.reset_state()

        current = self.game.current_player()
        if current.is_ai:
            self.renderer.start_ai_turn(self.game)


# ============================================================
# УТИЛИТЫ
# ============================================================
def _print_dump(game: GameState) -> None:
    print("\n=== ДАМП ===")
    for a in game.armies.values():
        print(f"  {a.id}: owner={a.owner}, loc={a.location}, units={a.units}")
    print(f"  Греция жива: {game.is_greece_alive()}")
    print(f"  _army_counter = {game._army_counter}")


# ============================================================
# ТОЧКА ВХОДА
# ============================================================
def main() -> None:
    pygame.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Фаланга: Путь Александра")

    clock = pygame.time.Clock()

    app = App(screen)
    app.run(clock)

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()