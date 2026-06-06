# ✈️ Aviation Recovery Control Tower

> An AI-driven aviation disruption recovery platform that simulates real-world private flight operations and intelligently optimizes aircraft rescheduling during operational disruptions — powered by Google OR-Tools, Groq LLM, and a Gradio web interface.

[![🤗 Live Demo](https://img.shields.io/badge/🤗%20Live%20Demo-Hugging%20Face%20Spaces-orange?style=for-the-badge)](https://huggingface.co/spaces/Mehraj05038/ai_aviation-recovery-control-tower)

---

## Table of Contents

- [Live Demo](#live-demo)
- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Core Modules](#core-modules)
- [Recovery Optimization Pipeline](#recovery-optimization-pipeline)
- [AI Copilot (GenAI)](#ai-copilot-genai)
- [Web Interface](#web-interface)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the App](#running-the-app)
- [Generating Synthetic Data](#generating-synthetic-data)
- [Running Tests](#running-tests)
- [Make Commands](#make-commands)
- [Cost Model](#cost-model)
- [Tech Stack](#tech-stack)
- [License](#license)

---

## Live Demo

The application is deployed and publicly accessible on Hugging Face Spaces:

🔗 **[https://huggingface.co/spaces/Mehraj05038/ai_aviation-recovery-control-tower](https://huggingface.co/spaces/Mehraj05038/ai_aviation-recovery-control-tower)**

No installation required — open the link, click **🔄 Load / Refresh** on any tab to pull live data, and navigate to **🚀 Recovery Optimizer** to run the optimization and chat with the AI Copilot.

---

## Overview

The Aviation Recovery Control Tower is a decision-support system designed for private aviation operations. When an aircraft experiences a disruption (mechanical failure, weather, crew issue), the platform:

1. Detects active disruptions from the database
2. Builds a feasibility-checked assignment matrix of candidate recovery aircraft
3. Solves a constrained optimization problem using OR-Tools CP-SAT to find the minimum-cost recovery plan
4. Presents the results in an interactive Gradio dashboard
5. Enables natural language Q&A about the recovery plan via a Groq-powered AI copilot

The system simulates a fleet of 25 aircraft operating across 7 US airports, with realistic turnaround times, passenger capacity constraints, and SLA-aware cost modelling.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Gradio Web Interface                      │
│   Tab 1: Flight Schedule  |  Tab 2: Disruptions  |  Tab 3   │
│                           Recovery Optimizer                 │
└──────────────────────────────┬──────────────────────────────┘
                               │
              ┌────────────────▼─────────────────┐
              │       Recovery Pipeline           │
              │                                  │
              │  1. build_assignment_matrix()     │
              │     ├─ Query active disruptions   │
              │     ├─ Get feasible candidates    │
              │     └─ Score each (cost model)    │
              │                                  │
              │  2. RecoveryOptimizer.solve()     │
              │     ├─ Build CP-SAT model         │
              │     ├─ Add constraints            │
              │     └─ Minimize total cost        │
              │                                  │
              │  3. RecoveryContextBuilder.build()│
              │     └─ Enrich results for LLM    │
              └────────┬─────────────────────────┘
                       │
         ┌─────────────▼──────────────┐
         │   PostgreSQL (Supabase)    │
         │  aircraft | flights        │
         │  disruptions | customers   │
         │  airport_proximity         │
         └────────────────────────────┘
                       │
         ┌─────────────▼──────────────┐
         │   Groq LLM (AI Copilot)   │
         │   openai/gpt-oss-120b      │
         └────────────────────────────┘
```

---

## Project Structure

```
aviation_recovery_ai/
│
├── app.py                          # Gradio application entry point
│
├── config/
│   ├── settings.py                 # Env-based config (DB URL, Groq key)
│   └── __init__.py
│
├── models/                         # SQLAlchemy ORM models
│   ├── base.py                     # Declarative base
│   ├── aircraft.py                 # Aircraft table
│   ├── flight.py                   # Flights table
│   ├── disruption.py               # Disruptions table
│   ├── customer.py                 # Customers table
│   ├── flight_customer.py          # Flight–customer join table
│   ├── flight_crew.py              # Flight–crew join table
│   ├── crew.py                     # Crew table
│   └── airport_proximity.py        # Airport proximity scores
│
├── src/
│   ├── database/
│   │   └── session.py              # SQLAlchemy session factory
│   │
│   ├── optimization/
│   │   ├── build_assignment_matrix.py   # Candidate scoring & matrix build
│   │   └── optimize_recovery.py         # CP-SAT solver & solution extraction
│   │
│   ├── recovery/
│   │   ├── recovery_cost_model.py       # 9-step cost calculation pipeline
│   │   ├── schedule_feasiblity.py       # Time/reposition feasibility checker
│   │   └── aircraft_conflict_detector.py # Schedule conflict detection
│   │
│   └── genai/
│       └── services/
│           ├── recovery_chat_service.py      # Groq LLM chat interface
│           └── recovery_context_builder.py   # Context string builder for LLM
│
├── generate_operational_data.py    # Synthetic data seeder
├── update_aircraft_availability.py # Aircraft status updater script
├── tests/
│   └── test_data.py                # Database URL and data tests
│
├── data/                           # Raw / interim / processed data folders
├── notebooks/                      # Jupyter notebooks (placeholder)
├── reports/                        # Output reports and figures
├── docs/                           # Additional documentation
│
├── requirements.txt
├── pyproject.toml
├── Makefile
└── .env                            # Local environment variables (not committed)
```

---

## Database Schema

The application connects to a PostgreSQL database (hosted on Supabase). The schema consists of six tables:

### `aircraft`
| Column | Type | Description |
|---|---|---|
| `aircraft_id` | VARCHAR(20) PK | Unique aircraft identifier |
| `aircraft_type` | VARCHAR(100) | e.g. Citation XLS, Gulfstream G650 |
| `capacity` | INTEGER | Max passenger capacity |
| `current_airport` | VARCHAR(10) | ICAO/IATA code of current location |
| `status` | VARCHAR(30) | AVAILABLE / UNAVAILABLE |
| `maintenance_due` | BOOLEAN | Flag for maintenance hold |
| `available_from` | TIMESTAMP | Earliest dispatch time |

### `flights`
| Column | Type | Description |
|---|---|---|
| `flight_id` | VARCHAR(20) PK | Unique flight identifier |
| `departure_airport` | VARCHAR(10) | Origin airport code |
| `arrival_airport` | VARCHAR(10) | Destination airport code |
| `dep_time` | TIMESTAMP | Scheduled departure |
| `arr_time` | TIMESTAMP | Scheduled arrival |
| `assigned_aircraft` | VARCHAR(20) FK | Linked aircraft |
| `flight_status` | VARCHAR(30) | SCHEDULED / DISRUPTED / etc. |
| `passenger_count` | INTEGER | Number of passengers booked |

### `disruptions`
| Column | Type | Description |
|---|---|---|
| `disruption_id` | INTEGER PK (auto) | Unique disruption ID |
| `disruption_type` | VARCHAR(50) | e.g. MECHANICAL, WEATHER |
| `aircraft_id` | VARCHAR(20) FK | Affected aircraft |
| `flight_id` | VARCHAR(20) FK | Affected flight |
| `severity` | VARCHAR(20) | LOW / MEDIUM / HIGH / CRITICAL |
| `description` | TEXT | Free-text description |
| `resolved` | BOOLEAN | Whether disruption is cleared |

### `customers`
| Column | Type | Description |
|---|---|---|
| `customer_id` | VARCHAR(20) PK | Unique customer identifier |
| `customer_name` | VARCHAR(100) | Full name |
| `tier` | VARCHAR(30) | VIP tier level |
| `sla_penalty` | DECIMAL(12,2) | Financial penalty for SLA breach |

### `airport_proximity`
| Column | Type | Description |
|---|---|---|
| `source_airport` | VARCHAR(10) | Origin airport for proximity lookup |
| `target_airport` | VARCHAR(10) | Candidate aircraft's current airport |
| `proximity_score` | INTEGER | Lower = closer; drives reposition cost |

### `flight_customer` / `flight_crew`
Join tables linking flights to customers and crew members respectively.

---

## Core Modules

### `src/recovery/recovery_cost_model.py`

The heart of the candidate scoring system. Implements a 9-step pipeline:

1. **Get disrupted flight details** — fetches flight and aircraft info from the DB
2. **Get feasible recovery candidates** — queries `AVAILABLE` aircraft with sufficient capacity, joined to proximity scores
3. **Calculate reposition cost** — `proximity_score × $1,000`
4. **Estimate recovery delay** — based on aircraft `available_from` + reposition time vs. scheduled departure
5. **Calculate delay penalty** — `delay_minutes × $100`
6. **Calculate SLA impact** — sums `sla_penalty` across all VIP customers on the disrupted flight
7. **Calculate total recovery cost** — `reposition_cost + delay_penalty + sla_impact`
8. **Rank recovery options** — sorted by total cost ascending
9. **Display results** — console output for debugging

### `src/recovery/schedule_feasiblity.py`

Checks whether a candidate aircraft can physically reach and depart on time:

- Estimates reposition time as `proximity_score × 15 minutes`
- Adds a 30-minute turnaround buffer
- Compares `required_ready_time` against flight `dep_time`
- Returns a `FeasibilityResult` dataclass with reason codes

### `src/recovery/aircraft_conflict_detector.py`

Detects schedule conflicts using standard interval overlap logic with a 30-minute turnaround buffer. Used to prevent double-assigning an aircraft that already has an active flight.

### `src/optimization/build_assignment_matrix.py`

Orchestrates the full candidate generation process:

- Queries all unresolved disruptions
- For each disrupted flight, collects feasible candidates
- Skips aircraft that are themselves disrupted
- Scores each (flight, aircraft) pair using the cost model
- Returns a flat list of `AssignmentOption` dataclass objects

### `src/optimization/optimize_recovery.py`

Wraps Google OR-Tools CP-SAT to solve the assignment problem:

- **Decision variables**: binary `x[flight, aircraft]`
- **Constraint 1**: exactly one aircraft assigned per disrupted flight (`add_exactly_one`)
- **Constraint 2**: each aircraft used at most once (`sum ≤ 1`)
- **Objective**: minimize total recovery cost
- Raises an exception if no feasible solution is found

---

## Recovery Optimization Pipeline

When "Run Recovery Optimization" is clicked in the UI, the following steps execute in sequence:

```
Step 1: build_assignment_matrix()
  └─ Query active disruptions
  └─ For each disruption → get feasible candidates → score → AssignmentOption

Step 2: RecoveryOptimizer(assignment_matrix).solve()
  └─ Build CP-SAT model
  └─ Add flight + aircraft constraints
  └─ Minimize total cost
  └─ Extract RecoveryAssignment list

Step 3: Enrich results
  └─ Merge with disruptions (type, severity)
  └─ Merge with flights (passenger count, airports)

Step 4: Build recovery context
  └─ RecoveryContextBuilder.build(enriched_df)
  └─ Structured text context for AI Copilot
```

---

## AI Copilot (GenAI)

### `src/genai/services/recovery_chat_service.py`

Interfaces with the **Groq API** using model `openai/gpt-oss-120b`. The system prompt instructs the model to act as a brief Operations Recovery Analyst answering only from provided recovery data. Handles:

- Assignment rationale questions ("Why was AC_007 assigned?")
- Exclusion questions ("Why wasn't AC_012 used?")
- Cost breakdown questions
- Rate limit and authentication errors gracefully

### `src/genai/services/recovery_context_builder.py`

Builds a structured plain-text context string from the enriched results DataFrame, including for each assignment:

- Selection rationale (proximity, reposition time, cost, SLA impact)
- Disruption details (type, severity, route, passengers)
- Optimization constraints explanation
- Reasons other aircraft were not selected

---

## Web Interface

The Gradio app (`app.py`) has three tabs:

### Tab 1 — 📅 Flight Schedule
- Loads all scheduled flights from the database
- Displays a sortable data table
- Renders an interactive **Plotly Gantt chart** of aircraft rotations by time

### Tab 2 — ⚠️ Disrupted Flights
- Shows active (unresolved) disruptions
- Displays metric counters for total active and critical disruptions
- Renders disruptions in an HTML table with colour-coded severity cells (CRITICAL = dark red, HIGH = dark yellow, MEDIUM = olive, LOW = dark green)

### Tab 3 — 🚀 Recovery Optimizer
- "Run Recovery Optimization" button triggers the full pipeline with a streaming progress status
- Displays recovered flight count and total network cost on completion
- Shows the optimal recovery plan table
- "📥 Download Recovery Plan" button exports results as CSV
- "🤖 Recovery Copilot" button opens an in-page chat panel backed by the Groq LLM

---

## Prerequisites

- Python 3.12
- `uv` (recommended) or `pip`
- PostgreSQL database (Supabase or self-hosted)
- Groq API key (free tier available at [console.groq.com](https://console.groq.com))

---

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd aviation_recovery_ai

# 2. Create a virtual environment
uv venv --python 3.12
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
uv pip install -r requirements.txt
```

> **Note:** The `requirements.txt` uses `-e .` to install the `src` package in editable mode via `flit`. Ensure `pyproject.toml` is present at the project root.

---

## Configuration

Create a `.env` file in the project root with the following variables:

```env
# PostgreSQL connection
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=your_db_name

# Groq LLM API
GROQ_API_KEY=your_groq_api_key
```

The `config/settings.py` module loads these automatically via `python-dotenv` and assembles the `DATABASE_URL`.

---

## Running the App

```bash
python app.py
```

The Gradio server starts on `http://127.0.0.1:7860` by default. Open it in your browser.

Click **"🔄 Load / Refresh"** on Tab 1 or Tab 2 to fetch live data, then navigate to Tab 3 to run the optimizer.

---

## Generating Synthetic Data

The project includes a comprehensive synthetic data generator that produces operationally consistent aviation data — no aircraft teleportation, sequential rotations, realistic turnarounds:

```bash
python generate_operational_data.py
```

**What it generates:**

| Entity | Count |
|---|---|
| Operational aircraft | 20 |
| Reserve aircraft | 5 |
| Flights per aircraft | 5 (sequential rotations) |
| Crew members | 40 |
| Customers | 200 |
| Airports | 7 (JFK, TEB, MIA, LAX, BOS, ORD, DAL) |
| Aircraft types | Citation XLS (8), Phenom 300 (6), Challenger 350 (10), Gulfstream G650 (14) |

To update aircraft availability independently (e.g. after a shift):

```bash
python update_aircraft_availability.py
```

---

## Running Tests

```bash
# Via make
make test

# Or directly
python -m pytest tests
```

The test suite currently covers:

- `test_database_url_percent_encodes_special_characters` — verifies the `DATABASE_URL` assembly from environment variables handles special characters (e.g. `@` → `%40`) correctly

---

## Make Commands

```bash
make requirements      # Install dependencies via uv
make test              # Run pytest
make lint              # Check code style with ruff
make format            # Auto-fix and format with ruff
make clean             # Remove all __pycache__ and .pyc files
make create_environment # Create a new uv virtual environment
```

---

## Cost Model

The total recovery cost for assigning a candidate aircraft to a disrupted flight is:

```
Total Cost = Reposition Cost + Delay Penalty + SLA Impact

Where:
  Reposition Cost  = proximity_score × $1,000
  Delay Penalty    = delay_minutes   × $100
  SLA Impact       = Σ customer.sla_penalty  (for all VIP passengers on the flight)
```

**Proximity score** is a pre-computed integer stored in the `airport_proximity` table. A score of 1 means the aircraft is at the same airport (or nearest hub); higher scores mean farther repositioning.

**Delay** is calculated as the gap between when the aircraft can realistically be ready (`available_from + reposition_time + 30 min turnaround`) and the scheduled departure time. If the aircraft can be ready before departure, delay is 0.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Web UI | Gradio 6.x |
| Data visualization | Plotly Express |
| ORM | SQLAlchemy 2.x |
| Database | PostgreSQL (Supabase) |
| Database driver | psycopg2-binary |
| Optimization solver | Google OR-Tools CP-SAT |
| LLM provider | Groq (`openai/gpt-oss-120b`) |
| Data manipulation | pandas |
| Synthetic data | Faker |
| Linting / formatting | Ruff |
| Testing | pytest |
| Package management | uv + flit |
| Environment config | python-dotenv |

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.