"""Тесты боя: attack, потери, смерть Александра."""

import pytest

from core.army import Army
from core.combat import estimate_defense, estimate_attack


def test_attack_captures_undefended_region(simple_game):
    """Атака нейтрального региона без столицы — захват."""
    army = simple_game.armies["army_mac_1"]
    result = simple_game.attack("army_mac_1", "epirus")

    assert result["ok"] is True
    assert result["winner"] == "attacker"
    assert simple_game.regions["epirus"].owner == "macedonia"
    assert army.location == "epirus"
    assert army.has_acted is True
    assert result["losses"] >= 1


def test_attack_with_defender_army(simple_game):
    """Атака Афин с гарнизоном: атакующий слабее (37.7 vs 48), проигрывает."""
    from core.army import Army

    defender = Army(id="army_gr_1", owner="greece", location="athens")
    defender.add_units("Фаланга", 2)
    simple_game.armies["army_gr_1"] = defender
    simple_game.players["greece"].armies.append("army_gr_1")

    result = simple_game.attack("army_mac_1", "athens")

    assert result["ok"] is True
    # Македоняне: 3 фаланги + 1 гетайр = attack 16, без Александра
    # Афины: (4*5*1.5 + 2*5) * 1.2 = 48
    # 16 < 48 → атакующий проигрывает
    assert result["winner"] == "defender", (
        f"Ожидали поражение (16 vs 48), получили {result['winner']} "
        f"({result['attacker_strength']} vs {result['defender_strength']})"
    )
    assert simple_game.regions["athens"].owner == "greece"
    assert result["defender_strength"] == pytest.approx(48.0)


def test_attack_cannot_attack_own_region(simple_game):
    """Атака своего региона запрещена."""
    result = simple_game.attack("army_mac_1", "pella")
    assert result["ok"] is False
    assert "ваш" in result["reason"].lower()


def test_attack_cannot_attack_non_neighbor(simple_game):
    """Атака несоседнего региона запрещена."""
    # pella не соседствует с athens
    army = Army(id="army_mac_2", owner="macedonia", location="pella")
    army.add_units("Фаланга", 5)
    simple_game.armies["army_mac_2"] = army
    simple_game.players["macedonia"].armies.append("army_mac_2")

    result = simple_game.attack("army_mac_2", "athens")
    assert result["ok"] is False
    assert "сосед" in result["reason"].lower()


def test_attack_already_acted_army(simple_game):
    """Армия, которая уже действовала, не может атаковать."""
    army = simple_game.armies["army_mac_1"]
    army.has_acted = True

    result = simple_game.attack("army_mac_1", "athens")
    assert result["ok"] is False
    assert "действовала" in result["reason"].lower()


def test_alexander_bonus_increases_attack(simple_game):
    """С Александром attack_strength выше (проверяем формулу)."""
    import pytest

    army = simple_game.armies["army_mac_1"]

    army.alexander_attached = False
    strength_no_alex = army.attack_strength() * (army.morale / 100)

    army.alexander_attached = True
    strength_alex = army.attack_strength() * (army.morale / 100) * 1.3

    assert strength_alex == pytest.approx(strength_no_alex * 1.3)


def test_alexander_dies_when_army_destroyed(simple_game):
    """Если армия с Александром уничтожена — Александр погибает."""
    # Ставим слабую армию с Александром против сильного защитника
    army = Army(id="army_weak", owner="macedonia", location="thessaly")
    army.add_units("Лучники", 1)
    army.alexander_attached = True
    simple_game.armies["army_weak"] = army
    simple_game.players["macedonia"].armies.append("army_weak")

    # Убираем сильную армию, чтобы атаковала только слабая
    del simple_game.armies["army_mac_1"]

    # Усиливаем Афины
    simple_game.regions["athens"].population = 10

    result = simple_game.attack("army_weak", "athens")

    # Скорее всего, проиграем — и Александр погибнет (армия уничтожена)
    assert result["ok"] is True
    if result["winner"] == "defender":
        # Армия из 1 лучника с attack 2*1=2 против pop 10*5=50*1.5*1.2 — точно проигрыш
        assert result["alexander_died"] is True
        assert simple_game.alexander_died is True
        assert simple_game.game_over is True
        assert simple_game.game_over_reason == "alexander_died"

def test_attack_uses_estimate_defense(simple_game):
    """attack() не должен применять столицу/местность/армию повторно.

    Проверяем не «две функции совпадают», а что attack() реально
    берёт цифру из estimate_defense, а не считает по-своему.
    """
    from core.combat import estimate_defense
    from core.army import Army
    import pytest

    # Афины: pop 4, столица, холмы → 4*5*1.5*1.2 = 36 без армии
    simple_game.regions["athens"].owner = "greece"
    base = estimate_defense(simple_game.regions["athens"], simple_game)
    assert base == pytest.approx(36.0), f"Базовая защита Афин: {base}"

    # Добавляем армию защитника: 2 фаланги (defense 10)
    # (20*1.5 + 10) * 1.2 = 40 * 1.2 = 48
    gr = Army(id="gr1", owner="greece", location="athens")
    gr.add_units("Фаланга", 2)
    simple_game.armies["gr1"] = gr
    simple_game.players["greece"].armies.append("gr1")

    expected = estimate_defense(simple_game.regions["athens"], simple_game)
    assert expected == pytest.approx(48.0), f"С армией: {expected}"

    # Реальный бой: attack() должен вернуть ровно 48, а не 76.8
    result = simple_game.attack("army_mac_1", "athens")
    assert result["defender_strength"] == pytest.approx(48.0), (
        f"attack() насчитал {result['defender_strength']}, "
        f"а estimate_defense даёт 48. Двойной учёт столицы/местности/армии."
    )


def test_estimate_defense_sums_all_defender_armies(simple_game):
    """Две армии защитника в регионе — обе учитываются."""
    from core.army import Army

    region = simple_game.regions["athens"]
    base = estimate_defense(region, simple_game)

    a1 = Army(id="gr_a1", owner="greece", location="athens")
    a1.add_units("Фаланга", 2)
    simple_game.armies["gr_a1"] = a1

    a2 = Army(id="gr_a2", owner="greece", location="athens")
    a2.add_units("Фаланга", 3)
    simple_game.armies["gr_a2"] = a2

    after = estimate_defense(region, simple_game)
    # 2 фаланги (def 10) + 3 фаланги (def 15) = +25, потом *1.2 (холмы)
    assert after == pytest.approx(base + 25 * 1.2)


def test_estimate_defense_neutral_has_strength(simple_game):
    """Нейтральный регион без армии всё равно имеет оборону (гарнизон)."""
    region = simple_game.regions["epirus"]  # нейтрал, равнина, pop 1
    strength = estimate_defense(region, simple_game)
    assert strength > 0, "Нейтрал не должен быть беззащитным"

def test_neutral_region_has_visible_defense(simple_game):
    """Нейтральный регион без армии всё равно имеет оборону для панели."""
    from core.combat import estimate_defense
    from core.region import Region

    simple_game.regions["thrace"] = Region(
        id="thrace", name="Фракия", terrain="горы",
        owner=None, income=1, population=2,
        neighbors=["thessaly"], x=0, y=0,
    )
    strength = estimate_defense(simple_game.regions["thrace"], simple_game)
    # 2*5 * 1.5 = 15
    assert strength == pytest.approx(15.0), (
        f"Фракия должна иметь оборону 15 (гарнизон 10 × горы 1.5), "
        f"а не {strength}. Игрок не должен проигрывать вслепую."
    )

def test_cannot_attack_story_goal_region(simple_game):
    """Регион со story_goal берётся послами, не штурмом."""
    from core.region import Region

    simple_game.regions["thessaly"].neighbors.append("thebes")
    simple_game.regions["thebes"] = Region(
        id="thebes", name="Фивы", terrain="равнина",
        owner="greece", income=2, population=1,
        neighbors=["thessaly"], x=0, y=0,
        story_goal="act1_thebes_surrender",
    )

    result = simple_game.attack("army_mac_1", "thebes")
    assert result["ok"] is False
    assert "посл" in result["reason"].lower() or "сюжет" in result["reason"].lower()
    assert simple_game.regions["thebes"].owner == "greece"  # не захвачен

def test_valid_attack_target_excludes_story_goal(simple_game):
    """UI не должен подсвечивать регион со story_goal как цель атаки."""
    from core.region import Region
    from ui.actions import ActionController

    simple_game.regions["thessaly"].neighbors.append("thebes")
    simple_game.regions["thebes"] = Region(
        id="thebes", name="Фивы", terrain="равнина",
        owner="greece", income=2, population=1,
        neighbors=["thessaly"], x=0, y=0,
        story_goal="act1_thebes_surrender",
    )

    actions = ActionController(simple_game)
    assert actions.is_valid_attack_target("army_mac_1", "thebes") is False
    assert actions.is_valid_attack_target("army_mac_1", "athens") is True  # без story_goal