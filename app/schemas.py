from pydantic import BaseModel

class CityBase(BaseModel):
    city: str
    country_code: str

class CityCreate(CityBase):
    pass

class CityResponse(CityBase):
    id: int

    class Config:
        orm_mode = True
