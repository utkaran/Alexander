"""Боевые формулы. ЕДИНЫЙ источник правды для game.py и ai.py.

Почему отдельный файл: attack() и ai._estimate_defense() считали
защиту по-разному (порядок умножения на местность + только первая
армия защитника). Это ломало оценку ИИ. Теперь одна функция.
"""

from core.constants import (
    GARRISON_PER_POP,
    CAPITAL_DEFENSE_BONUS,
    TERRAIN_BONUS,
    ALEXANDER_ATTACK_BONUS
)

def estimate_defense(region, game) -> float:
    """

    Формула:
      (population * GARRISON_PER_POP * [столица] + defense всех армий)
      * бонус местности

    Важно: местность умножается ПОСЛЕ добавления армий.
    Иначе бонус местности не действует на армию защитника —
    а он должен, защитник обороняется В местности.
    """

    strength = region.population * GARRISON_PER_POP
    if region.is_capital:
        strength *= CAPITAL_DEFENSE_BONUS

        # Суммируем ВСЕ армии защитника, не только первую
    defender_owner = region.owner if region.owner else "neutral"
    for army in game.armies.values():
        if (army.owner == defender_owner
                and army.location == region.id
                and not army.is_empty()):
            strength += army.defense_strength()

    strength *= TERRAIN_BONUS.get(region.terrain.lower(), 1.0)
    return strength

def estimate_attack(army) -> float:
    """Сила атаки армии с учётом морали и Александра."""
    strength = army.attack_strength() * (army.morale / 100)
    if army.alexander_attached:
        strength *= ALEXANDER_ATTACK_BONUS
    return strength