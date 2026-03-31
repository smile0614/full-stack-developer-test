from pydantic import BaseModel, HttpUrl


class Car(BaseModel):
    brand: str
    model: str
    year: int | None = None
    mileage_km: int | None = None
    price: str
    photo: HttpUrl | str
    source_url: HttpUrl | str
