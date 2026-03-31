# Full Stack Developer Test Task

This project implements:

- ENCAR parsing (brand, model, year, mileage, price, photo)
- Data persistence in JSON
- Automatic refresh once per day
- Responsive landing page with car cards

## Stack

- Python 3.11+
- FastAPI
- BeautifulSoup
- APScheduler
- Jinja2 (templating)

## Run locally

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open: `http://127.0.0.1:8000`

## API

- `GET /api/cars` - all parsed cars
- `POST /api/refresh` - trigger immediate refresh

## Daily update

Daily update runs automatically inside the FastAPI app using APScheduler (`interval: 1 day`).

You can also force manual refresh:

```bash
python scripts/refresh_data.py
```

## Notes

- If ENCAR structure changes or temporary blocking happens, the app stores fallback demo data to keep UI functional.
- Parsed data is saved to `data/cars.json`.
