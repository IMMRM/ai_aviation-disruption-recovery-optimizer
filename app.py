import pandas as pd
from src.optimization.build_assignment_matrix import build_assignment_matrix
import gradio as gr
import plotly.express as px
from config.settings import DATABASE_URL

from sqlalchemy import create_engine

from src.optimization.optimize_recovery import (
    RecoveryOptimizer
)

from src.genai.services.recovery_chat_service import (
    RecoveryChatService
)

from src.genai.services.recovery_context_builder import (
    RecoveryContextBuilder
)


# ============================================================
# DATABASE CONFIG
# ============================================================

engine = create_engine(DATABASE_URL)

# ============================================================
# APP STATE (module-level, replaces st.session_state)
# ============================================================

app_state = {
    "messages": [],
    "optimization_completed": False,
    "results_df": None,
    "recovery_context": None,
    "total_cost": 0,
    "flights_recovered": 0,
    "enriched_df": None,
}

# ============================================================
# DATA LOADERS  (simple TTL caching via functools)
# ============================================================

import functools, time

_cache = {}

def ttl_cache(ttl=60):
    """Simple TTL cache decorator (replaces @st.cache_data)."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = (fn.__name__, args, tuple(sorted(kwargs.items())))
            cached = _cache.get(key)
            if cached and (time.time() - cached["ts"]) < ttl:
                return cached["value"]
            result = fn(*args, **kwargs)
            _cache[key] = {"value": result, "ts": time.time()}
            return result
        return wrapper
    return decorator


@ttl_cache(ttl=60)
def load_flights():
    query = """
        SELECT
            flight_id,
            assigned_aircraft,
            departure_airport,
            arrival_airport,
            dep_time,
            arr_time,
            passenger_count
        FROM flights
        ORDER BY dep_time
    """
    return pd.read_sql(query, engine)


@ttl_cache(ttl=60)
def load_disruptions():
    query = """
        SELECT
            d.flight_id,
            d.aircraft_id,
            d.disruption_type,
            d.severity,
            d.description,
            d.resolved
        FROM disruptions d
        ORDER BY severity
    """
    return pd.read_sql(query, engine)


# ============================================================
# SEVERITY STYLING  (replaces color_severity / df.style.map)
# ============================================================

_SEVERITY_COLORS = {
    "CRITICAL": ("background-color: #8B0000", "color: white", "font-weight: bold"),
    "HIGH":     ("background-color: #B8860B", "color: white", "font-weight: bold"),
    "MEDIUM":   ("background-color: #556B2F", "color: white", "font-weight: bold"),
    "LOW":      ("background-color: #006400", "color: white", "font-weight: bold"),
}

def _severity_html_table(df: pd.DataFrame) -> str:
    """Render disruptions dataframe as an HTML table with coloured severity cells."""
    rows_html = ""
    for _, row in df.iterrows():
        cells = ""
        for col in df.columns:
            value = row[col]
            if col == "severity" and value in _SEVERITY_COLORS:
                style = "; ".join(_SEVERITY_COLORS[value])
                cells += f'<td style="{style}">{value}</td>'
            else:
                cells += f"<td>{value}</td>"
        rows_html += f"<tr>{cells}</tr>"

    header = "".join(f"<th>{c}</th>" for c in df.columns)
    return (
        "<table style='border-collapse:collapse;width:100%'>"
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        "</table>"
    )


# ============================================================
# TAB 1 — FLIGHT SCHEDULE
# ============================================================

def render_flight_schedule():
    """Returns (dataframe, plotly figure) for the flight schedule tab."""
    flights_df = load_flights()
    gantt_df = flights_df.copy()
    gantt_df["dep_time"] = pd.to_datetime(gantt_df["dep_time"])
    gantt_df["arr_time"] = pd.to_datetime(gantt_df["arr_time"])

    fig = px.timeline(
        gantt_df,
        x_start="dep_time",
        x_end="arr_time",
        y="assigned_aircraft",
        color="departure_airport",
        text="flight_id",
        hover_data=["flight_id", "arrival_airport", "passenger_count"],
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_traces(textposition="inside", textfont=dict(size=20))

    return flights_df, fig


# ============================================================
# TAB 2 — DISRUPTIONS
# ============================================================

def render_disruptions():
    """Returns (active_count, critical_count, html_table) for the disruptions tab."""
    disruptions_df = load_disruptions()
    active_count = len(disruptions_df)
    critical_count = len(disruptions_df[disruptions_df["severity"] == "CRITICAL"])
    table_html = _severity_html_table(disruptions_df)
    return str(active_count), str(critical_count), table_html


# ============================================================
# TAB 3 — RECOVERY OPTIMIZER
# ============================================================

def run_optimization(progress=gr.Progress()):
    """
    Runs the full optimization pipeline.
    Yields status strings (streamed into a Textbox) and, when done,
    populates app_state so the results section can be rendered.
    """
    try:
        progress(0, desc="Building assignment matrix…")
        yield "Building assignment matrix…", "", "", None, gr.update(visible=False), gr.update(visible=False)

        assignment_matrix = build_assignment_matrix()

        if not assignment_matrix:
            yield (
                "✅ No active disruptions — network operating normally",
                "", "", None,
                gr.update(visible=False),
                gr.update(visible=False),
            )
            return

        progress(0.25, desc="Initialising optimizer…")
        yield "Initialising optimizer…", "", "", None, gr.update(visible=False), gr.update(visible=False)

        optimizer = RecoveryOptimizer(assignment_matrix)

        progress(0.50, desc="Running OR-Tools solver…")
        yield "Running OR-Tools solver…", "", "", None, gr.update(visible=False), gr.update(visible=False)

        assignments = optimizer.solve()
        app_state["messages"] = []          # reset chat history on new run

        progress(0.90, desc="Preparing recovery plan…")
        yield "Preparing recovery plan…", "", "", None, gr.update(visible=False), gr.update(visible=False)

        # ---- Build result table ----
        disruptions_df = load_disruptions()
        flights_df = load_flights()

        disrupted_aircraft_lookup = {
            row["flight_id"]: row["aircraft_id"]
            for _, row in disruptions_df.iterrows()
        }

        proximity_lookup = {
            (opt.flight_id, opt.aircraft_id): {
                "proximity_score": opt.proximity_score,
                "estimated_delay": opt.estimated_delay,
                "sla_impact": opt.sla_impact,
            }
            for opt in assignment_matrix
        }

        results = []
        total_cost = 0

        for assignment in assignments:
            total_cost += assignment.recovery_cost
            lookup_key = (assignment.flight_id, assignment.aircraft_id)
            details = proximity_lookup.get(
                lookup_key,
                {"proximity_score": "N/A", "estimated_delay": "N/A", "sla_impact": "N/A"},
            )
            results.append({
                "Flight": assignment.flight_id,
                "Failed Aircraft": disrupted_aircraft_lookup.get(assignment.flight_id, "Unknown"),
                "Recovery Aircraft": assignment.aircraft_id,
                "Recovery Cost": f"${assignment.recovery_cost:,.0f}",
                "Proximity Score": details["proximity_score"],
                "Estimated Delay": details["estimated_delay"],
                "Reposition Minutes": details["estimated_delay"],
                "SLA Impact": details["sla_impact"],
            })

        results_df = pd.DataFrame(results)

        # ---- Build enriched context ----
        enriched_df = results_df.copy()

        disruptions_subset = disruptions_df[["flight_id", "disruption_type", "severity"]].copy()
        disruptions_subset.columns = ["Flight", "Disruption Type", "Severity"]
        enriched_df = enriched_df.merge(disruptions_subset, on="Flight", how="left")

        flights_subset = flights_df[["flight_id", "passenger_count", "departure_airport", "arrival_airport"]].copy()
        flights_subset.columns = ["Flight", "Passenger Count", "Departure Airport", "Arrival Airport"]
        enriched_df = enriched_df.merge(flights_subset, on="Flight", how="left")

        recovery_context = RecoveryContextBuilder.build(enriched_df)

        # ---- Persist to app_state ----
        app_state["optimization_completed"] = True
        app_state["results_df"] = results_df
        app_state["recovery_context"] = recovery_context
        app_state["total_cost"] = total_cost
        app_state["flights_recovered"] = len(assignments)
        app_state["enriched_df"] = enriched_df

        progress(1.0, desc="Optimization complete ✅")

        display_df = results_df[["Flight", "Failed Aircraft", "Recovery Aircraft", "Recovery Cost"]]

        csv_bytes = results_df.to_csv(index=False).encode()

        yield (
            "✅ Optimization Complete",
            str(len(assignments)),
            f"${total_cost:,.0f}",
            display_df,
            gr.update(visible=True),   # copilot button
            gr.update(visible=True),   # download button
        )

    except Exception as e:
        yield (
            f"❌ Optimization Failed\n\n{str(e)}",
            "", "", None,
            gr.update(visible=False),
            gr.update(visible=False),
        )


def get_csv_download():
    """Returns the CSV bytes for the download button."""
    if app_state["results_df"] is not None:
        return app_state["results_df"].to_csv(index=False)
    return ""


# ============================================================
# RECOVERY COPILOT CHAT
# ============================================================

def chat_with_copilot(user_message: str, history: list):
    """
    Handles a single chat turn with the Recovery Copilot.
    `history` is a list of {"role": ..., "content": ...} dicts (Gradio messages format).
    """
    if not user_message.strip():
        return history, ""

    if not app_state.get("recovery_context"):
        bot_reply = (
            "❌ Recovery context is empty. "
            "Please run the optimization first."
        )
        history = history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": bot_reply},
        ]
        return history, ""

    try:
        answer = RecoveryChatService().ask(
            question=user_message,
            recovery_context=app_state["recovery_context"],
        )
    except Exception as e:
        answer = (
            f"❌ Error: {str(e)}\n\n"
            "Please check if the GROQ_API_KEY is configured in your environment."
        )

    history = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": answer},
    ]
    return history, ""


def toggle_copilot(current_visible: bool):
    """Toggles the copilot panel visibility."""
    new_state = not current_visible
    return gr.update(visible=new_state), new_state


# ============================================================
# GRADIO UI
# ============================================================

with gr.Blocks(title="Aviation Recovery Control Tower") as demo:

    # ---- Page title ----
    gr.Markdown("# ✈️ Aviation Recovery Control Tower")
    gr.Markdown("Recovery Optimization Platform for Private Aviation Operations")

    # ---- Tabs ----
    with gr.Tabs():

        # ================================================
        # TAB 1 — FLIGHT SCHEDULE
        # ================================================
        with gr.TabItem("📅 Flight Schedule"):
            gr.Markdown("## Flight Schedule")

            load_flights_btn = gr.Button("🔄 Load / Refresh Flights")

            gr.Markdown("### Scheduled Flights")
            flights_table = gr.Dataframe(
                label="Scheduled Flights",
                interactive=False,
                wrap=True,
            )

            gr.Markdown("### Aircraft Rotation Timeline")
            gantt_chart = gr.Plot(label="Aircraft Rotation Timeline")

            load_flights_btn.click(
                fn=render_flight_schedule,
                inputs=[],
                outputs=[flights_table, gantt_chart],
            )

        # ================================================
        # TAB 2 — DISRUPTIONS
        # ================================================
        with gr.TabItem("⚠️ Disrupted Flights"):
            gr.Markdown("## Active Disruptions")

            load_disruptions_btn = gr.Button("🔄 Load / Refresh Disruptions")

            with gr.Row():
                metric_active = gr.Textbox(
                    label="Active Disruptions",
                    interactive=False,
                )
                metric_critical = gr.Textbox(
                    label="Critical Events",
                    interactive=False,
                )

            gr.Markdown("---")
            disruptions_html = gr.HTML(label="Disruptions Table")

            load_disruptions_btn.click(
                fn=render_disruptions,
                inputs=[],
                outputs=[metric_active, metric_critical, disruptions_html],
            )

        # ================================================
        # TAB 3 — RECOVERY OPTIMIZER
        # ================================================
        with gr.TabItem("🚀 Recovery Optimizer"):
            gr.Markdown("## Recovery Optimization")
            gr.Markdown("Generate optimal aircraft recovery assignments.")

            run_btn = gr.Button(
                "▶️ Run Recovery Optimization",
                variant="primary",
            )

            status_box = gr.Textbox(
                label="Status",
                interactive=False,
                lines=2,
            )

            gr.Markdown("---")

            with gr.Row():
                metric_recovered = gr.Textbox(
                    label="Flights Recovered",
                    interactive=False,
                    visible=False,
                )
                metric_cost = gr.Textbox(
                    label="Total Network Cost",
                    interactive=False,
                    visible=False,
                )

            gr.Markdown("### Optimal Recovery Plan")
            results_table = gr.Dataframe(
                label="Recovery Assignments",
                interactive=False,
                visible=False,
                wrap=True,
            )

            with gr.Row():
                copilot_btn = gr.Button(
                    "🤖 Recovery Copilot",
                    visible=False,
                )
                download_btn = gr.DownloadButton(
                    label="📥 Download Recovery Plan",
                    visible=False,
                )

            # ---- Copilot panel (hidden until toggled) ----
            copilot_visible_state = gr.State(False)

            with gr.Column(visible=False) as copilot_panel:
                gr.Markdown("---")
                gr.Markdown("## 🤖 Recovery Copilot")

                with gr.Row():
                    with gr.Column(scale=1):
                        copilot_metric_recovered = gr.Textbox(
                            label="Recovered Flights",
                            interactive=False,
                        )
                    with gr.Column(scale=1):
                        copilot_metric_cost = gr.Textbox(
                            label="Total Cost",
                            interactive=False,
                        )

                gr.Markdown("*Ask questions about the recovery plan.*")

                chatbot = gr.Chatbot(label="Copilot Chat", height=400)
                chat_input = gr.Textbox(
                    placeholder="Ask a question…",
                    label="Your question",
                    lines=1,
                )
                with gr.Row():
                    send_btn = gr.Button("Send", variant="primary")
                    close_btn = gr.Button("❌ Close Copilot")

            # ---- Wire up optimizer ----
            def _run_and_show(progress=gr.Progress()):
                """Wraps run_optimization and also makes metrics visible."""
                for status, recovered, cost, df, copilot_upd, download_upd in run_optimization(progress):
                    if df is not None:
                        yield (
                            status,
                            gr.update(value=recovered, visible=True),
                            gr.update(value=cost, visible=True),
                            gr.update(value=df, visible=True),
                            copilot_upd,
                            download_upd,
                        )
                    else:
                        yield (
                            status,
                            gr.update(visible=False),
                            gr.update(visible=False),
                            gr.update(visible=False),
                            copilot_upd,
                            download_upd,
                        )

            run_btn.click(
                fn=_run_and_show,
                inputs=[],
                outputs=[
                    status_box,
                    metric_recovered,
                    metric_cost,
                    results_table,
                    copilot_btn,
                    download_btn,
                ],
            )

            # ---- Download ----
            def _prepare_download():
                import tempfile
                csv_str = get_csv_download()
                if not csv_str:
                    return None
                tmp = tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".csv",
                    delete=False,
                    prefix="recovery_plan_",
                )
                tmp.write(csv_str)
                tmp.close()
                return tmp.name

            download_btn.click(
                fn=_prepare_download,
                inputs=[],
                outputs=[download_btn],
            )

            # ---- Copilot toggle ----
            def _open_copilot():
                flights_recovered = app_state.get("flights_recovered", 0)
                total_cost = app_state.get("total_cost", 0)
                return (
                    gr.update(visible=True),
                    True,
                    str(flights_recovered),
                    f"${total_cost:,.0f}",
                )

            copilot_btn.click(
                fn=_open_copilot,
                inputs=[],
                outputs=[
                    copilot_panel,
                    copilot_visible_state,
                    copilot_metric_recovered,
                    copilot_metric_cost,
                ],
            )

            def _close_copilot():
                return gr.update(visible=False), False

            close_btn.click(
                fn=_close_copilot,
                inputs=[],
                outputs=[copilot_panel, copilot_visible_state],
            )

            # ---- Chat ----
            send_btn.click(
                fn=chat_with_copilot,
                inputs=[chat_input, chatbot],
                outputs=[chatbot, chat_input],
            )
            chat_input.submit(
                fn=chat_with_copilot,
                inputs=[chat_input, chatbot],
                outputs=[chatbot, chat_input],
            )


# ============================================================
# LAUNCH
# ============================================================

if __name__ == "__main__":
    demo.launch()