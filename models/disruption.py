# ============================================================
# src/models/disruption.py
# ============================================================

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    TIMESTAMP,
    ForeignKey,
    Text
)

from sqlalchemy.orm import relationship

from sqlalchemy.sql import func

from models.base import Base


class Disruption(Base):

    __tablename__ = "disruptions"

    disruption_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    disruption_type = Column(
        String(50),
        nullable=False
    )

    aircraft_id = Column(
        String(20),
        ForeignKey("aircraft.aircraft_id")
    )

    flight_id = Column(
        String(20),
        ForeignKey("flights.flight_id")
    )

    severity = Column(
        String(20),
        nullable=False
    )

    disruption_time = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    description = Column(Text)

    resolved = Column(
        Boolean,
        default=False
    )

    aircraft = relationship(
        "Aircraft"
    )

    flight = relationship(
        "Flight"
    )