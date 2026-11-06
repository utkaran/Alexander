"""Централизованная настройка логирования.

Пишет в консоль и в файл рядом с сейвами (data/saves/game.log).
При сборке в --windowed консоли нет — файл остаётся единственным
местом, где видны ошибки.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from core.paths import save_dir

_configured = False

def setup_logging(level: int = logging.INFO) -> None:
    """Настраивает корневой логгер. Вызывать один раз при старте."""
    global _configured
    if _configured:
        return
    _configured = True

    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Консоль
    if sys.stdout is not None:
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(fmt)
        root.addHandler(console)

    # Файл — рядом с сейвами, с ротацией (5 МБ × 3 файла)
    try:
        log_path = save_dir() / 'game.log'
        file_handler = RotatingFileHandler(
            log_path, maxBytes=5 * 1024 * 1024, backupCount=3,
            encoding='utf-8',
        )
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    except OSError:
        root.warning("Не удалось открыть файл лога, пишу только в консоль")

def get_logger(name:str) -> logging.Logger:
    """Возвращает логгер по имени модуля."""
    return logging.getLogger(name)