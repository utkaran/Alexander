def test_set_region_owner_removes_defender_armies(simple_game):
    """set_region_owner удаляет армии старого владельца."""
    from core.army import Army
    defender = Army(id="gr_def", owner="greece", location="athens")
    defender.add_units("Фаланга", 2)
    simple_game.armies["gr_def"] = defender

    simple_game.set_region_owner("athens", "macedonia")

    assert simple_game.regions["athens"].owner == "macedonia"
    assert "gr_def" not in simple_game.armies


def test_set_region_owner_removes_neutral_garrison(simple_game):
    """set_region_owner удаляет гарнизон нейтрала."""
    from core.army import Army
    garrison = Army(id="garrison_ep", owner="neutral", location="epirus")
    garrison.add_units("Фаланга", 1)
    simple_game.armies["garrison_ep"] = garrison

    simple_game.set_region_owner("epirus", "macedonia")

    assert simple_game.regions["epirus"].owner == "macedonia"
    assert "garrison_ep" not in simple_game.armies


def test_set_region_owner_removes_dead_player(simple_game):
    """Если у старого владельца не осталось регионов — он удаляется."""
    # У Греции только Афины
    simple_game.set_region_owner("athens", "macedonia")
    assert "greece" not in simple_game.players

def test_remove_player_if_dead_cleans_orphan_garrisons(simple_game):
    """Когда фракция умирает, её гарнизоны тоже удаляются."""
    from core.army import Army
    # Гарнизон Греции в Афинах (не в player.armies — как настоящий)
    garrison = Army(id="garrison_athens", owner="greece", location="athens", is_garrison=True)
    garrison.add_units("Фаланга", 2)
    simple_game.armies["garrison_athens"] = garrison

    # Убираем у Греции последний регион — она «мертва»
    simple_game.players["greece"].regions = []
    simple_game._remove_player_if_dead("greece")

    assert "greece" not in simple_game.players
    assert "garrison_athens" not in simple_game.armies, (
        "Гарнизон мёртвой фракции должен быть удалён"
    )