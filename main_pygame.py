import sys
import pygame

from core.game import GameState
from core.army import Army
from ui.renderer import Renderer

from core.save_load import save_game, load_game

def main() -> None:
    pygame.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Фаланга: Путь Александра")

    clock = pygame.time.Clock()

    game = GameState()
    game.load_map('data/map_act1.json')

    army = Army(id='army1', owner='macedonia', location='pella')
    army.add_units('Фаланга', 5)
    army.add_units('Гетайры', 2)
    army.alexander_attached = True
    game.armies[army.id] = army
    game.players['macedonia'].armies.append(army.id)

    game.start('macedonia')

    from core.army import Army as TestArmy
    rear = TestArmy(id='g_rear', owner='greece', location='sparta')
    rear.add_units('Фаланга', 3)
    game.armies['g_rear'] = rear
    game.players['greece'].armies.append('g_rear')

    renderer = Renderer(screen, game)

    running = True
    while running:
        dt = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # ESC: сначала закрываем окна, потом выход
                    if renderer.recruit_mode or renderer.attack_mode or renderer.move_mode:
                        renderer.handle_key(event.key)
                    else:
                        running = False
                elif event.key == pygame.K_F1:
                    print("\n=== ДАМП ===")
                    for a in game.armies.values():
                        print(f"  {a.id}: owner={a.owner}, loc={a.location}, units={a.units}")
                        print(f"  Греция жива: {game.is_greece_alive()}")
                    print(f"  _army_counter = {game._army_counter}")
                else:
                    renderer.handle_key(event.key)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not game.game_over:
                    action = renderer.handle_click(event.pos)
                    if action == 'end_turn' and not renderer.ai_turn_active:
                        _end_player_turn(game, renderer)
                    elif action == 'save_game':
                        _save_game(game, renderer)
                    elif action == 'load_game':
                        _load_game(game, renderer)

        renderer.update(dt)
        renderer.draw()
        pygame.display.flip()

    pygame.quit()
    sys.exit()


def _save_game(game: GameState, renderer: Renderer) -> None:
    try:
        save_game(game, 'data/saves/slot1.json')
        renderer.battle_report = {
            "ok": True,
            "winner": "save",
            "region": "slot1",
            "move_info": "Игра сохранена",
        }
        renderer.battle_report_timer = 1500
    except Exception as e:
        renderer.battle_report = {
            "ok": False,
            "reason": f"Ошибка сохранения: {e}",
        }
        renderer.battle_report_timer = 3000

def _load_game(game: GameState, renderer: Renderer) -> None:
    """Загружает игру. Возвращает новый GameState."""
    try:
        loaded = load_game('data/saves/slot1.json')
    except Exception as e:
        renderer.battle_report = {
            "ok": False,
            "reason": f"Ошибка загрузки: {e}",
        }
        renderer.battle_report_timer = 3000
        return game

    # Обновляем все ссылки
    renderer.game = loaded
    renderer.actions.game = loaded
    renderer.reset_state()

    renderer.battle_report = {
        "ok": True,
        "winner": "load",
        "region": "slot1",
        "move_info": "Игра загружена",
    }
    renderer.battle_report_timer = 1500

    return loaded
def _end_player_turn(game: GameState, renderer: Renderer) -> None:
    game.end_turn()
    renderer.reset_state()

    current = game.current_player()
    if current.is_ai:
        renderer.start_ai_turn(game)


if __name__ == '__main__':
    main()
