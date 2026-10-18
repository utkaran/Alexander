"""Тесты цепочки целей."""

from core.objectives import ACT1_CHAIN, get_chain, is_objective_complete


def test_act1_chain_order():
    """Порядок целей Акта I фиксирован: Фивы → Афины → Спарта → Геллеспонт."""
    ids = [o.id for o in ACT1_CHAIN]
    assert ids == ["thebes", "athens", "sparta", "hellespont"]


def test_get_chain_act1():
    assert get_chain(1) is ACT1_CHAIN


def test_get_chain_act2_empty_for_now():
    """Акт II пока без целей — вернётся пустой список."""
    assert get_chain(2) == []


def test_objective_complete(simple_game):
    """Цель выполнена, когда регион принадлежит Македонии."""
    thebes = next(o for o in ACT1_CHAIN if o.id == "thebes")
    # В simple_game Фив нет — цель не выполнена
    assert is_objective_complete(thebes, simple_game) is False


def test_objective_complete_when_owned(simple_game):
    """Если регион македонский — цель выполнена."""
    from core.region import Region
    simple_game.regions["thebes"] = Region(
        id="thebes", name="Фивы", terrain="равнина",
        owner="macedonia", income=2, population=3,
        neighbors=["athens"], x=0, y=0,
    )
    thebes = next(o for o in ACT1_CHAIN if o.id == "thebes")
    assert is_objective_complete(thebes, simple_game) is True


def test_objective_rewards():
    """Награды соответствуют доку (10/15/10/20 золота)."""
    rewards = {o.id: o.reward_gold for o in ACT1_CHAIN}
    assert rewards == {"thebes": 10, "athens": 15, "sparta": 10, "hellespont": 20}

def test_capture_objective_completes_and_rewards(simple_game):
    """Захват Фив завершает цель и даёт золото."""
    from core.region import Region
    # Делаем Фивы соседом Фессалии, чтобы можно было атаковать
    simple_game.regions["thessaly"].neighbors.append("thebes")
    simple_game.regions["thebes"] = Region(
        id="thebes", name="Фивы", terrain="равнина",
        owner="greece", income=2, population=1,
        neighbors=["thessaly"], x=0, y=0,
    )
    simple_game.players["greece"].regions.append("thebes")

    gold_before = simple_game.players["macedonia"].gold
    simple_game.attack("army_mac_1", "thebes")

    assert "thebes" in simple_game.objectives_complete
    assert simple_game.current_objective_index == 1
    assert simple_game.players["macedonia"].gold == gold_before + 10


def test_current_objective_advances(simple_game):
    """После выполнения Фив текущая цель — Афины."""
    from core.region import Region
    simple_game.regions["thessaly"].neighbors.append("thebes")
    simple_game.regions["thebes"] = Region(
        id="thebes", name="Фивы", terrain="равнина",
        owner="greece", income=2, population=1,
        neighbors=["thessaly"], x=0, y=0,
    )
    simple_game.players["greece"].regions.append("thebes")
    simple_game.attack("army_mac_1", "thebes")

    obj = simple_game.current_objective()
    assert obj is not None
    assert obj.id == "athens"


def test_current_objective_none_when_done(simple_game):
    """Когда все цели выполнены — current_objective возвращает None."""
    simple_game.current_objective_index = 4  # len(ACT1_CHAIN)
    assert simple_game.current_objective() is None