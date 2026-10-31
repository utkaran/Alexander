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
    # НОВЫЕ ПОЛЯ:
    # Гарнизон (постоянная армия региона). Создаётся при load_map.
    # Формат: {"Фаланга": 2, "Лучники": 1}. None — гарнизона нет.
    garrison_army: dict[str, int] | None = None
    # Сюжетная цель: вместо штурма — новелла («Отправить послов»).
    # None — регион берётся обычной атакой.
    story_goal: str | None = None
    original_owner: str | None = None
    is_protected: bool = False

    def __post_init__(self) -> None:
        self.terrain = self.terrain.lower()

    def is_neighbor(self, other_id: str) -> bool:
        return other_id in self.neighbors

    def __repr__(self) -> str:
        return f'<Region {self.name} ({self.owner or "нейтр."})>'