"""Тесты найма."""


def test_recruit_success(simple_game):
    """Найм фаланги: золото списывается, армия растёт."""
    gold_before = simple_game.players["macedonia"].gold
    result = simple_game.recruit("macedonia", "pella", "Фаланга", 1)

    assert result["ok"] is True
    assert simple_game.players["macedonia"].gold == gold_before - 12  # cost Фаланги


def test_recruit_insufficient_gold(simple_game):
    """Найм при нехватке золота — ошибка, золото не списывается."""
    simple_game.players["macedonia"].gold = 5
    result = simple_game.recruit("macedonia", "pella", "Фаланга", 1)

    assert result["ok"] is False
    assert "золота" in result["reason"].lower()
    assert simple_game.players["macedonia"].gold == 5  # не списалось


def test_recruit_not_my_region(simple_game):
    """Найм в чужом регионе запрещён."""
    result = simple_game.recruit("macedonia", "athens", "Фаланга", 1)
    assert result["ok"] is False
    assert "не ваш" in result["reason"].lower()


def test_recruit_creates_new_army(simple_game):
    """Если в регионе нет армии — создаётся новая."""
    # В pella армии нет (только в thessaly)
    result = simple_game.recruit("macedonia", "pella", "Лучники", 1)

    assert result["ok"] is True
    # Появилась армия в pella
    armies_in_pella = [
        a for a in simple_game.armies.values()
        if a.owner == "macedonia" and a.location == "pella"
    ]
    assert len(armies_in_pella) == 1
    assert armies_in_pella[0].units["Лучники"] == 1


def test_recruit_unknown_unit(simple_game):
    """Неизвестный тип юнита — ошибка."""
    result = simple_game.recruit("macedonia", "pella", "Драконы", 1)
    assert result["ok"] is False
    assert "нет такого" in result["reason"].lower()