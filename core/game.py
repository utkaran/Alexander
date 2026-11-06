import json
from pathlib import Path
import random

from .player import Player
from .army import Army
from .region import Region
from .constants import (
UNIT_STATS, ATTACKER_WIN_LOSS_RATE,
ATTACKER_LOSE_LOSS_RATE
)
from core.paths import resource_path
from .alexander_state import AlexanderState
from core.combat import estimate_attack, estimate_defense
from core.log import get_logger
log = get_logger(__name__)

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
        self.alexander: AlexanderState = AlexanderState()
        self.game_over: bool = False

        # Цели Акта I — регионы, которые нужно захватить
        self.act1_goal_regions: set[str] = {'hellespont'}
        self.act1_completed: bool = False
        self.game_over_reason: str | None = None

        self.current_objective_index: int = 0
        self.objectives_complete: set[str] = set()

        self.act2_goal_regions: set[str] = {'persia', 'egypt', 'mesopotamia'}
        self.act2_completed: bool = False

        self.tutorial_active: bool = False
        self.tutorial_scene_id: str | None = None
        self.tutorial_line_index: int = 0

        #Сюжетные сцены - очередь тригеров
        self.pending_scenes: list[str] = []
        self.played_scenes: set[str] = set()

        #Текущий акт(1, 2, ...,)
        self.current_act: int = 1

        self.forced_objective: str | None = None

        self.revolt_timer: int = 0
        self.pending_thebes_revolt: bool = False

        # очередь подсказок
        self.pending_hints: list[str] = []

    # Загрузка данных
    def load_map(self, path: str | Path) -> None:
        full_path = Path(path)
        if not full_path.is_absolute():
            full_path = resource_path(str(path))
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
                supply = r.get('supply', 1),
                garrison_army=r.get('garrison_army'),  # ← ДОБАВЬ
                story_goal=r.get('story_goal'),
                original_owner=r.get('owner')
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
                    log.warning("%s ссылается на несуществующий %s", region.id, neighbor_id)
            if region.owner and region.owner not in self.players:
                log.warning("%s принадлежит неизвестной фракции %s", region.id, region.owner)

        for region in self.regions.values():
            self._spawn_garrison_for(region)

    def load_map_additive(self, path:str | Path) -> None:
        """Догружает карту, НЕ удаляя существующие регионы."""
        full_path = Path(path)
        if not full_path.is_absolute():
            full_path = resource_path(str(path))

        with open(full_path, encoding='utf-8') as f:
            data = json.load(f)

        for r in data['regions']:
            if r['id'] in self.regions:
                continue
            region = Region(
                id=r['id'],
                name=r['name'],
                terrain=r.get('terrain', 'равнина'),
                owner=r.get('owner'),
                income=r.get('income', 1),
                population=r.get('population', 1),
                neighbors=r.get('neighbors', []),
                is_port=r.get('is_port', False),
                is_capital=r.get('is_capital', False),
                x=r.get('x', 0.0),
                y=r.get('y', 0.0),
                supply=r.get('supply', 1),
                garrison_army=r.get('garrison_army'),  # ← ДОБАВЬ
                story_goal=r.get('story_goal'),
            )
            self.regions[region.id] = region

        for p in data['players']:
            if p['id'] in self.players:
                continue
            player = Player(
                id=p['id'],
                name=p['name'],
                gold=p.get('gold', 0),
                food=p.get('food', 0),
                is_ai=p.get('is_ai', False),
                color=tuple(p.get('color', [200, 200, 200])),
            )
            self.players[player.id] = player

        for region in self.regions.values():
            if region.owner and region.owner in self.players:
                if region.id not in self.players[region.owner].regions:
                    self.players[region.owner].add_region(region.id)
            self._spawn_garrison_for(region)

    def current_objective(self):
        """Текущая цель Акта или None, если цепочка пройдена."""
        from core.objectives import get_chain
        chain = get_chain(self.current_act)
        if self.current_objective_index >= len(chain):
            return None
        return chain[self.current_objective_index]
    # Ходы

    def start(self, first_player_id: str) -> None:
        self.current_player_id = first_player_id
        self.turn = 1
        self._reset_actions(first_player_id)

    def _tick_revolt(self) -> None:
        """Уменьшает таймер восстания. Когда 0 — снимает is_garrison."""
        if self.revolt_timer <= 0:
            return  # нет активного восстания

            # Есть ли ещё живое восстание в Фивах?
        revolt_alive = any(
            a.is_revolt and not a.is_empty() and a.location == 'thebes'
            for a in self.armies.values()
        )
        if not revolt_alive:
            self.revolt_timer = 0  # восстание подавлено — сброс
            return

        self.revolt_timer -= 1
        if self.revolt_timer <= 0:
            # Таймер вышел — восстание идёт в атаку
            for a in self.armies.values():
                if a.is_revolt:
                    a.is_garrison = False
    def end_turn(self) -> None:
        if self.current_player_id not in self.players:
            self._advance_to_next_alive_player()
        player_ids = list(self.players.keys())
        if not player_ids:
            self.current_player_id = None
            return
        if self.current_player_id not in player_ids:
            idx = 0
        else:
            idx = player_ids.index(self.current_player_id)
            idx = (idx+1) % len(player_ids)

        if idx == 0:
            self.turn += 1
            self._collect_income()
            self._tick_revolt()

        self.current_player_id = player_ids[idx]
        self._reset_actions(self.current_player_id)

        self.check_game_end()

    def _reset_actions(self, player_id: str) -> None:
        for army in self.armies.values():
            if army.owner == player_id:
                army.has_acted = False

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
        if attacker_army_id in self.armies and self.armies[attacker_army_id].has_acted:
            return {"ok": False, "reason": "Эта армия уже действовала в этом ходу"}
        # Защита от битых ID
        if attacker_army_id not in self.armies:
            return {"ok": False, "reason": f"армия {attacker_army_id} не найдена"}
        if target_region_id not in self.regions:
            return {"ok": False, "reason": f"регион {target_region_id} не найден"}

        army = self.armies[attacker_army_id]
        target = self.regions[target_region_id]

        if getattr(target, 'is_protected', False):  # ← новое
            return {"ok": False, "reason": "Этот регион сохраняет нейтралитет — атака невозможна"}

        if target.story_goal is not None and target.owner != army.owner:
            return {
                "ok": False,
                "reason": "Этот регион можно склонить только послами (кнопка «Отправить послов»)",
            }

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

        attacker_strength = estimate_attack(army)

        # Оборона
        defender_strength = estimate_defense(target, self)
        defender_owner = target.owner if target.owner else "neutral"
        has_defender_army = any(
            a.owner == defender_owner and a.location == target.id and not a.is_empty()
            for a in self.armies.values()
        )

        winner = "attacker" if attacker_strength > defender_strength else "defender"
        alexander_died = False

        if winner == 'attacker':
            defender_owner = target.owner if target.owner else "neutral"
            defender_armies = [
                a for a in self.armies.values()
                if a.owner == defender_owner and a.location == target.id
            ]
            for def_army in defender_armies:
                def_army.units.clear()

            old_owner = target.owner
            if old_owner and old_owner in self.players:
                self.players[old_owner].remove_region(target.id)
                self._remove_player_if_dead(old_owner)
            target.owner = army.owner
            self.players[army.owner].add_region(target.id)
            self._on_region_captured(target.id)
            if target.id == 'thebes':
                self.revolt_timer = 0

            base_losses = army.total_count() * ATTACKER_WIN_LOSS_RATE * random.uniform(0.5, 1.5)
            if has_defender_army:
                losses = max(1, int(base_losses))
            else:
                losses = max(1, int(base_losses * 0.5))

            army.apply_losses(losses)
            army.location = target.id
            army.has_acted = True

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
            army.apply_losses(losses)
            army.has_acted = True

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
        if army_id in self.armies and self.armies[army_id].has_acted:
            return {"ok": False, "reason": "Эта армия уже действовала в этом ходу"}
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
            army.has_acted = True
            return {
                "ok": True,
                "merged": False,
                "army": army.id,
                "to": target.name,
            }

    def spawn_thebes_revolt(self) -> None:
        """Создаёт армию восстания в Фивах и ставит принудительную цель."""
        region = self.regions.get('thebes')
        if region is None:
            return
        if region.owner == 'macedonia':
            return

        existing = None
        for a in self.armies.values():
            if a.owner == 'greece' and a.location == 'thebes' and not a.is_empty():
                existing = a
                break

        if existing is not None:
            # Дополняем существующую армию до состава восстания
            existing.add_units('Фаланга', 3)
            existing.add_units('Гипасписты', 1)
            existing.add_units('Лучники', 1)
            existing.is_garrison = True
            existing.is_revolt = True# ← КРИТИЧНО
            existing.has_acted = True
        else:
            self._army_counter += 1
            army_id = f"army_thebes_revolt"
            revolt = Army(id=army_id, owner='greece', location='thebes', is_garrison=True, is_revolt=True)
            revolt.add_units('Фаланга', 3)
            revolt.add_units('Гипасписты', 1)
            revolt.add_units('Лучники', 1)
            revolt.has_acted = True
            self.armies[army_id] = revolt
            greece = self.players.get('greece')
            if greece is not None:
                greece.armies.append(army_id)

        self.forced_objective = 'thebes'
        self.revolt_timer = 3
        self.queue_hint('hint_thebes_revolt')

    def unlock_scenario(self, scenario_id: str) -> None:
        """Разблокирует сценарий в профиле (если ещё не разблокирован).

            Вызывается из _on_story_scene_finished (Renderer), когда игрок
            прошёл соответствующую сюжетную сцену.
            """

        from core.profile import load_profile, save_profile

        profile = load_profile()
        unlocked = profile.get('scenarios_unlocked', [])
        if scenario_id not in unlocked:
            unlocked.append(scenario_id)
            profile['scenarios_unlocked'] = unlocked
            save_profile(profile)

    def check_act1_victory(self) -> bool:
        # Проверяет, захвачены ли все целевые регионы Акта I.
        if self.act1_completed:
            return True

        from core.objectives import get_chain
        chain = get_chain(1)
        if not chain:
            return False
        if all(o.id in self.objectives_complete for o in chain):
            self.act1_completed = True
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
        if 'greece' not in self.players:
            return False
        for rid in ('sparta', 'thebes', 'athens'):
            region = self.regions.get(rid)
            if region and region.owner == 'greece':
                return True
        return False

    def _check_objective_completed(self, region_id: str) -> None:
        """Если захваченный регион — текущая цель, засчитать и наградить."""
        from core.objectives import get_chain
        chain = get_chain(self.current_act)
        if self.current_objective_index >= len(chain):
            return

        objective = chain[self.current_objective_index]
        if objective.region_id != region_id:
            return

        if 'macedonia' in self.players:
            self.players['macedonia'].gold += objective.reward_gold

        self.objectives_complete.add(objective.id)
        self.current_objective_index += 1

    def _spawn_garrison_for(self, region: Region) -> None:
        """Создаёт армию-гарнизон из region.garrison_army, если она есть."""
        if not region.garrison_army:
            return

        army_id = f"army_garrison_{region.id}"
        # Чтобы не плодить дубликаты (если вызовем дважды)
        if army_id in self.armies:
            return

        # Владелец гарнизона = владелец региона, или "neutral" для нейтралов
        army_owner = region.owner if region.owner else "neutral"
        army = Army(id=army_id, owner=army_owner, location=region.id)
        for unit_type, count in region.garrison_army.items():
            army.add_units(unit_type, count)

        self.armies[army_id] = army
        # ВАЖНО: НЕ добавляем в player.armies!
        # Иначе ИИ попытается двигать гарнизон.

    def _remove_player_if_dead(self, player_id: str) -> bool:
        """Удаляет фракцию, если у неё не осталось регионов.

            Возвращает True, если фракция удалена.
            """

        player = self.players.get(player_id)
        if player is None:
            return False
        if player.regions:
            return False

        # 1. Убираем все армии фракции из игры
        for army_id in list(player.armies):
            self._remove_army(army_id)
            # Плюс армии, которые не в player.armies (гарнизоны, восстания)
        for army_id, army in list(self.armies.items()):
            if army.owner == player_id:
                self._remove_army(army_id)

        # 2. Убираем из players
        del self.players[player_id]

        # 3. Если это был текущий игрок — переключаем на следующего живого
        if self.current_player_id == player_id:
            self._advance_to_next_alive_player()
        return True

    def _advance_to_next_alive_player(self) -> None:
        """Переключает current_player_id на следующего живого игрока."""
        if not self.players:
            self.current_player_id = None
            return
        player_ids = list(self.players.keys())
        if self.current_player_id in player_ids:
            idx = player_ids.index(self.current_player_id)
            idx = (idx + 1) % len(player_ids)
        else:
            idx = 0
        self.current_player_id = player_ids[idx]
        self._reset_actions(self.current_player_id)

    # СЮЖЕТНЫЕ ТРИГГЕРЫ
    def queue_scene(self, scene_id: str) -> None:
        """Ставит сцену в очередь. Если уже игралась/в очереди — игнорирует."""
        if scene_id in self.played_scenes:
            return
        if scene_id in self.pending_scenes:
            return
        self.pending_scenes.append(scene_id)

    def pop_scene(self) -> str | None:
        """Забирает следующую сцену из очереди. Помечает как сыгранную."""
        if not self.pending_scenes:
            return None
        scene_id = self.pending_scenes.pop(0)
        self.played_scenes.add(scene_id)
        return scene_id

    def has_pending_scene(self) -> bool:
        return bool(self.pending_scenes)

    def queue_hint(self, hint_id: str) -> None:
        """Ставит подсказку в очередь. Если уже игралась/в очереди — игнорирует."""
        if hint_id in self.played_scenes:
            return
        if hint_id in self.pending_hints:
            return
        self.pending_hints.append(hint_id)

    def pop_hint(self) -> str | None:
        """Забирает следующую подсказку. Помечает как сыгранную."""
        if not self.pending_hints:
            return None
        hint_id = self.pending_hints.pop(0)
        self.played_scenes.add(hint_id)
        return hint_id

    def has_pending_hint(self) -> bool:
        return bool(self.pending_hints)

    def _on_region_captured(self, region_id: str) -> None:
        """Триггеры при захвате региона."""
        self._check_objective_completed(region_id)
        if region_id == 'thebes':
            self.queue_scene('act1_thebes_burn')
        elif region_id == 'athens':
            self.queue_scene('act1_athens_surrender')
        elif region_id == 'sparta':
            self.queue_scene('act1_sparta_neutrality')
        elif region_id == 'hellespont':
            self.queue_scene('act1_hellespont')
    # Утилиты

    def current_player(self) -> Player:
        return self.players[self.current_player_id]

    def __repr__(self) -> str:
        return f'<GameState: ход {self.turn}, игрок {self.current_player_id}'