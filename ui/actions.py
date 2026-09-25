"""Контроллер действий игрока: атака, движение, найм.

Не знает ничего о Pygame и рисовании.
Возвращает простые результаты — рендерер решает, как их показать.
"""

from core.game import GameState
from core.constants import UNIT_STATS

class ActionController:
    def __init__(self, game: GameState) -> None:
        self.game = game

    # ПОИСК АРМИИ

    def get_army_in_region(self, region_id: str) -> str | None:
        # ID армии текущего игрока в регионе (или None).
        current_player_id = self.game.current_player_id
        for army in self.game.armies.values():
            if (army.owner == current_player_id
                    and army.location == region_id
                    and not army.is_empty()):
                return army.id
        return None

    def get_army_strength_in_region(self, region_id: str) -> float:
        # Суммарная сила всех армий текущего игрока в регионе.
        total = 0.0
        current_player_id = self.game.current_player_id
        for army in self.game.armies.values():
            if army.owner == current_player_id and army.location == region_id:
                total += army.total_strength()
        return total

    # АТАКА

    def can_attack_from(self, region_id: str) -> bool:
        """Может ли текущий игрок атаковать из этого региона."""
        return self.get_army_in_region(region_id) is not None

    def is_valid_attack_target(self, attacker_army_id: str, region_id: str) -> bool:
        """Можно ли атаковать регион этой армией."""
        army = self.game.armies.get(attacker_army_id)
        if not army:
            return False

        region = self.game.regions.get(region_id)
        if not region:
            return False

        if region.owner == army.owner:
            return False

        attacker_region = self.game.regions.get(army.location)
        if not attacker_region:
            return False

        if region_id not in attacker_region.neighbors:
            return False

        return True

    def execute_attack(self, attacker_army_id: str, target_region_id: str) -> dict:
        """Выполняет атаку. Возвращает результат боя."""
        return self.game.attack(attacker_army_id, target_region_id)

    # ПЕРЕМЕЩЕНИЕ

    def is_valid_move_target(self, moving_army_id: str, region_id: str) -> bool:
        """Можно ли двигать армию в этот регион."""
        army = self.game.armies.get(moving_army_id)
        if not army:
            return False

        region = self.game.regions.get(region_id)
        if not region:
            return False

        if region_id == army.location:
            return False

        current = self.game.regions.get(army.location)
        if not current:
            return False

        if region_id not in current.neighbors:
            return False

        return True

    def execute_move(self, moving_army_id: str, target_region_id: str) -> dict:
        """Выполняет перемещение. Возвращает результат."""
        return self.game.move_army(moving_army_id, target_region_id)

    # НАЙМ

    def is_my_region(self, region_id: str) -> bool:
        """Принадлежит ли регион текущему игроку."""
        region = self.game.regions.get(region_id)
        return region is not None and region.owner == self.game.current_player_id

    def can_recruit_in(self, region_id: str) -> bool:
        """Можно ли нанимать в этом регионе."""
        return self.is_my_region(region_id)

    def execute_recruit(self, region_id: str, unit_type: str, count: int = 1) -> dict:
        """Нанимает юниты в регионе."""
        return self.game.recruit(
            self.game.current_player_id,
            region_id,
            unit_type,
            count,
        )

    def unit_cost(self, unit_type: str) -> int:
        """Стоимость одного юнита."""
        stats = UNIT_STATS.get(unit_type)
        return stats["cost"] if stats else 0