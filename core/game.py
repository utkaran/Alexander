import json
from pathlib import Path
import random

from .player import Player
from .army import Army
from .region import Region
from .constants import (
UNIT_STATS, TERRAIN_BONUS,
GARRISON_PER_POP, CAPITAL_DEFENSE_BONUS,
ALEXANDER_ATTACK_BONUS, ATTACKER_WIN_LOSS_RATE,
ATTACKER_LOSE_LOSS_RATE
)
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent

class GameState:
    def __init__(self) -> None:
        self.regions: dict[str, Region] = {}
        self.players: dict[str, Player] = {}
        self.armies: dict[str, Army] = {}
        self.current_player_id: str | None = None
        self.turn: int = 0
        self._army_counter = 0

        # Александр и финал
        self.alexander_died: bool = False
        self.game_over: bool = False

        # Цели Акта I — регионы, которые нужно захватить
        self.act1_goal_regions: set[str] = {'sparta', 'thebes', 'athens'}
        self.act1_completed: bool = False
        self.game_over_reason: str | None = None

        self.act2_goal_regions: set[str] = {'persia', 'egypt', 'mesopotamia'}
        self.act2_completed: bool = False

    # Загрузка данных
    def load_map(self, path: str | Path) -> None:
        full_path = Path(path)
        if not full_path.is_absolute():
            full_path = PROJECT_ROOT / full_path
        with open(full_path, encoding='utf-8') as f:
            data = json.load(f)

        for r in data['regions']:
            region = Region(
                id = r['id'],
                name = r['name'],
                terrain = r.get('terrain', 'равнина'),
                owner = r.get('owner'),
                income = r.get('income', 1),
                population = r.get('population', 1),
                neighbors = r.get('neighbors', []),
                is_port = r.get('is_port', False),
                is_capital = r.get('is_capital', False),
                x = r.get('x', 0.0),
                y = r.get('y', 0.0),
                supply = r.get('supply', 1)
            )
            self.regions[region.id] = region

        for p in data['players']:
            player = Player(
                id = p['id'],
                name = p['name'],
                gold = p.get('gold', 0),
                food = p.get('food', 0),
                is_ai = p.get('is_ai', False),
                color = tuple(p.get('color', [200, 200, 200]))
            )
            self.players[player.id] = player

        for region in self.regions.values():
            if region.owner and region.owner in self.players:
                self.players[region.owner].add_region(region.id)

        for region in self.regions.values():
            for neighbor_id in region.neighbors:
                if neighbor_id not in self.regions:
                    print(f"⚠️  {region.id} ссылается на несуществующий {neighbor_id}")
            if region.owner and region.owner not in self.players:
                print(f"⚠️  {region.id} принадлежит неизвестной фракции {region.owner}")

    # Ходы

    def start(self, first_player_id: str) -> None:
        self.current_player_id = first_player_id
        self.turn = 1

    def end_turn(self) -> None:
        player_ids = list(self.players.keys())
        idx = player_ids.index(self.current_player_id)
        idx = (idx + 1) % len(player_ids)

        if idx == 0:
            self.turn += 1
            self._collect_income()

        self.current_player_id = player_ids[idx]

        self.check_game_end()

    def _collect_income(self) -> None:
        for player in self.players.values():
            income = sum(
                self.regions[rid].income
                for rid in player.regions
                if rid in self.regions
            )
            player.gold += income

    # Бой и захват

    def attack(self, attacker_army_id: str, target_region_id: str) -> dict:
        # Защита от битых ID
        if attacker_army_id not in self.armies:
            return {"ok": False, "reason": f"армия {attacker_army_id} не найдена"}
        if target_region_id not in self.regions:
            return {"ok": False, "reason": f"регион {target_region_id} не найден"}

        army = self.armies[attacker_army_id]
        target = self.regions[target_region_id]

        if army.is_empty():
            return {"ok": False, "reason": "армия пуста — некому воевать"}

        if army.location not in self.regions:
            return {"ok": False, "reason": "армия не на карте"}

        current_region = self.regions[army.location]
        if current_region.owner != army.owner:
            return {"ok": False, "reason": f"армия в чужом регионе ({current_region.name})"}

        if not current_region.is_neighbor(target_region_id):
            return {"ok": False, "reason": "регион не соседний"}
        if target.owner == army.owner:
            return {"ok": False, "reason": "это ваш регион"}

        attacker_strength = army.total_strength() * (army.morale / 100)

        # Оборона
        defender_strength = target.population * GARRISON_PER_POP
        if target.is_capital:
            defender_strength *= CAPITAL_DEFENSE_BONUS
        defender_army = None
        if target.owner:
            for a in self.armies.values():
                if a.owner == target.owner and a.location == target.id and not a.is_empty():
                    defender_army = a
                    defender_strength += a.total_strength()
                    break
        has_defender_army = defender_army is not None

        terrain_bonus = {
            "горы": 1.5, "пустыня": 1.2, "равнина": 1.0,
            "джунгли": 1.3, "море": 1.0, "холмы": 1.2,
        }
        defender_strength *= TERRAIN_BONUS.get(target.terrain, 1.0)

        if army.alexander_attached:
            attacker_strength *= ALEXANDER_ATTACK_BONUS

        winner = "attacker" if attacker_strength > defender_strength else "defender"
        alexander_died = False

        if winner == 'attacker':
            if target.owner:
                defender_armies = [
                    a for a in self.armies.values()
                    if a.owner == target.owner and a.location == target.id
                ]
                for def_army in defender_armies:
                    def_army.units.clear()

            old_owner = target.owner
            if old_owner and old_owner in self.players:
                self.players[old_owner].remove_region(target.id)
            target.owner = army.owner
            self.players[army.owner].add_region(target.id)

            # Потери: если у защитника была армия — считаем, иначе 0
            if has_defender_army:
                losses = max(1, int(army.total_count() * ATTACKER_WIN_LOSS_RATE * random.uniform(0.5, 1.5)))
            else:
                losses = 0

            self._apply_losses(army, losses)
            army.location = target.id

            self._cleanup_empty_armies()
            self.check_game_end()

            return {
                'ok': True,
                'winner': 'attacker',
                'region': target.name,
                'losses': losses,
                'attacker_strength': round(attacker_strength, 1),
                'defender_strength': round(defender_strength, 1),
                'had_defender_army': has_defender_army,  # ← добавили для отчёта
                'alexander_died': False,
            }
        else:
            losses = max(1, int(army.total_count() * ATTACKER_LOSE_LOSS_RATE * random.uniform(0.5, 1.5)))
            self._apply_losses(army, losses)

            # Судьба Александра при поражении
            if army.alexander_attached:
                if army.is_empty():
                    alexander_died = True
                elif random.random() < 0.3:
                    alexander_died = True

            if alexander_died:
                army.alexander_attached = False
                self.alexander_died = True
                self.game_over = True
                self.game_over_reason = 'alexander_died'

            self._cleanup_empty_armies()

            self.check_game_end()
            return {
                'ok': True,
                'winner': 'defender',
                'region': target.name,
                'losses': losses,
                'attacker_strength': round(attacker_strength, 1),
                'defender_strength': round(defender_strength, 1),
                'had_defender_army': has_defender_army,
                'alexander_died': alexander_died,
            }

    def _apply_losses(self, army: Army, total_losses: int) -> None:
        if total_losses <= 0 or army.is_empty():
            return

        total = army.total_count()
        if total == 0:
            return

        remaining = total_losses
        for unit_type in list(army.units.keys()):
            if remaining <= 0:
                break
            count = army.units[unit_type]
            # Пропорционально, но не больше remaining и не больше count
            loss = min(count, remaining, max(1, int(count / total * total_losses)))
            army.remove_units(unit_type, loss)
            remaining -= loss

        # Если остались потери — добиваем случайные юниты
        while remaining > 0 and not army.is_empty():
            for unit_type in list(army.units.keys()):
                if remaining <= 0:
                    break
                army.remove_units(unit_type, 1)
                remaining -= 1

    def _remove_army(self, army_id: str) -> None:
        # Полностью убирает армию из игры и из списков игрока.
        army = self.armies.pop(army_id, None)
        if army is None:
            return
        player = self.players.get(army.owner)
        if player and army_id in player.armies:
            player.armies.remove(army_id)

    def _cleanup_empty_armies(self) -> None:
        # Убирает все армии с нулём юнитов. Вызывать после боя/потерь.
        empty_ids = [aid for aid, a in self.armies.items() if a.is_empty()]
        for aid in empty_ids:
            self._remove_army(aid)

    def recruit(self, player_id: str, region_id: str, unit_type: str, count: int) -> dict:
        """Найм юнитов в регионе."""

        if player_id not in self.players:
            return {"ok": False, "reason": f"игрок {player_id} не найден"}
        if region_id not in self.regions:
            return {"ok": False, "reason": f"регион {region_id} не найден"}
        if count <= 0:
            return {"ok": False, "reason": "количество должно быть положительным"}

        player = self.players[player_id]
        region = self.regions[region_id]

        if region.owner != player_id:
            return {"ok": False, "reason": "регион не ваш"}

        stats = UNIT_STATS.get(unit_type)
        if not stats:
            return {"ok": False, "reason": f"нет такого юнита: {unit_type}"}

        total_cost = stats["cost"] * count
        if player.gold < total_cost:
            return {"ok": False, "reason": f"нужно {total_cost} золота, есть {player.gold}"}


        # Ищем армию игрока в регионе или создаём новую
        army = None
        for a in self.armies.values():
            if a.owner == player_id and a.location == region_id:
                army = a
                break

        if army is None:
            self._army_counter +=1
            army_id = f"army_{player_id}_{self._army_counter}"
            army = Army(id=army_id, owner=player_id, location=region_id)
            self.armies[army.id] = army
            player.armies.append(army.id)

        army.add_units(unit_type, count)
        player.gold -= total_cost

        return {"ok": True, "army": army.id, "unit": unit_type, "count": count, "cost": total_cost}

    # Перемещение армии

    def move_army(self, army_id: str, target_region_id: str) -> dict:
        if army_id not in self.armies:
            return {"ok": False, "reason": f"армия {army_id} не найдена"}
        if target_region_id not in self.regions:
            return {"ok": False, "reason": f"регион {target_region_id} не найден"}

        army = self.armies[army_id]

        if army.is_empty():
            return {"ok": False, "reason": "армия пуста — нечего двигать"}

        if army.location not in self.regions:
            return {"ok": False, "reason": "армия не на карте"}

        target = self.regions[target_region_id]
        current = self.regions[army.location]

        if current.owner != army.owner:
            return {"ok": False, "reason": "армия не в своём регионе"}
        if target.owner != army.owner:
            return {"ok": False, "reason": "регион не ваш — атакуйте"}
        if target_region_id not in current.neighbors:
            return {"ok": False, "reason": "регион не соседний"}

        # Ищем армию игрока в целевом регионе

        target_army = None
        for a in self.armies.values():
            if a.owner == army.owner and a.location == target_region_id and a.id != army.id:
                target_army = a
                break
        if target_army:
        # Объединяем: перекидываем юниты из army в target_army
            for unit_type, count in army.units.items():
                target_army.add_units(unit_type, count)

        # Если у перемещаемой армии был Александр — переносим

            if army.alexander_attached:
                target_army.alexander_attached = True
                army.alexander_attached = False

        # Удаляем перемещаемую армию
            self._remove_army(army.id)

            return {
                "ok": True,
                "merged": True,
                "army": target_army.id,
                "to": target.name,
            }
        else:
         # Просто перемещаем
            army.location = target_region_id
            return {
                "ok": True,
                "merged": False,
                "army": army.id,
                "to": target.name,
            }

    def check_act1_victory(self) -> bool:
        # Проверяет, захвачены ли все целевые регионы Акта I.
        if self.act1_completed:
            return True

        all_captured = all(
            self.regions.get(rid) is not None
            and self.regions[rid].owner == 'macedonia'
            for rid in self.act1_goal_regions
        )

        if all_captured:
            self.act1_completed = True
            # self.game_over = True
            # self.game_over_reason = 'victory'
        return self.act1_completed

    def check_act2_victory(self) -> bool:
        if self.act2_completed:
            return True

        all_captured = all(
            self.regions.get(rid) is not None
            and self.regions[rid].owner == 'macedonia'
            for rid in self.act2_goal_regions
        )

        if all_captured:
            self.act2_completed = True
            self.game_over = True
            self.game_over_reason = 'campaign_complete'
        return self.act2_completed

    def check_pella_lost(self) -> bool:
        pella = self.regions.get('pella')
        if pella is None:
            return False
        if pella.owner != 'macedonia':
            self.game_over = True
            self.game_over_reason = 'pella_lost'
            return True
        return False

    def check_game_end(self) -> None:
        if self.game_over:
            return

        self.check_act1_victory()
        if self.game_over:
            return
        self.check_act2_victory()
        if self.game_over:
            return
        self.check_pella_lost()

    def is_greece_alive(self) -> bool:
        """Жива ли Греция — владеет ли хотя бы одним из стартовых регионов."""
        for rid in ('sparta', 'thebes', 'athens'):
            region = self.regions.get(rid)
            if region and region.owner == 'greece':
                return True
        return False
    # Утилиты

    def current_player(self) -> Player:
        return self.players[self.current_player_id]

    def __repr__(self) -> str:
        return f'<GameState: ход {self.turn}, игрок {self.current_player_id}'