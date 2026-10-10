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