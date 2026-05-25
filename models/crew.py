# ============================================================
# src/models/crew.py
# ============================================================

from sqlalchemy import (
    Column,
    String,
    DECIMAL,
    TIMESTAMP
)

from sqlalchemy.sql import func

from models.base import Base


class Crew(Base):

    __tablename__ = "crew"

    crew_id = Column(
        String(20),
        primary_key=True
    )

    crew_name = Column(
        String(100)
    )

    role = Column(
        String(30),
        nullable=False
    )

    current_airport = Column(
        String(10)
    )

    duty_remaining_hours = Column(
        DECIMAL(5, 2),
        nullable=False
    )

    status = Column(
        String(30),
        default="AVAILABLE"
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )