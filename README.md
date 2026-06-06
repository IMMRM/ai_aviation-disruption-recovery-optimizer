# ✈️ Aviation Recovery AI

An AI-driven aviation disruption recovery platform that simulates real-world airline operations and intelligently recommends optimal aircraft recovery plans during operational disruptions.

The system combines:

- Operations Research (Google OR-Tools)
- Optimization Modeling
- Recovery Cost Analysis
- Aviation Scheduling Constraints
- Generative AI Copilot (Groq LLM)
- Interactive Streamlit Control Tower Dashboard

---

# Problem Statement

Airlines and private aviation operators frequently face disruptions caused by:

- Aircraft maintenance issues
- Technical failures
- Operational delays
- Aircraft unavailability
- Network scheduling conflicts

When disruptions occur, operations teams must quickly answer:

- Which aircraft can replace the failed aircraft?
- Which option minimizes operational impact?
- What is the recovery cost?
- Which flights should be prioritized?
- Why was a specific recovery decision made?

Traditionally, this process is highly manual and time-sensitive.

This project demonstrates how Optimization + GenAI can assist operations teams in making faster and more explainable recovery decisions.

---

# Solution Overview

The platform simulates an aviation network and automatically:

1. Detects disrupted flights
2. Generates feasible recovery aircraft candidates
3. Evaluates schedule feasibility
4. Calculates recovery costs
5. Optimizes aircraft assignments using OR-Tools
6. Produces a network-wide recovery plan
7. Explains recovery decisions using an AI Copilot

---

# System Architecture

```text
                     ┌─────────────────┐
                     │ Operational Data│
                     └────────┬────────┘
                              │
                              ▼
                   ┌────────────────────┐
                   │ Disruption Events  │
                   └────────┬───────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │ Candidate Generation    │
                └────────┬────────────────┘
                         │
                         ▼
              ┌────────────────────────────┐
              │ Schedule Feasibility Check │
              └────────┬───────────────────┘
                       │
                       ▼
              ┌────────────────────────────┐
              │ Recovery Cost Modeling     │
              └────────┬───────────────────┘
                       │
                       ▼
              ┌────────────────────────────┐
              │ OR-Tools Optimizer         │
              └────────┬───────────────────┘
                       │
                       ▼
              ┌────────────────────────────┐
              │ Recovery Plan              │
              └────────┬───────────────────┘
                       │
                       ▼
              ┌────────────────────────────┐
              │ GenAI Recovery Copilot     │
              └────────────────────────────┘
```

---

# Key Features

## Flight Network Simulation

Synthetic aviation environment containing:

- Airports
- Aircraft
- Flights
- Customers
- Disruptions
- Recovery resources

---

## Disruption Recovery

Supports disruptions such as:

- Technical Failure
- Maintenance Events
- Aircraft Unavailability

---

## Feasibility Validation

Ensures recovery aircraft satisfy:

- Capacity requirements
- Availability constraints
- Repositioning constraints
- Turnaround requirements
- Conflict-free schedules

---

## Recovery Cost Modeling

Recovery cost considers:

### Reposition Cost

Cost of moving aircraft to disruption location.

### Delay Penalty

Operational delay impact.

### SLA Impact

Customer-level contractual penalties.

### Total Recovery Cost

```text
Total Cost =
Reposition Cost
+ Delay Penalty
+ SLA Impact
```

---

## OR-Tools Optimization

Uses Google OR-Tools CP-SAT solver.

Objective:

```text
Minimize Total Network Recovery Cost
```

Subject to:

- One aircraft assigned per disrupted flight
- Aircraft assignment constraints
- Schedule feasibility constraints

---

## GenAI Recovery Copilot

Powered by:

- Groq
- Llama 3.3 70B

Supports natural language questions:

Examples:

```text
Why was AC_022 selected?

Which recovery option was most expensive?

How many flights were recovered?

Summarize the recovery plan.

Which aircraft failed?
```

---

# Technology Stack

## Backend

- Python 3.12
- SQLAlchemy ORM
- PostgreSQL

## Optimization

- Google OR-Tools
- CP-SAT Solver

## AI

- Groq API
- Llama 3.3 70B

## Dashboard

- Streamlit
- Plotly

---

# Project Structure

```text
aviation_recovery_ai/

├── config/
│   └── settings.py

├── models/
│   ├── aircraft.py
│   ├── flight.py
│   ├── disruption.py
│   └── ...

├── src/

│   ├── database/
│   │   └── session.py

│   ├── recovery/
│   │   ├── recovery_cost_model.py
│   │   ├── schedule_feasiblity.py
│   │   └── aircraft_conflict_detector.py

│   ├── optimization/
│   │   ├── build_assignment_matrix.py
│   │   └── optimize_recovery.py

│   ├── genai/
│   │   └── services/
│   │       ├── recovery_chat_service.py
│   │       └── recovery_context_builder.py

├── streamlit/
│   └── app.py

├── generate_operational_data.py

└── README.md
```

---

# Dashboard

## Flight Schedule

Visualizes:

- Flight schedule
- Aircraft rotations
- Network timeline

Features:

- Interactive tables
- Plotly Gantt chart

---

## Disruption Control Center

Displays:

- Active disruptions
- Severity levels
- Aircraft impact

---

## Recovery Optimizer

Generates:

- Optimal recovery assignments
- Recovery cost metrics
- Downloadable recovery plans

---

## Recovery Copilot

Interactive AI assistant for operations teams.

Provides:

- Recovery explanations
- Plan summaries
- Operational insights

---

# Example Recovery Plan

| Flight | Failed Aircraft | Recovery Aircraft | Recovery Cost |
|----------|----------|----------|----------|
| FL_0033 | AC_005 | AC_022 | $31,000 |
| FL_0019 | AC_003 | AC_021 | $57,000 |
| FL_0041 | AC_007 | AC_018 | $29,000 |

---

# Example Copilot Questions

```text
Why was AC_022 selected?

Which disruption had the highest cost?

How many reserve aircraft were used?

Summarize the recovery plan.

Which flights were impacted by maintenance events?
```

---

# Future Enhancements

## Crew Recovery Optimization

Recover crew schedules alongside aircraft.

---

## Passenger Re-accommodation

Recommend passenger recovery actions.

---

## Multi-Day Network Recovery

Optimize across multiple operational days.

---

## Real-Time Streaming Events

Integrate live operational events.

---

## What-If Analysis

Examples:

```text
What if AC_022 becomes unavailable?

What if delay penalties double?
```

---

# Learning Outcomes

This project demonstrates:

- Operations Research
- Constraint Programming
- Optimization Modeling
- Aviation Scheduling
- SQLAlchemy ORM
- PostgreSQL
- Streamlit Development
- GenAI Integration
- Production-Oriented Software Design

---

# Author

IMMRM
ML Engineer | AI Engineering | Optimization | Agentic AI

---

# License

MIT License