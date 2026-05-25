# ============================================================
# src/models/aircraft.py
# ============================================================

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    TIMESTAMP
)

from sqlalchemy.sql import func

from models.base import Base


class Aircraft(Base):

    __tablename__ = "aircraft"

    aircraft_id = Column(
        String(20),
        primary_key=True
    )

    aircraft_type = Column(
        String(100),
        nullable=False
    )

    capacity = Column(
        Integer,
        nullable=False
    )

    current_airport = Column(
        String(10),
        nullable=False
    )

    maintenance_due = Column(
        Boolean,
        default=False
    )

    status = Column(
        String(30),
        nullable=False
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )