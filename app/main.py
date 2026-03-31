from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.scheduler import refresh_cars, scheduler, start_scheduler
from app.scraper import fallback_cars
from app.storage import ensure_data_file, load_cars, save_cars

app = FastAPI(title="Million Miles Test Task")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.on_event("startup")
async def on_startup() -> None:
    ensure_data_file()
    current = load_cars()
    if not current:
        save_cars(fallback_cars())
    refresh_cars()
    start_scheduler()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request) -> HTMLResponse:
    cars = load_cars()
    return templates.TemplateResponse(request=request, name="index.html", context={"cars": cars})


@app.get("/api/cars")
async def get_cars() -> list[dict]:
    return [car.model_dump() for car in load_cars()]


@app.post("/api/refresh")
async def refresh() -> dict:
    refresh_cars()
    return {"status": "ok", "items": len(load_cars())}
