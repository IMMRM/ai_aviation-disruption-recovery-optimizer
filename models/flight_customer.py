# ============================================================
# src/models/flight_customer.py
# ============================================================

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey
)

from sqlalchemy.orm import relationship

from models.base import Base


class FlightCustomer(Base):

    __tablename__ = "flight_customers"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    flight_id = Column(
        String(20),
        ForeignKey("flights.flight_id")
    )

    customer_id = Column(
        String(20),
        ForeignKey("customers.customer_id")
    )

    booking_status = Column(
        String(30),
        default="CONFIRMED"
    )

    flight = relationship(
        "Flight"
    )

    customer = relationship(
        "Customer"
    )