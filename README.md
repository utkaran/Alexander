# Фаланга: Путь Александра

Пошаговая стратегия с новеллистическими вставками. Александр — юнит-генерал на карте, а не абстрактная фракция.

## Быстрый старт
```bash
pip install -r requirements.txt
python main_pygame.py

pyinstaller --onefile --windowed --name "Фаланга" --icon=assets/icon.ico ^
  --add-data "assets;assets" --add-data "data;data" --add-data "story;story" ^
  main_pygame.py