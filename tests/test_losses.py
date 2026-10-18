"""Тесты распределения потерь в _apply_losses."""

from core.army import Army


def test_losses_do_not_kill_rare_unit_first():
    """1 гетайр + 10 фаланг, потеря 1 юнита — гетайр не должен умирать первым.

    Пропорционально гетайру полагается 1/11 ≈ 0.09 потери.
    Значит, умереть должен кто-то из фаланг (их 10/11 ≈ 0.9).
    """
    army = Army(id="a", owner="macedonia", location="pella")
    army.add_units("Гетайры", 1)
    army.add_units("Фаланга", 10)

    # Вызываем _apply_losses через GameState (это приватный метод, но тест — белый ящик)
    from core.game import GameState
    game = GameState()
    game._apply_losses(army, 1)

    # Гетайр должен выжить, фаланг стало 9
    assert army.units.get("Гетайры", 0) == 1, "Гетайр не должен умирать при потере 1 из 11"
    assert army.units.get("Фаланга", 0) == 9, "Должна умереть одна фаланга"


def test_losses_are_exact():
    """Потери должны быть ровно total_losses, если армия достаточно велика."""
    army = Army(id="a", owner="macedonia", location="pella")
    army.add_units("Фаланга", 10)

    from core.game import GameState
    game = GameState()
    game._apply_losses(army, 4)

    assert army.total_count() == 6, f"Ожидали 6 юнитов, осталось {army.total_count()}"


def test_losses_never_exceed_army_size():
    """Нельзя потерять больше, чем есть."""
    army = Army(id="a", owner="macedonia", location="pella")
    army.add_units("Фаланга", 2)
    army.add_units("Лучники", 1)

    from core.game import GameState
    game = GameState()
    game._apply_losses(army, 100)

    assert army.is_empty(), "Армия должна быть уничтожена"
    assert army.total_count() == 0