# ============================================================
# recovery_cost_model.py (ORM VERSION)
# ============================================================
# PURPOSE:
#
# This module:
# - uses SQLAlchemy ORM
# - calculates recovery costs
# - ranks recovery candidates
# - prepares optimization-ready scoring
# ============================================================

from sqlalchemy.orm import Session
from sqlalchemy import func

# ============================================================
# IMPORT ORM MODELS
# ============================================================

# UPDATE THESE IMPORTS
# according to your project structure

from src.database.session import SessionLocal

from models.aircraft import Aircraft
from models.flight import Flight
from models.customer import Customer
from models.flight_customer import FlightCustomer
from models.airport_proximity import AirportProximity
from src.recovery.schedule_feasiblity import ScheduleFeasibilityChecker

# ============================================================
# CONFIGURABLE COST PARAMETERS
# ============================================================

REPOSITION_COST_MULTIPLIER = 1000

DELAY_COST_PER_MINUTE = 100


# ============================================================
# GET DB SESSION
# ============================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()

# ============================================================
# STEP 1 — GET DISRUPTED FLIGHT DETAILS
# ============================================================

def get_disrupted_flight_details(
    db: Session,
    flight_id: str
):

    flight = (
        db.query(Flight)
        .filter(
            Flight.flight_id == flight_id
        )
        .first()
    )

    if not flight:

        raise Exception(
            f"Flight {flight_id} not found."
        )

    aircraft = (
        db.query(Aircraft)
        .filter(
            Aircraft.aircraft_id
            == flight.assigned_aircraft
        )
        .first()
    )

    return {

        "flight_id":
            flight.flight_id,

        "departure_airport":
            flight.departure_airport,

        "arrival_airport":
            flight.arrival_airport,

        "dep_time":
            flight.dep_time,

        "arr_time":
            flight.arr_time,

        "assigned_aircraft":
            flight.assigned_aircraft,

        "passenger_count":
            flight.passenger_count,

        "capacity":
            aircraft.capacity,
        
        "flight_orm":
            flight
    }

# ============================================================
# STEP 2 — GET FEASIBLE RECOVERY CANDIDATES
# ============================================================

def get_feasible_recovery_candidates(
    db: Session,
    disrupted_flight: dict
):

    departure_airport = (
        disrupted_flight[
            "departure_airport"
        ]
    )

    passenger_count = (
        disrupted_flight[
            "passenger_count"
        ]
    )

    failed_aircraft = (
        disrupted_flight[
            "assigned_aircraft"
        ]
    )
    
    flight=disrupted_flight["flight_orm"]

    results = (

        db.query(
            Aircraft,
            AirportProximity.proximity_score
        )

        .join(
            AirportProximity,
            Aircraft.current_airport
            ==
            AirportProximity.target_airport
        )

        .filter(
            AirportProximity.source_airport
            ==
            departure_airport
        )

        .filter(
            Aircraft.status == "AVAILABLE"
        )

        .filter(
            Aircraft.maintenance_due == False
        )

        .filter(
            Aircraft.capacity
            >= passenger_count
        )

        .filter(
            Aircraft.aircraft_id
            != failed_aircraft
        )

        .order_by(
            AirportProximity.proximity_score.asc()
        )

        .all()
    )

    candidates = []

    for aircraft, proximity_score in results:

        feasibility = (
            ScheduleFeasibilityChecker.check(
                flight=flight,
                aircraft=aircraft,
                proximity_score=proximity_score
            )
        )

        if not feasibility.feasible:

            print(
                f"{aircraft.aircraft_id} rejected"
                f" | reason={feasibility.reason}"
            )

            continue

        candidates.append({

            "aircraft_id":
                aircraft.aircraft_id,

            "aircraft_type":
                aircraft.aircraft_type,

            "capacity":
                aircraft.capacity,

            "current_airport":
                aircraft.current_airport,

            "proximity_score":
                proximity_score,

            "reposition_minutes":
                feasibility.reposition_minutes,

            "available_from":
                aircraft.available_from,

            "required_ready_time":
                feasibility.required_ready_time
        })

    return candidates
    
    return candidates

# ============================================================
# STEP 3 — CALCULATE REPOSITION COST
# ============================================================

def calculate_reposition_cost(
    proximity_score: int
):

    return (
        proximity_score
        * REPOSITION_COST_MULTIPLIER
    )

# ============================================================
# STEP 4 — ESTIMATE RECOVERY DELAY
# ============================================================

def estimate_recovery_delay(
    candidate: dict,
    disrupted_flight: dict
):

    required_ready_time = (
        candidate["required_ready_time"]
    )

    scheduled_departure = (
        disrupted_flight["dep_time"]
    )

    if required_ready_time <= scheduled_departure:

        return 0

    delay_minutes = (

        required_ready_time
        -
        scheduled_departure

    ).total_seconds() / 60

    return int(delay_minutes)
# ============================================================
# STEP 5 — CALCULATE DELAY PENALTY
# ============================================================

def calculate_delay_penalty(
    estimated_delay_minutes: int
):

    return (
        estimated_delay_minutes
        * DELAY_COST_PER_MINUTE
    )

# ============================================================
# STEP 6 — CALCULATE SLA IMPACT
# ============================================================

def calculate_sla_impact(
    db: Session,
    flight_id: str
):

    total_sla_impact = (

        db.query(
            func.coalesce(
                func.sum(
                    Customer.sla_penalty
                ),
                0
            )
        )

        .join(
            FlightCustomer,
            FlightCustomer.customer_id
            ==
            Customer.customer_id
        )

        .filter(
            FlightCustomer.flight_id
            ==
            flight_id
        )

        .scalar()
    )

    return total_sla_impact

# ============================================================
# STEP 7 — CALCULATE TOTAL RECOVERY COST
# ============================================================

def calculate_total_recovery_cost(
    db: Session,
    flight_id: str,
    candidate: dict
):

    proximity_score = (
        candidate[
            "proximity_score"
        ]
    )

    reposition_cost = (
        calculate_reposition_cost(
            proximity_score
        )
    )

    disrupted_flight = (
    get_disrupted_flight_details(
        db,
        flight_id
    )
)

    estimated_delay = (
        estimate_recovery_delay(
            candidate,
            disrupted_flight
        )
    )

    delay_penalty = (
        calculate_delay_penalty(
            estimated_delay
        )
    )

    sla_impact = (
        calculate_sla_impact(
            db,
            flight_id
        )
    )

    total_cost = (

        reposition_cost
        + delay_penalty
        + sla_impact
    )

    return {

        "candidate_aircraft":
            candidate["aircraft_id"],

        "candidate_airport":
            candidate["current_airport"],

        "proximity_score":
            proximity_score,

        "reposition_cost":
            reposition_cost,

        "estimated_delay_minutes":
            estimated_delay,

        "delay_penalty":
            delay_penalty,

        "sla_impact":
            sla_impact,

        "total_recovery_cost":
            total_cost
    }

# ============================================================
# STEP 8 — RANK RECOVERY OPTIONS
# ============================================================

def rank_recovery_options(
    db: Session,
    flight_id: str
):

    disrupted_flight = (
        get_disrupted_flight_details(
            db,
            flight_id
        )
    )

    candidates = (
        get_feasible_recovery_candidates(
            db,
            disrupted_flight
        )
    )

    scored_candidates = []

    for candidate in candidates:

        scored = (
            calculate_total_recovery_cost(
                db,
                flight_id,
                candidate
            )
        )

        scored_candidates.append(
            scored
        )

    ranked = sorted(
        scored_candidates,
        key=lambda x:
            x["total_recovery_cost"]
    )

    return ranked

# ============================================================
# STEP 9 — DISPLAY RESULTS
# ============================================================

def display_ranked_options(
    ranked_options
):

    print("\n")
    print("=" * 70)
    print("RANKED RECOVERY OPTIONS")
    print("=" * 70)

    for idx, option in enumerate(
        ranked_options,
        start=1
    ):

        print(f"\nOPTION #{idx}")

        print(
            f"Aircraft: "
            f"{option['candidate_aircraft']}"
        )

        print(
            f"Airport: "
            f"{option['candidate_airport']}"
        )

        print(
            f"Proximity Score: "
            f"{option['proximity_score']}"
        )

        print(
            f"Estimated Delay: "
            f"{option['estimated_delay_minutes']} mins"
        )

        print(
            f"Reposition Cost: "
            f"${option['reposition_cost']:,}"
        )

        print(
            f"Delay Penalty: "
            f"${option['delay_penalty']:,}"
        )

        print(
            f"SLA Impact: "
            f"${option['sla_impact']:,}"
        )

        print(
            f"TOTAL RECOVERY COST: "
            f"${option['total_recovery_cost']:,}"
        )

# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    db = next(get_db())

    disrupted_flight_id = "FL_0054"

    ranked_options = (
        rank_recovery_options(
            db,
            disrupted_flight_id
        )
    )

    display_ranked_options(
        ranked_options
    )