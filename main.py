from core.game import GameState
from core.army import Army
from core.ai import ai_turn


def print_map(game: GameState) -> None:
    print('\n=== КАРТА ===')
    for region in game.regions.values():
        owner = game.players[region.owner].name if region.owner else 'нейтрал'
        print(f' {region.name:15} | {owner:12} | доход: {region.income} | соседи: {", ".join(region.neighbors)}')


def main() -> None:
    game = GameState()
    game.load_map('data/map_act1.json')

    # Стартовая армия Македонии
    army = Army(id='army1', owner='macedonia', location='pella')
    army.add_units('Фаланга', 5)
    army.add_units('Гетайры', 2)
    army.alexander_attached = True
    game.armies[army.id] = army

    game.start('macedonia')
    print_map(game)

    # Атака Фракии
    print("\n=== АТАКА ФРАКИИ ===")
    result = game.attack('army1', 'thrace')
    print(result)
    print(f"Армия после боя: {army}")

    # Найм
    print("\n=== НАЙМ ===")
    result = game.recruit("macedonia", "pella", "Фаланга", 2)
    print(result)
    print(f"Золото Македонии: {game.players['macedonia'].gold}")

    # Игровой цикл с ИИ
    print("\n=== ИГРОВОЙ ЦИКЛ С ИИ ===")
    max_turns = 9
    for _ in range(max_turns):
        current = game.current_player()
        if current.id == "macedonia":
            game.end_turn()
            continue

        print(f"\n--- Ход {current.name} (раунд {game.turn}) ---")
        actions = ai_turn(game, current.id)
        for a in actions:
            print(f"  {a}")
        game.end_turn()

    print_map(game)
    print(f"\nИтог: {game}")


if __name__ == '__main__':
    main()