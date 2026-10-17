"""Общие фикстуры для тестов core/."""

import pytest

from core.game import GameState
from core.player import Player
from core.region import Region
from core.army import Army


@pytest.fixture
def empty_game() -> GameState:
    """Пустая игра без карты — для юнит-тестов отдельных механик."""
    return GameState()


@pytest.fixture
def simple_game() -> GameState:
    """Мини-карта: 3 региона, 2 игрока, 1 армия.

    pella (macedonia) -- thessaly (macedonia) -- athens (greece)
    """
    game = GameState()

    game.regions["pella"] = Region(
        id="pella", name="Пелла", terrain="равнина",
        owner="macedonia", income=3, population=3,
        neighbors=["thessaly"], is_capital=True,
        x=0, y=0,
    )
    game.regions["thessaly"] = Region(
        id="thessaly", name="Фессалия", terrain="равнина",
        owner="macedonia", income=2, population=2,
        neighbors=["pella", "athens", "epirus"], x=100, y=0,
    )
    game.regions["athens"] = Region(
        id="athens", name="Афины", terrain="холмы",
        owner="greece", income=3, population=4,
        neighbors=["thessaly"], is_capital=True,
        x=200, y=0,
    )
    game.regions["epirus"] = Region(
        id="epirus", name="Эпир", terrain="равнина",
        owner=None, income=1, population=1,
        neighbors=["thessaly"], x=50, y=50,
    )

    game.players["macedonia"] = Player(
        id="macedonia", name="Македония", gold=100,
        color=(200, 150, 50), regions=["pella", "thessaly"],
    )
    game.players["greece"] = Player(
        id="greece", name="Греция", gold=50, is_ai=True,
        color=(80, 120, 200), regions=["athens"],
    )

    army = Army(id="army_mac_1", owner="macedonia", location="thessaly")
    army.add_units("Фаланга", 3)
    army.add_units("Гетайры", 1)
    game.armies[army.id] = army
    game.players["macedonia"].armies.append(army.id)

    game.start("macedonia")
    return game


@pytest.fixture
def greek_army_game(simple_game) -> GameState:
    """Та же карта, но в Афинах стоит греческая армия (для тестов обороны)."""
    greece_army = Army(id="army_gr_1", owner="greece", location="athens")
    greece_army.add_units("Фаланга", 2)
    simple_game.armies[greece_army.id] = greece_army
    simple_game.players["greece"].armies.append(greece_army.id)
    return simple_game

