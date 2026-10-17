"""Состояние Александра: истощение, здоровье, перки.

Заглушка для Этапа 5A-3 (Акт IV). Поля есть, механика НЕ реализована.
Нужно, чтобы сейвы с самого начала содержали эти поля и не требовали
миграции SAVE_VERSION при введении истощения.
"""

from dataclasses import dataclass, field

@dataclass
class AlexanderState:
    exhaustion: int = 0 # 0–100, растёт в походе (Этап 5A-3)
    health: int = 100 # 0–100, задел на ранения/болезни
    perks: list[str] = field(default_factory=list) # купленные перки (Этап 6)

    def is_exhausted(self) -> bool:
        return self.exhaustion >= 100

    def __repr__(self):
        return (f'<AlexanderState: истощение {self.exhaustion}/100, '
                f'здоровье {self.health}/100, перков: {len(self.perks)}>')