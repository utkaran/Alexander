"""Тесты сериализации: to_dict / from_dict для всех классов."""

from core.army import Army
from core.region import Region
from core.player import Player
from core.alexander_state import AlexanderState
from core.game import GameState, SAVED_GAME_FIELDS


def test_army_to_dict_round_trip():
    """Army.to_dict → Army.from_dict возвращает эквивалентную армию."""
    army = Army(id="a1", owner="macedonia", location="pella")
    army.add_units("Фаланга", 3)
    army.add_units("Гетайры", 1)
    army.morale = 80
    army.alexander_attached = True
    army.has_acted = True
    army.is_garrison = False
    army.is_revolt = False

    d = army.to_dict()
    restored = Army.from_dict(d)

    assert restored == army


def test_army_to_dict_has_all_dataclass_fields():
    """Army.to_dict содержит все поля датакласса. Если нет — забыл добавить."""
    import dataclasses
    army = Army(id="a1", owner="m", location="p")
    expected = {f.name for f in dataclasses.fields(Army)}
    actual = set(army.to_dict().keys())
    missing = expected - actual
    assert not missing, f"Army.to_dict() не содержит поля: {missing}"

def test_region_to_dict_round_trip():
    region = Region(
        id="r1", name="Пелла", terrain="равнина",
        owner="macedonia", income=3, population=3,
        neighbors=["a", "b"], is_capital=True,
        x=100.0, y=200.0, supply=3,
        garrison_army={"Фаланга": 2},
        story_goal="test_scene",
        original_owner="macedonia",
        is_protected=False,
    )
    d = region.to_dict()
    restored = Region.from_dict(d)
    assert restored == region


def test_region_to_dict_has_all_dataclass_fields():
    import dataclasses
    region = Region(id="r1", name="R")
    expected = {f.name for f in dataclasses.fields(Region)}
    actual = set(region.to_dict().keys())
    missing = expected - actual
    assert not missing, f"Region.to_dict() не содержит поля: {missing}"

def test_player_to_dict_round_trip():
    player = Player(
        id="m", name="Македония", gold=100, food=50,
        reputation=10, is_ai=False, color=(200, 150, 50),
        regions=["pella"], armies=["a1"],
    )
    d = player.to_dict()
    restored = Player.from_dict(d)
    assert restored == player


def test_player_to_dict_has_all_dataclass_fields():
    import dataclasses
    player = Player(id="p", name="P")
    expected = {f.name for f in dataclasses.fields(Player)}
    actual = set(player.to_dict().keys())
    missing = expected - actual
    assert not missing, f"Player.to_dict() не содержит поля: {missing}"

def test_alexander_state_to_dict_round_trip():
    a = AlexanderState(exhaustion=30, health=80, perks=["a", "b"])
    d = a.to_dict()
    restored = AlexanderState.from_dict(d)
    assert restored == a


def test_alexander_state_to_dict_has_all_dataclass_fields():
    import dataclasses
    a = AlexanderState()
    expected = {f.name for f in dataclasses.fields(AlexanderState)}
    actual = set(a.to_dict().keys())
    missing = expected - actual
    assert not missing, f"AlexanderState.to_dict() не содержит поля: {missing}"

def test_game_to_dict_has_all_saved_fields(simple_game):
    """to_dict содержит все поля из SAVED_GAME_FIELDS."""
    d = simple_game.to_dict()
    actual = set(d.keys())
    expected = set(SAVED_GAME_FIELDS) | {"regions", "players", "armies", "alexander"}
    missing = expected - actual
    assert not missing, f"GameState.to_dict() не содержит: {missing}"


def test_game_to_dict_round_trip(simple_game):
    """GameState.to_dict → GameState.from_dict возвращает эквивалент."""
    d = simple_game.to_dict()
    restored = GameState.from_dict(d)

    assert restored.turn == simple_game.turn
    assert restored.current_player_id == simple_game.current_player_id
    assert restored.current_act == simple_game.current_act
    assert restored.objectives_complete == simple_game.objectives_complete
    assert restored.revolt_timers == simple_game.revolt_timers
    assert set(restored.regions.keys()) == set(simple_game.regions.keys())
    assert set(restored.players.keys()) == set(simple_game.players.keys())
    assert set(restored.armies.keys()) == set(simple_game.armies.keys())