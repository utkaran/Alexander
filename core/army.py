from dataclasses import dataclass, field

from .constants import UNIT_STATS

@dataclass
class Army:
    id: str
    owner: str
    location: str
    units: dict[str, int] = field(default_factory=dict)
    morale: int = 100
    alexander_attached: bool = False
    has_acted: bool = False
    is_garrison: bool = False
    is_revolt: bool = False

    def attack_strength(self) -> float:
        s = 0.0
        for unit_type, count in self.units.items():
            stats = UNIT_STATS.get(unit_type)
            if stats:
                s += stats['attack'] * count
        return s

    def defense_strength(self) -> float:
        s = 0.0
        for unit_type, count in self.units.items():
            stats = UNIT_STATS.get(unit_type)
            if stats:
                s += stats['defense'] * count
        return s

    def apply_losses(self, total_losses: int) -> None:
        """Распределяет потери пропорционально составу (largest remainder).

        Нельзя потерять больше, чем есть. Редкие юниты не умирают первыми
        при малых потерях: 1 гетайр + 10 фаланг, потеря 1 → умирает фаланга.
        """
        if total_losses <= 0 or self.is_empty():
            return

        total = self.total_count()
        if total == 0:
            return

        total_losses = min(total_losses, total)

        # Пропорциональные потери (дробные)
        exact = {
            unit_type: count / total * total_losses
            for unit_type, count in self.units.items()
        }

        # Целая часть — гарантированные потери
        losses = {unit_type: int(value) for unit_type, value in exact.items()}
        assigned = sum(losses.values())
        remaining = total_losses - assigned

        # Остаток — тем, у кого наибольшая дробная часть (largest remainder)
        if remaining > 0:
            by_remainder = sorted(
                exact.keys(),
                key=lambda u: exact[u] - losses[u],
                reverse=True,
            )
            for unit_type in by_remainder:
                if remaining <= 0:
                    break
                if losses[unit_type] < self.units[unit_type]:
                    losses[unit_type] += 1
                    remaining -= 1

        # Применяем, не превышая количество юнитов каждого типа
        for unit_type, loss in losses.items():
            loss = min(loss, self.units.get(unit_type, 0))
            if loss > 0:
                self.remove_units(unit_type, loss)
    def total_strength(self) -> float:
        return self.attack_strength() + self.defense_strength()

    def total_count(self) -> int:
        return sum(self.units.values())

    def add_units(self, unit_type: str, count: int) -> None:
        if count <= 0:
            return
        self.units[unit_type] = self.units.get(unit_type, 0) + count

    def remove_units(self, unit_type: str, count: int) -> None:
        if count <= 0 or unit_type not in self.units:
            return
        self.units[unit_type] -= count
        if self.units[unit_type] <= 0:
            del self.units[unit_type]

    def is_empty(self) -> bool:
        return self.total_count() == 0

    def __repr__(self) -> str:
        return f'<Army {self.id} ({self.owner}) в {self.location}, юнитов: {self.total_count()}>'