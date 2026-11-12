import pytest
def test_garrison_created_from_json():
    """load_map создаёт армию-гарнизон из garrison_army."""
    from core.game import GameState
    from core.region import Region

    game = GameState()
    game.regions["thrace"] = Region(
        id="thrace", name="Фракия", terrain="горы",
        owner=None, population=2, x=0, y=0,
        garrison_army={"Фаланга": 2, "Лучники": 1},
    )
    game._spawn_garrison_for(game.regions["thrace"])

    assert "army_garrison_thrace" in game.armies
    garrison = game.armies["army_garrison_thrace"]
    assert garrison.units["Фаланга"] == 2
    assert garrison.units["Лучники"] == 1
    assert garrison.owner == "neutral"


def test_neutral_garrison_counts_in_defense():
    """Гарнизон нейтрала учитывается в estimate_defense."""
    from core.game import GameState
    from core.region import Region
    from core.combat import estimate_defense

    game = GameState()
    game.regions["thrace"] = Region(
        id="thrace", name="Фракия", terrain="горы",
        owner=None, population=2, x=0, y=0,
        garrison_army={"Фаланга": 2, "Лучники": 1},
    )
    game._spawn_garrison_for(game.regions["thrace"])

    defense = estimate_defense(game.regions["thrace"], game)
    # (2*5 + 2*5 + 1*1) * 1.5 = (10 + 10 + 1) * 1.5 = 31.5
    assert defense == pytest.approx(31.5), f"Оборона Фракии: {defense}"


def test_neutral_garrison_defends_and_is_destroyed_on_capture(simple_game):
    from core.region import Region
    from core.combat import estimate_defense

    simple_game.regions["thrace"] = Region(
        id="thrace", name="Фракия", terrain="горы",
        owner=None, population=2, x=0, y=0,
        neighbors=["pella"],  # ← Фракия рядом с Пеллой
        garrison_army={"Фаланга": 2, "Лучники": 1}
    )
    simple_game.regions["pella"].neighbors.append("thrace")

    simple_game._spawn_garrison_for(simple_game.regions["thrace"])

    # Переставляем армию в Пеллу, чтобы она соседила с Фракией
    simple_game.armies["army_mac_1"].location = "pella"

    defense = estimate_defense(simple_game.regions["thrace"], simple_game)
    assert defense == pytest.approx(31.5)

    result = simple_game.attack("army_mac_1", "thrace")
    assert result["ok"] is True, f"Бой не начался: {result.get('reason')}"
    assert result["winner"] == "defender"
    assert result["had_defender_army"] is True

    simple_game.armies["army_mac_1"].add_units("Гетайры", 10)
    simple_game.armies["army_mac_1"].has_acted = False
    result = simple_game.attack("army_mac_1", "thrace")

    assert result["ok"] is True
    assert result["winner"] == "attacker"
    assert "army_garrison_thrace" not in simple_game.armies
    assert simple_game.regions["thrace"].owner == "macedonia"

def test_region_from_dict_has_all_fields():
    """_region_from_dict заполняет все поля Region."""
    from core.game import GameState
    game = GameState()
    r = game._region_from_dict({
        "id": "test", "name": "Тест", "terrain": "горы",
        "owner": "macedonia", "income": 3, "population": 4,
        "neighbors": ["a"], "is_capital": True,
        "garrison_army": {"Фаланга": 2},
        "story_goal": "test_scene",
    })
    assert r.id == "test"
    assert r.terrain == "горы"
    assert r.owner == "macedonia"
    assert r.is_capital is True
    assert r.garrison_army == {"Фаланга": 2}
    assert r.story_goal == "test_scene"
    assert r.original_owner == "macedonia"