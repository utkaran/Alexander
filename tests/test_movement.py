"""Тесты перемещения армий."""

from core.army import Army


def test_move_to_own_region(simple_game):
    """Перемещение в свой соседний регион."""
    result = simple_game.move_army("army_mac_1", "pella")

    assert result["ok"] is True
    assert result["merged"] is False
    assert simple_game.armies["army_mac_1"].location == "pella"
    assert simple_game.armies["army_mac_1"].has_acted is True


def test_move_merges_armies(simple_game):
    """Перемещение в регион со своей армией — объединение."""
    # Ставим вторую армию в pella
    second = Army(id="army_mac_2", owner="macedonia", location="pella")
    second.add_units("Фаланга", 2)
    simple_game.armies["army_mac_2"] = second
    simple_game.players["macedonia"].armies.append("army_mac_2")

    result = simple_game.move_army("army_mac_1", "pella")

    assert result["ok"] is True
    assert result["merged"] is True
    # army_mac_1 удалена, юниты перешли в army_mac_2
    assert "army_mac_1" not in simple_game.armies
    assert simple_game.armies["army_mac_2"].units["Фаланга"] == 5  # 3 + 2
    assert simple_game.armies["army_mac_2"].units["Гетайры"] == 1


def test_move_carries_alexander(simple_game):
    """При объединении Александр переносится в целевую армию."""
    simple_game.armies["army_mac_1"].alexander_attached = True

    second = Army(id="army_mac_2", owner="macedonia", location="pella")
    second.add_units("Фаланга", 2)
    simple_game.armies["army_mac_2"] = second
    simple_game.players["macedonia"].armies.append("army_mac_2")

    simple_game.move_army("army_mac_1", "pella")

    assert simple_game.armies["army_mac_2"].alexander_attached is True


def test_move_to_enemy_region_forbidden(simple_game):
    """Перемещение в чужой регион запрещено (только атака)."""
    result = simple_game.move_army("army_mac_1", "athens")
    assert result["ok"] is False
    assert "не ваш" in result["reason"].lower() or "атакуйте" in result["reason"].lower()


def test_move_to_non_neighbor_forbidden(simple_game):
    """Перемещение в несоседний регион запрещено."""
    second = Army(id="army_mac_2", owner="macedonia", location="pella")
    second.add_units("Фаланга", 2)
    simple_game.armies["army_mac_2"] = second
    simple_game.players["macedonia"].armies.append("army_mac_2")

    result = simple_game.move_army("army_mac_2", "athens")
    assert result["ok"] is False


def test_move_already_acted_forbidden(simple_game):
    """Армия, которая уже действовала, не может двигаться."""
    simple_game.armies["army_mac_1"].has_acted = True
    result = simple_game.move_army("army_mac_1", "pella")
    assert result["ok"] is False