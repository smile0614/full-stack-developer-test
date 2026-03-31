import json
import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from app.config import ENCAR_BASE_URL, REQUEST_TIMEOUT_SECONDS
from app.models import Car

ENCAR_API_URL = "https://api.encar.com/search/car/list/general"
ENCAR_IMAGE_BASE_URL = "https://ci.encar.com"
ENCAR_DETAIL_BASE_URL = "https://www.encar.com/dc/dc_cardetailview.do?carid="


def _safe_int(value: str | None) -> int | None:
    if not value:
        return None
    digits = re.sub(r"[^\d]", "", value)
    return int(digits) if digits else None


def _parse_title(title: str) -> tuple[str, str]:
    cleaned = re.sub(r"\s+", " ", title).strip()
    parts = cleaned.split(" ", 1)
    if len(parts) == 1:
        return parts[0], "Unknown model"
    return parts[0], parts[1]


def _build_photo_url(item: dict) -> str:
    photos = item.get("Photos") or []
    if photos and isinstance(photos, list):
        first = photos[0] if photos[0] else {}
        location = first.get("location")
        if isinstance(location, str) and location:
            if location.startswith("http"):
                return location
            return f"{ENCAR_IMAGE_BASE_URL}{location}"

    photo = item.get("Photo")
    if isinstance(photo, str) and photo:
        normalized = photo if photo.endswith(".jpg") else f"{photo}001.jpg"
        return f"{ENCAR_IMAGE_BASE_URL}{normalized}"
    return "https://via.placeholder.com/1200x760?text=No+Image"


def _format_price_krw(raw_price: float | int | None) -> str:
    if raw_price is None:
        return "Price on request"
    try:
        # ENCAR returns price in units of 10,000 KRW.
        krw = int(float(raw_price) * 10000)
        return f"{krw:,} KRW"
    except (TypeError, ValueError):
        return "Price on request"


def _cars_from_api(limit: int) -> list[Car]:
    query = "(And.Hidden.N.)"
    sort_range = f"|ModifiedDate|0|{max(limit * 2, 40)}"
    params = {
        "count": "true",
        "q": query,
        "sr": sort_range,
    }
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    response = requests.get(ENCAR_API_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()
    results = payload.get("SearchResults", [])
    cars: list[Car] = []

    for item in results:
        if not isinstance(item, dict):
            continue
        manufacturer = str(item.get("Manufacturer") or "").strip()
        model = str(item.get("Model") or "").strip()
        badge = str(item.get("Badge") or "").strip()
        year_raw = item.get("Year")
        mileage_raw = item.get("Mileage")
        car_id = str(item.get("Id") or "").strip()

        if not manufacturer or not model or not car_id:
            continue

        year_value = None
        if isinstance(year_raw, (float, int)):
            year_value = int(year_raw) // 100 if int(year_raw) > 9999 else int(year_raw)

        model_name = f"{model} {badge}".strip()
        photo_url = _build_photo_url(item)
        source_url = f"{ENCAR_DETAIL_BASE_URL}{quote(car_id)}"

        cars.append(
            Car(
                brand=manufacturer,
                model=model_name,
                year=year_value,
                mileage_km=int(mileage_raw) if isinstance(mileage_raw, (float, int)) else None,
                price=_format_price_krw(item.get('Price')),
                photo=photo_url,
                source_url=source_url,
            )
        )
        if len(cars) >= limit:
            break
    return cars


def _cars_from_ld_json(soup: BeautifulSoup) -> list[Car]:
    cars: list[Car] = []
    scripts = soup.select("script[type='application/ld+json']")
    for script in scripts:
        if not script.string:
            continue
        try:
            payload = json.loads(script.string)
        except json.JSONDecodeError:
            continue

        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if not isinstance(item, dict):
                continue
            offers = item.get("itemListElement", [])
            for offer in offers:
                obj = offer.get("item", offer) if isinstance(offer, dict) else {}
                if not isinstance(obj, dict):
                    continue
                title = obj.get("name", "Unknown car")
                brand, model = _parse_title(title)
                image = obj.get("image", "https://via.placeholder.com/600x400")
                if isinstance(image, list):
                    image = image[0] if image else "https://via.placeholder.com/600x400"
                price = obj.get("offers", {}).get("price")
                price_currency = obj.get("offers", {}).get("priceCurrency", "KRW")
                year = _safe_int(str(obj.get("productionDate", "")))
                source_url = obj.get("url", ENCAR_BASE_URL)
                if price:
                    price_value = f"{price} {price_currency}"
                else:
                    price_value = "Price on request"

                cars.append(
                    Car(
                        brand=brand,
                        model=model,
                        year=year,
                        mileage_km=None,
                        price=price_value,
                        photo=str(image),
                        source_url=str(source_url),
                    )
                )
    return cars


def _cars_from_html_cards(soup: BeautifulSoup) -> list[Car]:
    cars: list[Car] = []
    cards = soup.select("li, .car-list-item, .vehicle-list-item")
    for card in cards:
        title_node = card.select_one("a, .title, .name")
        if not title_node:
            continue
        title = title_node.get_text(" ", strip=True)
        if len(title) < 3:
            continue

        brand, model = _parse_title(title)
        text = card.get_text(" ", strip=True)
        year_match = re.search(r"(19|20)\d{2}", text)
        mileage_match = re.search(r"(\d[\d,\.]*)\s*(?:km|KM|킬로|km주행)", text)
        price_match = re.search(r"(\d[\d,\.]*)\s*(?:만원|KRW|원|\$)", text)
        image_node = card.select_one("img")
        link_node = card.select_one("a[href]")

        cars.append(
            Car(
                brand=brand,
                model=model,
                year=int(year_match.group(0)) if year_match else None,
                mileage_km=_safe_int(mileage_match.group(1)) if mileage_match else None,
                price=price_match.group(0) if price_match else "Price on request",
                photo=image_node["src"] if image_node and image_node.get("src") else "https://via.placeholder.com/600x400",
                source_url=link_node["href"] if link_node and link_node.get("href") else ENCAR_BASE_URL,
            )
        )
        if len(cars) >= 24:
            break
    return cars


def scrape_encar(limit: int = 24) -> list[Car]:
    try:
        cars = _cars_from_api(limit)
        if cars:
            return cars
    except Exception:  # noqa: BLE001
        pass

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    response = requests.get(
        ENCAR_BASE_URL,
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    cars = _cars_from_ld_json(soup)
    if not cars:
        cars = _cars_from_html_cards(soup)

    unique: list[Car] = []
    seen: set[tuple[str, str, str]] = set()
    for car in cars:
        key = (car.brand, car.model, str(car.source_url))
        if key in seen:
            continue
        seen.add(key)
        unique.append(car)
        if len(unique) >= limit:
            break
    return unique


def fallback_cars() -> list[Car]:
    return [
        Car(
            brand="Mercedes-Benz",
            model="E 300 4MATIC",
            year=2021,
            mileage_km=38000,
            price="59,900,000 KRW",
            photo="https://images.unsplash.com/photo-1549925862-990f9f5f5f4f?auto=format&fit=crop&w=1200&q=80",
            source_url=ENCAR_BASE_URL,
        ),
        Car(
            brand="BMW",
            model="520i M Sport",
            year=2020,
            mileage_km=47000,
            price="48,500,000 KRW",
            photo="https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=1200&q=80",
            source_url=ENCAR_BASE_URL,
        ),
        Car(
            brand="Porsche",
            model="Cayenne Coupe",
            year=2022,
            mileage_km=19000,
            price="108,000,000 KRW",
            photo="https://images.unsplash.com/photo-1616788494707-ec28f08d05a1?auto=format&fit=crop&w=1200&q=80",
            source_url=ENCAR_BASE_URL,
        ),
    ]
