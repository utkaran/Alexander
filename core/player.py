from dataclasses import dataclass, field

@dataclass
class Player:
    id: str
    name: str
    gold: int = 0
    food: int = 0
    reputation: int = 0
    is_ai: bool = False
    color: tuple[int, int, int] = (200, 200, 200)
    regions: list[str] = field(default_factory=list)
    armies: list[str] = field(default_factory=list)

    # relations: dict[str, str] = field(default_factory=dict)  # ← задел на дипломатию, ПОКА НЕ НУЖНО

    def add_region(self, region_id: str) -> None:
        if region_id not in self.regions:
            self.regions.append(region_id)

    def remove_region(self, region_id: str) -> None:
        if region_id in self.regions:
            self.regions.remove(region_id)

    def region_count(self) -> int:
        return len(self.regions)

    def __repr__(self) -> str:
        return (f'<Player {self.name} ({"AI" if self.is_ai else "человек"}), '
                f'регионов: {self.region_count()}, золото: {self.gold}, '
                f'репутация: {self.reputation}>')