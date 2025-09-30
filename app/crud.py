from sqlalchemy.orm import Session
import models, schemas

def get_city(db: Session, city_name: str):
    return db.query(models.City).filter(models.City.city == city_name).first()

def create_city(db: Session, city: schemas.CityCreate):
    db_city = models.City(city=city.city, country_code=city.country_code)
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city

def update_city(db: Session, city_name: str, country_code: str):
    db_city = get_city(db, city_name)
    if db_city:
        db_city.country_code = country_code
        db.commit()
        db.refresh(db_city)
    return db_city
