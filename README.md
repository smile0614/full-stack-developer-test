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

## Deploy to Vercel

This project is configured for Vercel serverless deployment:

- entrypoint: `api/index.py`
- config: `vercel.json`
- daily cron: `GET /api/refresh` at `02:00 UTC`

Important behavior on Vercel:

- APScheduler is disabled (serverless functions are not always running).
- Data file uses `/tmp/cars.json` in Vercel environment.
- If cache is empty, app fetches data on demand.

### Steps

1. Push project to GitHub.
2. Import repository in Vercel.
3. Framework preset: **Other**.
4. Build command: leave empty.
5. Output directory: leave empty.
6. Deploy.

### Optional security for cron refresh

If you set `CRON_SECRET` env var in Vercel, then `/api/refresh` requires header:

- `x-cron-secret: <CRON_SECRET>`

For Vercel cron jobs, either:

- keep `CRON_SECRET` unset, or
- call refresh from an external scheduler/service that can send custom header.
