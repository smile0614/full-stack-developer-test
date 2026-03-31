from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.scheduler import refresh_cars


if __name__ == "__main__":
    refresh_cars()
    print("Data refreshed.")
