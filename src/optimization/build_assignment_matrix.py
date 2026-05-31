from dataclasses import dataclass
from collections import defaultdict
from typing import List, Dict

from sqlalchemy.orm import Session

from src.database.session import SessionLocal

from models.disruption import Disruption

from src.recovery.recovery_cost_model import (
    get_disrupted_flight_details,
    get_feasible_recovery_candidates,
    calculate_total_recovery_cost,
)

# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class AssignmentOption:

    flight_id: str

    aircraft_id: str

    recovery_cost: float

    estimated_delay: int

    sla_impact: float

    proximity_score: int


# ============================================================
# BUILDER
# ============================================================

class AssignmentMatrixBuilder:

    def __init__(self, db: Session):

        self.db = db

    # ========================================================
    # ACTIVE DISRUPTIONS
    # ========================================================

    def get_active_disruptions(self):

        return (
            self.db.query(Disruption)
            .filter(
                Disruption.resolved.is_(False)
            )
            .all()
        )

    # ========================================================
    # AIRCRAFT ALREADY IN DISRUPTION
    # ========================================================

    def get_unavailable_aircraft_ids(self):

        disruptions = self.get_active_disruptions()

        return {
            disruption.aircraft_id
            for disruption in disruptions
            if disruption.aircraft_id
        }

    # ========================================================
    # BUILD ASSIGNMENT MATRIX
    # ========================================================

    def build(self) -> List[AssignmentOption]:

        assignment_matrix = []

        disruptions = self.get_active_disruptions()

        unavailable_aircraft_ids = (
            self.get_unavailable_aircraft_ids()
        )

        for disruption in disruptions:

            flight_id = disruption.flight_id

            disrupted_flight = (
                get_disrupted_flight_details(
                    self.db,
                    flight_id
                )
            )

            candidates = (
                get_feasible_recovery_candidates(
                    self.db,
                    disrupted_flight
                )
            )

            for candidate in candidates:

                # ------------------------------------
                # Skip aircraft already disrupted
                # ------------------------------------

                if (
                    candidate["aircraft_id"]
                    in unavailable_aircraft_ids
                ):
                    continue

                cost_details = (
                    calculate_total_recovery_cost(
                        self.db,
                        flight_id,
                        candidate
                    )
                )

                option = AssignmentOption(

                    flight_id=flight_id,

                    aircraft_id=
                    candidate["aircraft_id"],

                    recovery_cost=
                    cost_details[
                        "total_recovery_cost"
                    ],

                    estimated_delay=
                    cost_details[
                        "estimated_delay_minutes"
                    ],

                    sla_impact=
                    cost_details[
                        "sla_impact"
                    ],

                    proximity_score=
                    cost_details[
                        "proximity_score"
                    ],
                )

                assignment_matrix.append(
                    option
                )

        flight_counts = defaultdict(int)

        for row in assignment_matrix:

            flight_counts[
                row.flight_id
            ] += 1

        print("\n")
        print("=" * 70)
        print("CANDIDATES PER DISRUPTED FLIGHT")
        print("=" * 70)

        for flight_id, count in sorted(
            flight_counts.items()
        ):

            print(
                f"{flight_id} -> {count}"
            )

        print("=" * 70)



        return assignment_matrix

    # ========================================================
    # GROUP BY FLIGHT
    # ========================================================

    def build_grouped(self):

        matrix = self.build()

        grouped = defaultdict(list)

        for option in matrix:

            grouped[
                option.flight_id
            ].append(option)

        return grouped


# ============================================================
# PUBLIC API
# ============================================================

def build_assignment_matrix():

    db = SessionLocal()

    try:

        builder = (
            AssignmentMatrixBuilder(db)
        )
        

        return builder.build()

    finally:

        db.close()


def build_grouped_assignment_matrix():

    db = SessionLocal()

    try:

        builder = (
            AssignmentMatrixBuilder(db)
        )

        return builder.build_grouped()

    finally:

        db.close()


# ============================================================
# SUMMARY REPORT
# ============================================================

def print_summary(matrix):

    unique_flights = {
        row.flight_id
        for row in matrix
    }

    print("\n")
    print("=" * 80)
    print("ASSIGNMENT MATRIX SUMMARY")
    print("=" * 80)

    print(
        f"Disrupted Flights: "
        f"{len(unique_flights)}"
    )

    print(
        f"Feasible Assignments: "
        f"{len(matrix)}"
    )

    if unique_flights:

        avg_candidates = (
            len(matrix)
            / len(unique_flights)
        )

        print(
            f"Average Candidates/Flight: "
            f"{avg_candidates:.2f}"
        )

    print("=" * 80)


# ============================================================
# DISPLAY MATRIX
# ============================================================

def display_matrix(matrix):

    print("\n")
    print("=" * 120)
    print("ASSIGNMENT MATRIX")
    print("=" * 120)

    for option in matrix:

        print(

            f"Flight={option.flight_id} | "
            f"Aircraft={option.aircraft_id} | "
            f"Cost=${option.recovery_cost:,.0f} | "
            f"Delay={option.estimated_delay} mins | "
            f"SLA=${option.sla_impact:,.0f} | "
            f"Proximity={option.proximity_score}"

        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    matrix = build_assignment_matrix()

    print_summary(matrix)

    display_matrix(matrix)