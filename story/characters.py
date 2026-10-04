# Персонажи новелл

CHARACTERS = {
    'narrator': {
        'name': '',
        'color': (200, 200, 200),
        'flip': False,
    },

    'alexander': {
        'name': 'Александр',
        'color': (255, 215, 0), #золотой
        'flip': True,
    },

    'philip': {
        'name': 'Филипп II',
        'color': (200, 100, 50), # медный
        'flip': False,
    },

    'olympias': {
        'name': 'Олимпиада',
        'color': (180, 100, 180), # пурпурный
        'flip': True,
    },

    'aristotle': {
        'name': 'Аристотель',
        'color': (100, 150, 200), # синий
        'flip': False,
    },

    'hephaestion': {
        'name': 'Гефестион',
        'color': (100, 200, 150), # зеленый
        'flip': False,
    },

    'parmenion': {
        'name': 'Парменион',
        'color': (150, 150, 100), # тусклый
        'flip': True,
    },

    'bucephalus': {
        'name': 'Буцефал',
        'color': (120, 80, 40), # коричневый
        'flip': False,
    },

'attalus': {
        'name': 'Аттал',
        'color': (140, 90, 60),
        'flip': False,
    },
    'pausanias': {
        'name': 'Павсаний',
        'color': (90, 90, 90),
        'flip': False,
    },
    'cleopatra': {
        'name': 'Клеопатра',
        'color': (200, 150, 180),
        'flip': True,
    },
    'demosthenes': {
        'name': 'Демосфен',
        'color': (120, 130, 160),
        'flip': False,
    },
}

def get_name(who:str) -> str:
    return CHARACTERS.get(who, {}).get('name', who)

def get_color(who:str) -> tuple[int, int, int]:
    return CHARACTERS.get(who, {}).get('color', (200, 200, 200))

def get_flip(who: str) -> bool:
    return CHARACTERS.get(who, {}).get("flip", False)