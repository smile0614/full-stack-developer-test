from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
IS_VERCEL = os.getenv("VERCEL") == "1"
DATA_FILE = Path("/tmp/cars.json") if IS_VERCEL else (BASE_DIR / "data" / "cars.json")

ENCAR_BASE_URL = "https://www.encar.com/dc/dc_carsearchlist.do"
REQUEST_TIMEOUT_SECONDS = 20
