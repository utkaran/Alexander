from dataclasses import dataclass, field

@dataclass
class Region:
    id: str
    name: str
    terrain: str='равнина'
    owner: str | None = None
    income: int = 1
    population: int = 1
    neighbors: list[str] = field(default_factory=list)
    is_port: bool = False
    is_capital: bool = False
    x: float = 0.0
    y: float = 0.0
    supply: int = 1

    def __post_init__(self) -> None:
        self.terrain = self.terrain.lower()

    def is_neighbor(self, other_id: str) -> bool:
        return other_id in self.neighbors

    def __repr__(self) -> str:
        return f'<Region {self.name} ({self.owner or "нейтр."})>'