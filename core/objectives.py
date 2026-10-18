"""Цепочка сюжетных целей Акта I.

Чистая логика без pygame. GameState хранит current_objective_index,
а модуль знает, какие цели, в каком порядке и с какими наградами.

Цель считается выполненной, когда регион захвачен (owner == 'macedonia').
Пропуск цели (игрок ушёл вперёд) — отдельная механика, см. Этап 4.5 unrest.
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class Objective:
    id: str # 'thebes', 'athens', 'sparta', 'hellespont'
    title: str # 'Подавить восстание в Фивах'
    region_id: str # какой регион надо захватить
    reward_gold: int = 0
    reward_glory: int = 0 # задел на Этап 6 (очки славы), пока не используется

# Цепочка Акта I — порядок важен
ACT1_CHAIN: list[Objective] = [
    Objective(
        id='thebes',
        title="Подавить восстание в Фивах",
        region_id='thebes',
        reward_gold=10,
        reward_glory=1,
    ),
Objective(
        id="athens",
        title="Привести Афины к покорности",
        region_id="athens",
        reward_gold=15,
        reward_glory=2,
    ),
    Objective(
        id="sparta",
        title="Добиться нейтралитета Спарты",
        region_id="sparta",
        reward_gold=10,
        reward_glory=1,
    ),
    Objective(
        id="hellespont",
        title="Переправиться через Геллеспонт",
        region_id="hellespont",
        reward_gold=20,
        reward_glory=3,
    ),
]

def get_chain(act: int) -> list[Objective]:
    """Цепочка целей для акта. Пока только Акт I."""
    if act == 1:
        return ACT1_CHAIN
    return []

def is_objective_complete(objective: Objective, game) -> bool:
    """Выполнена ли цель: регион принадлежит Македонии."""
    region = game.regions.get(objective.region_id)
    return region is not None and region.owner == 'macedonia'