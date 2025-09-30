import time
import asyncio
from typing import Generator

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

import models, crud, schemas
from database import SessionLocal, engine, Base

from cache import get_from_cache, set_to_cache
from kafka_logger import start_producer, stop_producer, send_log

# create tables (dev convenience)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cities API")

@app.on_event("startup")
async def startup_event():
    app.state.cache_hits = 0
    app.state.cache_total = 0
    try:
        await start_producer()
    except Exception:
        print("⚠️ Kafka not available at startup")

@app.on_event("shutdown")
async def shutdown_event():
    try:
        await stop_producer()
    except Exception:
        pass

# DB dependency
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/city", response_model=schemas.CityResponse)
def create_or_update_city(city: schemas.CityCreate, db: Session = Depends(get_db)):
    """
    Insert if city doesn't exist; if it exists, update country_code.
    Also update cache for this city.
    """
    existing = crud.get_city(db, city.city)
    if existing:
        updated = crud.update_city(db, city.city, city.country_code)
        set_to_cache(city.city, {"id": updated.id, "city": updated.city, "country_code": updated.country_code})
        return updated

    new_city = crud.create_city(db, city)
    set_to_cache(city.city, {"id": new_city.id, "city": new_city.city, "country_code": new_city.country_code})
    return new_city

@app.get("/city/{city_name}", response_model=schemas.CityResponse)
async def read_city(city_name: str, db: Session = Depends(get_db)):
    """
    Try Redis cache first. If hit -> return.
    If miss -> query DB, set cache, return.
    Send a Kafka log (fire-and-forget) with latency, hit/miss, and running hit ratio.
    """
    start = time.time()

    cached = get_from_cache(city_name)
    app.state.cache_total += 1

    if cached:
        app.state.cache_hits += 1
        latency_ms = (time.time() - start) * 1000
        asyncio.create_task(send_log({
            "city": city_name,
            "cache": "hit",
            "latency_ms": latency_ms,
            "hit_ratio": round(app.state.cache_hits / app.state.cache_total, 4)
        }))
        return cached

    db_city = crud.get_city(db, city_name)
    if db_city is None:
        latency_ms = (time.time() - start) * 1000
        asyncio.create_task(send_log({
            "city": city_name,
            "cache": "miss",
            "latency_ms": latency_ms,
            "hit_ratio": round(app.state.cache_hits / app.state.cache_total, 4)
        }))
        raise HTTPException(status_code=404, detail="City not found")

    result = {"id": db_city.id, "city": db_city.city, "country_code": db_city.country_code}
    set_to_cache(city_name, result)

    latency_ms = (time.time() - start) * 1000
    asyncio.create_task(send_log({
        "city": city_name,
        "cache": "miss",
        "latency_ms": latency_ms,
        "hit_ratio": round(app.state.cache_hits / app.state.cache_total, 4)
    }))
    return result
