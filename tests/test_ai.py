"""Тесты ИИ: планировщик и исполнитель."""

from core.ai import ai_plan, execute_action


def test_ai_plan_returns_list(simple_game):
    """План ИИ — список действий."""
    plan = ai_plan(simple_game, "greece")
    assert isinstance(plan, list)


def test_ai_attacks_weak_neighbor(simple_game):
    """ИИ атакует, если у него перевес.

    В Афинах гарнизон (pop 4 * 5 * 1.5 * 1.2 = 36).
    Дадим Греции армию с атакой > 36 * 1.5 = 54.
    """
    from core.army import Army
    greek = Army(id="army_gr_big", owner="greece", location="athens")
    greek.add_units("Гетайры", 10)  # attack = 70
    simple_game.armies["army_gr_big"] = greek
    simple_game.players["greece"].armies.append("army_gr_big")

    # Убираем македонскую армию, чтобы Греция не боялась ответа    del simple_game.armies["army_mac_1"]

    # Ставим thessaly без защиты, но с армией — нет, thessaly принадлежит
    # Македонии. Атака на thessaly: defender = pop 2*5=10 * 1.0 (равнина) = 10.
    # 70 > 10 * 1.5 — да, ИИ должен атаковать.
    plan = ai_plan(simple_game, "greece")
    attacks = [a for a in plan if a["type"] == "attack"]
    assert len(attacks) >= 1
    assert attacks[0]["target"] == "thessaly"


def test_ai_does_not_attack_strong_neighbor(simple_game):
    """ИИ не атакует, если перевеса нет."""
    # У Греции нет армии — атаковать нечем
    plan = ai_plan(simple_game, "greece")
    attacks = [a for a in plan if a["type"] == "attack"]
    assert len(attacks) == 0


def test_ai_execute_attack(simple_game):
    """execute_action выполняет атаку и возвращает лог."""
    from core.army import Army
    greek = Army(id="army_gr_big", owner="greece", location="athens")
    greek.add_units("Гетайры", 10)
    simple_game.armies["army_gr_big"] = greek
    simple_game.players["greece"].armies.append("army_gr_big")

    result = execute_action(simple_game, {
        "type": "attack",
        "army": "army_gr_big",
        "target": "thessaly",
    })

    assert result["ok"] is True
    assert result["type"] == "attack"
    assert "text" in result