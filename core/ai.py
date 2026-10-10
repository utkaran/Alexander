from collections import deque
import random

from .game import GameState
from .constants import (
UNIT_STATS, TERRAIN_BONUS,
GARRISON_PER_POP, CAPITAL_DEFENSE_BONUS
)

ATTACK_RATIO_THRESHOLD = 1.5

# ПЛАНИРОВЩИК

def ai_plan(game: GameState, player_id: str) -> list[dict]:
    """Собирает план действий ИИ. Ничего не выполняет.

        Возвращает список действий в формате:
            {"type": "recruit", "region": "athens", "unit": "Фаланга"}
            {"type": "move",    "army": "army_greece_1", "target": "athens"}
            {"type": "attack",  "army": "army_greece_1", "target": "thessaly"}
    """

    player = game.players[player_id]
    plan: list[dict] = []

    _plan_recruit(game, player, plan)
    _plan_moves(game, player, plan)
    _plan_attacks(game, player, plan)

    return plan

# ВЫПОЛНЕНИЕ ОДНОГО ДЕЙСТВИЯ

def execute_action(game: GameState, action: dict) -> dict:
    """Выполняет одно действие из плана.

    Возвращает результат в формате, пригодном для лога:
        {"ok": True, "text": "Греция наняла Фалангу в Афинах"}
        {"ok": False, "text": "Не удалось выполнить действие"}
    """
    action_type = action.get("type")

    if action_type == "recruit":
        result = game.recruit(
            action["owner"],
            action["region"],
            action["unit"],
            1,
        )
        if result.get("ok"):
            region_name = game.regions[action["region"]].name
            return {
                "ok": True,
                "type": "recruit",
                "region": action["region"],
                "text": f"Нанял {action['unit']} в {region_name}",
            }
        return {"ok": False, "text": f"Найм не удался: {result.get('reason')}"}

    if action_type == "move":
        result = game.move_army(action["army"], action["target"])
        if result.get("ok"):
            return {
                "ok": True,
                "type": "move",
                "region": action["target"],
                "text": "Переместил армию" + (" (объединил)" if result.get("merged") else ""),
            }
        return {"ok": False, "text": f"Перемещение не удалось: {result.get('reason')}"}

    if action_type == "attack":
        result = game.attack(action["army"], action["target"])
        if result.get("ok"):
            if result["winner"] == "attacker":
                text = f"Захватил {result['region']} (потери: {result['losses']})"
            else:
                text = f"Атака на {result['region']} отбита (потери: {result['losses']})"
            return {
                "ok": True,
                "type": "attack",
                "region": action["target"],
                "battle": result,
                "text": text,
            }
        return {"ok": False, "text": f"Атака не удалась: {result.get('reason')}"}

    return {"ok": False, "text": f"Неизвестное действие: {action_type}"}

# ПЛАНИРОВАНИЕ: НАЙМ

def _plan_recruit(game: GameState, player, plan: list[dict]) -> None:
    border_regions = _find_border_regions(game, player)
    if not border_regions:
        return

    # Считаем, сколько можем потратить
    budget = player.gold
    if budget < UNIT_STATS["Лучники"]["cost"]:
        return

    for rid in border_regions:
        if budget < UNIT_STATS["Лучники"]["cost"]:
            break

        unit_type = _pick_unit_type(game, player, rid, budget)
        if unit_type is None:
            break

        cost = UNIT_STATS[unit_type]["cost"]
        plan.append({
            "type": "recruit",
            "owner": player.id,
            "region": rid,
            "unit": unit_type,
        })
        budget -= cost

def _find_border_regions(game: GameState, player) -> list[str]:
    """Регионы игрока, которые граничат с чужой или нейтральной территорией."""
    border_regions = []
    for rid in player.regions:
        if rid not in game.regions:
            continue
        region = game.regions[rid]
        for neighbor_id in region.neighbors:
            if neighbor_id not in game.regions:
                continue
            neighbor = game.regions[neighbor_id]
            if neighbor.owner != player.id:
                border_regions.append(rid)
                break
    return border_regions

def _pick_unit_type(game: GameState, player, region_id: str, budget: int) -> str | None:
    """Выбирает тип юнита для найма. None — если денег не хватает."""
    if budget >= UNIT_STATS["Осадные"]["cost"] and _near_enemy_capital(game, player, region_id):
        return "Осадные"
    if budget >= UNIT_STATS["Гетайры"]["cost"]:
        return "Гетайры"
    if budget >= UNIT_STATS["Фаланга"]["cost"]:
        return "Фаланга"
    if budget >= UNIT_STATS["Лучники"]["cost"]:
        return "Лучники"
    return None

def _near_enemy_capital(game: GameState, player, region_id: str) -> bool:
    """Граничит ли регион со столицей, принадлежащей не игроку."""
    region = game.regions.get(region_id)
    if region is None:
        return False
    for neighbor_id in region.neighbors:
        neighbor = game.regions.get(neighbor_id)
        if neighbor is None:
            continue
        if neighbor.is_capital and neighbor.owner != player.id:
            return True
    return False

# ПЛАНИРОВАНИЕ: ДВИЖЕНИЕ

def _plan_moves(game: GameState, player, plan: list[dict]) -> None:
    """Планирует движение армий к фронту."""
    for army in list(game.armies.values()):
        if army.owner != player.id or army.is_empty():
            continue
        if army.has_acted:
            continue
        if army.location not in game.regions:
            continue

        # Если из текущего региона можно атаковать — не двигаем
        if _has_attack_target(game, player, army):
            continue

        next_region = _find_step_towards_enemy(game, player, army.location)
        if next_region is None:
            continue

        plan.append({
            "type": "move",
            "army": army.id,
            "target": next_region,
        })

def _has_attack_target(game: GameState, player, army) -> bool:
    """Есть ли у армии сосед, которого она может атаковать с перевесом."""
    if army.location not in game.regions:
        return False

    current = game.regions[army.location]
    attacker_strength = army.attack_strength() * (army.morale / 100)

    for neighbor_id in current.neighbors:
        if neighbor_id not in game.regions:
            continue
        neighbor = game.regions[neighbor_id]
        if neighbor.owner == player.id:
            continue

        # Пассивность Персии
        if player.id == 'persia' and game.is_greece_alive() and neighbor.owner == 'macedonia':
            continue

        defender_strength = _estimate_defense(game, neighbor)
        if defender_strength <= 0:
            continue

        if attacker_strength / defender_strength > ATTACK_RATIO_THRESHOLD:
            return True

    return False

def _find_step_towards_enemy(game: GameState, player, start_region_id: str) -> str | None:
    """BFS по своим регионам. Возвращает ID соседнего региона,
    который делает первый шаг к ближайшему врагу. Или None."""
    my_regions = set(player.regions)

    visited = {start_region_id}
    queue = deque()
    queue.append((start_region_id, None))

    while queue:
        current_id, first_step = queue.popleft()
        current = game.regions.get(current_id)
        if current is None:
            continue

        has_enemy_neighbor = False
        for neighbor_id in current.neighbors:
            if neighbor_id not in game.regions:
                continue
            neighbor = game.regions[neighbor_id]
            if neighbor.owner != player.id:
                has_enemy_neighbor = True
                break

        if has_enemy_neighbor:
            return first_step

        for neighbor_id in current.neighbors:
            if neighbor_id in visited:
                continue
            if neighbor_id not in my_regions:
                continue
            visited.add(neighbor_id)
            next_first = first_step if first_step is not None else neighbor_id
            queue.append((neighbor_id, next_first))

    return None

# ПЛАНИРОВАНИЕ: АТАКИ

def _plan_attacks(game: GameState, player, plan: list[dict]) -> None:
    """Планирует одну атаку самой сильной армией."""
    persia_passive = (player.id == 'persia' and game.is_greece_alive())
    tutorial_passive = game.tutorial_active

    best_attack = None
    best_ratio = 0.0

    for army in list(game.armies.values()):
        if army.owner != player.id or army.is_empty():
            continue
        if army.has_acted:
            continue
        if army.location not in game.regions:
            continue

        current_region = game.regions[army.location]
        attacker_strength = army.attack_strength() * (army.morale / 100)

        for neighbor_id in current_region.neighbors:
            if neighbor_id not in game.regions:
                continue

            neighbor = game.regions[neighbor_id]
            if neighbor.owner == player.id:
                continue

            if persia_passive and neighbor.owner == 'macedonia':
                continue

            if tutorial_passive and neighbor.owner == 'macedonia':
                continue

            defender_strength = _estimate_defense(game, neighbor)
            if defender_strength <= 0:
                continue

            ratio = attacker_strength / defender_strength
            if ratio > ATTACK_RATIO_THRESHOLD and ratio > best_ratio:
                best_ratio = ratio
                best_attack = {"army": army.id, "target": neighbor_id}

    if best_attack:
        plan.append({
            "type": "attack",
            "army": best_attack["army"],
            "target": best_attack["target"],
        })

def _estimate_defense(game: GameState, region) -> float:
    """Оценка силы обороны региона."""
    strength = region.population * GARRISON_PER_POP
    strength *= TERRAIN_BONUS.get(region.terrain.lower(), 1.0)
    if region.is_capital:
        strength *= CAPITAL_DEFENSE_BONUS

    if region.owner:
        for army in game.armies.values():
            if army.owner == region.owner and army.location == region.id:
                strength += army.defense_strength()
                break

    return strength