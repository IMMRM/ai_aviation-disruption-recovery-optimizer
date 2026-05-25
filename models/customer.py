# ============================================================
# src/models/customer.py
# ============================================================

from sqlalchemy import (
    Column,
    String,
    DECIMAL,
    TIMESTAMP
)

from sqlalchemy.sql import func

from models.base import Base


class Customer(Base):

    __tablename__ = "customers"

    customer_id = Column(
        String(20),
        primary_key=True
    )

    customer_name = Column(
        String(100)
    )

    tier = Column(
        String(30),
        nullable=False
    )

    sla_penalty = Column(
        DECIMAL(12, 2),
        default=0
    )

    created_at = Column(
        TIMESTAMP,
        server_default=func.now()
    )