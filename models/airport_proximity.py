# ============================================================
# src/models/airport_proximity.py
# ============================================================

from sqlalchemy import (
    Column,
    String,
    Integer
)

from models.base import Base


class AirportProximity(Base):

    __tablename__ = "airport_proximity"

    source_airport = Column(
        String(10),
        primary_key=True
    )

    target_airport = Column(
        String(10),
        primary_key=True
    )

    proximity_score = Column(
        Integer,
        nullable=False
    )