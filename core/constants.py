# ЮНИТЫ

UNIT_STATS = {
    'Фаланга':    {'attack': 3,  'defense': 5, 'cost': 12, 'unlock_act': 1},
    'Гетайры':    {'attack': 7,  'defense': 2, 'cost': 20, 'unlock_act': 1},
    'Гипасписты': {'attack': 4,  'defense': 4, 'cost': 15, 'unlock_act': 2},
    'Лучники':    {'attack': 2,  'defense': 1, 'cost': 8, 'unlock_act': 1},
    'Осадные':    {'attack': 8,  'defense': 1, 'cost': 30, 'unlock_act': 2},
    'Слоны':      {'attack': 10, 'defense': 6, 'cost': 50, 'unlock_act': 4},
}

# МЕСТНОСТЬ — бонус к обороне

TERRAIN_BONUS = {
    "горы":     1.5,
    "пустыня":  1.2,
    "равнина":  1.0,
    "джунгли":  1.3,
    "море":     1.0,
    "холмы":    1.2,
}

# БОЕВЫЕ МОДИФИКАТОРЫ

# Гарнизон нейтрального/защищающегося региона = population * GARRISON_PER_POP
GARRISON_PER_POP = 5

# Бонус столицы к обороне
CAPITAL_DEFENSE_BONUS = 1.5

# Бонус Александра к атаке
ALEXANDER_ATTACK_BONUS = 1.3

# Доля потерь атакующего при победе (базовая, ещё умножается на random)
ATTACKER_WIN_LOSS_RATE = 0.2

# Доля потерь атакующего при поражении
ATTACKER_LOSE_LOSS_RATE = 0.4