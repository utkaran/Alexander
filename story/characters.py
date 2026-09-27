# Персонажи новелл

CHARACTERS = {
    'narrator': {
        'name': '',
        'color': (200, 200, 200),
    },

    'alexander': {
        'name': 'Александр',
        'color': (255, 215, 0), #золотой
    },

    'philip': {
        'name': 'Филипп II',
        'color': (200, 100, 50), # медный
    },

    'olympias': {
        'name': 'Олимпиада',
        'color': (180, 100, 180), # пурпурный
    },

    'aristotle': {
        'name': 'Аристотель',
        'color': (100, 150, 200), # синий
    },

    'hephaestion': {
        'name': 'Гефестион',
        'color': (100, 200, 150), # зеленый
    },

    'parmenion': {
        'name': 'Парменион',
        'color': (150, 150, 100), # тусклый
    },

    'bucephalus': {
        'name': 'Буцефал',
        'color': (120, 80, 40), # коричневый
    },
}

def get_name(who:str) -> str:
    return CHARACTERS.get(who, {}).get('name', who)

def get_color(who:str) -> tuple[int, int, int]:
    return CHARACTERS.get(who, {}).get('color', (200, 200, 200))