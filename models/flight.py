# ============================================================
# src/models/flight.py
# ============================================================

from sqlalchemy import (
    Column,
    String,
    Integer,
    TIMESTAMP,
    ForeignKey
)

from sqlalchemy.orm import relationship

from sqlalchemy.sql import func

from models.base import Base


class Flight(Base):

    __tablename__ = "flights"

    flight_id = Column(
        String(20),
        primary_key=True
    )

    departure_airport = Column(
        String(10),
        nullable=False
    )

    arrival_airport = Column(
        String(10),
        nullable=False
    )

    dep_time = Column(
        TIMESTAMP,
        nullable=False
    )

    arr_time = Column(
        TIMESTAMP,
        nullable=False
    )

    assigned_aircraft = Column(
        String(20),
        ForeignKey("aircraft.aircraft_id")
    )

    flight_status = Column(
        String(30),
        default="SCHEDULED"
    )

    passenger_count = Column(
        Integer,
        default=0
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    aircraft = relationship(
        "Aircraft"
    )