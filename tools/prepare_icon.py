"""Готовит иконку: обрезает белые углы, делает 256/32/ico."""
from pathlib import Path
from PIL import Image, ImageDraw


def make_rounded_mask(size: int, radius: int) -> Image.Image:
    """Создаёт маску со скруглёнными углами (прозрачность вне скругления)."""
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=radius,
        fill=255,
    )
    return mask


def main():
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    src = PROJECT_ROOT / "assets" / "icon_source.jpg"
  # ← твой скачанный файл
    if not src.exists():
        print(f"Нет файла: {src}. Скачай иконку и положи сюда.")
        return

    img = Image.open(src).convert("RGBA")
    size = img.width  # 1024 (или сколько скачал)

    # Скруглённые углы: радиус ≈ 22% от размера (как у iOS)
    radius = int(size * 0.22)
    mask = make_rounded_mask(size, radius)

    # Применяем маску — углы становятся прозрачными
    img.putalpha(mask)

    # Сохраняем в разных размерах

    out_dir = PROJECT_ROOT / "assets"
    out_dir.mkdir(exist_ok=True)

    img.resize((256, 256), Image.LANCZOS).save(out_dir / "icon.png")
    img.resize((32, 32), Image.LANCZOS).save(out_dir / "icon_32.png")
    img.resize((256, 256), Image.LANCZOS).save(
        out_dir / "icon.ico", format="ICO", sizes=[(256, 256)]
    )

    print("Готово: assets/icon.png, assets/icon_32.png, assets/icon.ico")


if __name__ == "__main__":
    main()