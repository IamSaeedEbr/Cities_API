from sqlalchemy import Column, Integer, String, UniqueConstraint
from database import Base

class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=False, index=True)
    country_code = Column(String, nullable=False, index=True)

    __table_args__ = (UniqueConstraint('city', name='uq_city'),)
