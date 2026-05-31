from dataclasses import dataclass
from typing import Dict, List

from ortools.sat.python import cp_model

from src.optimization.build_assignment_matrix import (
    AssignmentOption,
    build_assignment_matrix
)

# ============================================================
# SOLUTION DTO
# ============================================================

@dataclass
class RecoveryAssignment:

    flight_id: str

    aircraft_id: str

    recovery_cost: float


# ============================================================
# MODEL BUILDER
# ============================================================

class RecoveryOptimizationModel:

    def __init__(
        self,
        assignment_options: List[AssignmentOption]
    ):

        self.assignment_options = (
            assignment_options
        )

        self.model = cp_model.CpModel()

        self.variables = {}

    # ========================================================
    # CREATE DECISION VARIABLES
    # ========================================================

    def create_decision_variables(self):

        for option in self.assignment_options:

            key = (
                option.flight_id,
                option.aircraft_id
            )

            self.variables[key] = (
                self.model.NewBoolVar(
                    f"x_{option.flight_id}"
                    f"_{option.aircraft_id}"
                )
            )

    # ========================================================
    # CONSTRAINT:
    # ONE AIRCRAFT PER FLIGHT
    # ========================================================

    def add_flight_constraints(self):

        flights = {

            option.flight_id

            for option

            in self.assignment_options
        }

        for flight_id in flights:

            candidate_vars = []

            for option in self.assignment_options:

                if option.flight_id == flight_id:

                    key = (
                        option.flight_id,
                        option.aircraft_id
                    )

                    candidate_vars.append(
                        self.variables[key]
                    )

            self.model.add_exactly_one(
                candidate_vars
            )

    # ========================================================
    # CONSTRAINT:
    # AIRCRAFT CAN ONLY BE USED ONCE
    #
    # MVP VERSION
    # ========================================================

    def add_aircraft_constraints(self):

        aircraft_ids = {

            option.aircraft_id

            for option

            in self.assignment_options
        }

        for aircraft_id in aircraft_ids:

            aircraft_vars = []

            for option in self.assignment_options:

                if option.aircraft_id == aircraft_id:

                    key = (
                        option.flight_id,
                        option.aircraft_id
                    )

                    aircraft_vars.append(
                        self.variables[key]
                    )

            self.model.Add(
                sum(aircraft_vars) <= 1
            )

    # ========================================================
    # OBJECTIVE FUNCTION
    # ========================================================

    def build_objective(self):

        objective_terms = []

        for option in self.assignment_options:

            key = (
                option.flight_id,
                option.aircraft_id
            )

            objective_terms.append(

                self.variables[key]

                * int(
                    option.recovery_cost
                )
            )

        self.model.Minimize(
            sum(objective_terms)
        )

    # ========================================================
    # BUILD MODEL
    # ========================================================

    def build(self):

        self.create_decision_variables()

        self.add_flight_constraints()

        self.add_aircraft_constraints()

        self.build_objective()

        return self.model


# ============================================================
# SOLVER
# ============================================================

class RecoveryOptimizer:

    def __init__(
        self,
        assignment_options: List[AssignmentOption]
    ):

        self.assignment_options = (
            assignment_options
        )

        self.model_builder = (
            RecoveryOptimizationModel(
                assignment_options
            )
        )

    def solve(self):

        model = (
            self.model_builder.build()
        )

        solver = cp_model.CpSolver()

        status = solver.Solve(model)

        if status not in (
            cp_model.OPTIMAL,
            cp_model.FEASIBLE
        ):

            raise Exception(
                "No feasible recovery solution found."
            )

        solution = []

        for option in self.assignment_options:

            key = (
                option.flight_id,
                option.aircraft_id
            )

            variable = (
                self.model_builder
                .variables[key]
            )

            if solver.Value(variable) == 1:

                solution.append(

                    RecoveryAssignment(

                        flight_id=
                        option.flight_id,

                        aircraft_id=
                        option.aircraft_id,

                        recovery_cost=
                        option.recovery_cost
                    )
                )

        return solution


# ============================================================
# REPORTING
# ============================================================

class SolutionReporter:

    @staticmethod
    def display(
        assignments:
        List[RecoveryAssignment]
    ):

        print("\n")
        print("=" * 80)
        print("OPTIMAL RECOVERY PLAN")
        print("=" * 80)

        total_cost = 0

        for assignment in assignments:

            total_cost += (
                assignment.recovery_cost
            )

            print(

                f"Flight: "
                f"{assignment.flight_id}"

                f" -> "

                f"{assignment.aircraft_id}"

                f" | Cost: "
                f"${assignment.recovery_cost:,.0f}"

            )

        print("\n")

        print(
            f"TOTAL NETWORK COST: "
            f"${total_cost:,.0f}"
        )

        print("=" * 80)


# ============================================================
# APPLICATION ENTRYPOINT
# ============================================================

def optimize_recovery():

    assignment_matrix = (
        build_assignment_matrix()
    )
    print(
    f"Rows = {len(assignment_matrix)}")

    optimizer = (
        RecoveryOptimizer(
            assignment_matrix
        )
    )

    assignments = (
        optimizer.solve()
    )

    SolutionReporter.display(
        assignments
    )



    return assignments


if __name__ == "__main__":

    optimize_recovery()