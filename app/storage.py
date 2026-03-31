import json
from pathlib import Path

from app.config import DATA_FILE
from app.models import Car


def ensure_data_file(path: Path = DATA_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("[]", encoding="utf-8")


def save_cars(cars: list[Car], path: Path = DATA_FILE) -> None:
    ensure_data_file(path)
    payload = [car.model_dump() for car in cars]
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_cars(path: Path = DATA_FILE) -> list[Car]:
    ensure_data_file(path)
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    return [Car(**item) for item in data]
