from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable


# ============================================================
# CONFIG
# ============================================================

TURNAROUND_BUFFER_MINUTES = 30


# ============================================================
# RESULT DTO
# ============================================================

@dataclass(frozen=True)
class ConflictResult:

    has_conflict: bool

    reason: str

    conflicting_flight_id: str | None = None


# ============================================================
# AIRCRAFT CONFLICT DETECTOR
# ============================================================

class AircraftConflictDetector:

    @staticmethod
    def has_time_overlap(
        start_a: datetime,
        end_a: datetime,
        start_b: datetime,
        end_b: datetime
    ) -> bool:
        """
        Standard interval overlap check.

        Example:

        A: 13:00 -> 15:00
        B: 14:00 -> 16:00

        overlap = True
        """

        return (
            start_a < end_b
            and
            start_b < end_a
        )

    @staticmethod
    def has_operational_overlap(
        existing_flight,
        recovery_flight
    ) -> bool:
        """
        Uses turnaround buffer.

        Existing flight:

        dep ---- arr ---- turnaround

        Recovery flight:

        dep ---- arr

        If recovery departs before
        turnaround completes,
        we have a conflict.
        """

        existing_start = (
            existing_flight.dep_time
        )

        existing_end = (

            existing_flight.arr_time

            + timedelta(
                minutes=
                TURNAROUND_BUFFER_MINUTES
            )
        )

        recovery_start = (
            recovery_flight.dep_time
        )

        recovery_end = (
            recovery_flight.arr_time
        )

        return (
            AircraftConflictDetector
            .has_time_overlap(
                existing_start,
                existing_end,
                recovery_start,
                recovery_end
            )
        )

    @staticmethod
    def detect_conflict(
        recovery_flight,
        existing_flights: Iterable
    ) -> ConflictResult:
        """
        Check if recovery flight conflicts
        with any already scheduled flight
        for the same aircraft.
        """

        for flight in existing_flights:

            if (
                AircraftConflictDetector
                .has_operational_overlap(
                    existing_flight=flight,
                    recovery_flight=recovery_flight
                )
            ):

                return ConflictResult(

                    has_conflict=True,

                    reason=
                    "SCHEDULE_CONFLICT",

                    conflicting_flight_id=
                    flight.flight_id
                )

        return ConflictResult(

            has_conflict=False,

            reason="NO_CONFLICT"
        )