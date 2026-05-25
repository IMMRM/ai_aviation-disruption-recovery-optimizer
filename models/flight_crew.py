# ============================================================
# src/models/flight_crew.py
# ============================================================

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey
)

from sqlalchemy.orm import relationship

from models.base import Base


class FlightCrew(Base):

    __tablename__ = "flight_crew"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    flight_id = Column(
        String(20),
        ForeignKey("flights.flight_id")
    )

    crew_id = Column(
        String(20),
        ForeignKey("crew.crew_id")
    )

    assigned_role = Column(
        String(30)
    )

    flight = relationship(
        "Flight"
    )

    crew = relationship(
        "Crew"
    )