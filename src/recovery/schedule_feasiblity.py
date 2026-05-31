from dataclasses import dataclass
from datetime import datetime, timedelta

# ============================================================
# CONFIG
# ============================================================

TURNAROUND_BUFFER_MINUTES = 30

REPOSITION_MINUTES_PER_PROXIMITY = 15

# ============================================================
# RESULT DTO
# ============================================================

@dataclass
class FeasibilityResult:

    feasible: bool

    reason: str

    reposition_minutes: int

    turnaround_minutes: int

    required_ready_time: datetime | None

    available_from: datetime | None

# ============================================================
# FEASIBILITY CHECKER
# ============================================================

class ScheduleFeasibilityChecker:

    @staticmethod
    def estimate_reposition_minutes(
        proximity_score: int
    ) -> int:

        return (
            proximity_score
            * REPOSITION_MINUTES_PER_PROXIMITY
        )

    @staticmethod
    def check(
        flight,
        aircraft,
        proximity_score: int
    ) -> FeasibilityResult:

        # ----------------------------------------
        # Aircraft availability unknown
        # ----------------------------------------

        if aircraft.available_from is None:

            return FeasibilityResult(
                feasible=False,
                reason="AIRCRAFT_AVAILABILITY_UNKNOWN",
                reposition_minutes=0,
                turnaround_minutes=0,
                required_ready_time=None,
                available_from=None
            )

        reposition_minutes = (
            ScheduleFeasibilityChecker
            .estimate_reposition_minutes(
                proximity_score
            )
        )

        required_ready_time = (

            aircraft.available_from

            + timedelta(
                minutes=reposition_minutes
            )

            + timedelta(
                minutes=TURNAROUND_BUFFER_MINUTES
            )
        )

        # ----------------------------------------
        # Schedule feasibility
        # ----------------------------------------

        if required_ready_time > flight.dep_time:

            return FeasibilityResult(

                feasible=False,

                reason="INSUFFICIENT_TIME",

                reposition_minutes=
                reposition_minutes,

                turnaround_minutes=
                TURNAROUND_BUFFER_MINUTES,

                required_ready_time=
                required_ready_time,

                available_from=
                aircraft.available_from
            )

        return FeasibilityResult(

            feasible=True,

            reason="FEASIBLE",

            reposition_minutes=
            reposition_minutes,

            turnaround_minutes=
            TURNAROUND_BUFFER_MINUTES,

            required_ready_time=
            required_ready_time,

            available_from=
            aircraft.available_from
        )