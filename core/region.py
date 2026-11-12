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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "terrain": self.terrain,
            "owner": self.owner,
            "income": self.income,
            "population": self.population,
            "neighbors": list(self.neighbors),
            "is_port": self.is_port,
            "is_capital": self.is_capital,
            "x": self.x,
            "y": self.y,
            "supply": self.supply,
            "garrison_army": self.garrison_army,
            "story_goal": self.story_goal,
            "original_owner": self.original_owner,
            "is_protected": self.is_protected,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Region":
        return cls(
            id=d["id"],
            name=d["name"],
            terrain=d.get("terrain", "равнина"),
            owner=d.get("owner"),
            income=d.get("income", 1),
            population=d.get("population", 1),
            neighbors=list(d.get("neighbors", [])),
            is_port=d.get("is_port", False),
            is_capital=d.get("is_capital", False),
            x=d.get("x", 0.0),
            y=d.get("y", 0.0),
            supply=d.get("supply", 1),
            garrison_army=d.get("garrison_army"),
            story_goal=d.get("story_goal"),
            original_owner=d.get("original_owner", d.get("owner")),
            is_protected=d.get("is_protected", False),
        )