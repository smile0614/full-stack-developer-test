from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "cars.json"

ENCAR_BASE_URL = "https://www.encar.com/dc/dc_carsearchlist.do"
REQUEST_TIMEOUT_SECONDS = 20
