import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.scraper import fallback_cars, scrape_encar
from app.storage import save_cars

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def refresh_cars() -> None:
    try:
        cars = scrape_encar()
        if not cars:
            cars = fallback_cars()
        save_cars(cars)
        logger.info("Car data refreshed successfully (%d rows).", len(cars))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Refresh failed, writing fallback data: %s", exc)
        save_cars(fallback_cars())


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(refresh_cars, "interval", days=1, id="encar_daily_refresh", replace_existing=True)
    scheduler.start()
