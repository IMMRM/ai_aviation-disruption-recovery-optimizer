import pandas as pd
import streamlit as st
import plotly.express as px
from config.settings import DATABASE_URL

from sqlalchemy import create_engine

from src.optimization.optimize_recovery import (
    optimize_recovery
)

# ============================================================
# DATABASE CONFIG
# ============================================================



engine = create_engine(DATABASE_URL)

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Aviation Recovery Control Tower",
    page_icon="✈️",
    layout="wide"
)

st.title(
    "✈️ Aviation Recovery Control Tower"
)

st.markdown(
    """
    Recovery Optimization Platform for
    Private Aviation Operations
    """
)

# ============================================================
# DATA LOADERS
# ============================================================

@st.cache_data
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

    return pd.read_sql(
        query,
        engine
    )


@st.cache_data
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

    return pd.read_sql(
        query,
        engine
    )

# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3 = st.tabs(
    [
        "📅 Flight Schedule",
        "⚠️ Disrupted Flights",
        "🚀 Recovery Optimizer"
    ]
)

# ============================================================
# TAB 1
# FLIGHT SCHEDULE
# ============================================================

with tab1:

    st.header(
        "Flight Schedule"
    )

    flights_df = load_flights()

    st.subheader(
        "Scheduled Flights"
    )

    st.dataframe(
        flights_df,
        use_container_width=True
    )

    st.divider()

    st.subheader(
        "Aircraft Rotation Timeline"
    )

    gantt_df = flights_df.copy()

    gantt_df["dep_time"] = pd.to_datetime(
        gantt_df["dep_time"]
    )

    gantt_df["arr_time"] = pd.to_datetime(
        gantt_df["arr_time"]
    )

    fig = px.timeline(
    gantt_df,
    x_start="dep_time",
    x_end="arr_time",
    y="assigned_aircraft",
    color="departure_airport",
    text="flight_id",
    hover_data=[
        "flight_id",
        "arrival_airport",
        "passenger_count"
    ]
    )

    fig.update_yaxes(
        autorange="reversed"
    )
    fig.update_traces(

    textposition="inside",

    textfont=dict(
        size=20
    )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ============================================================
# TAB 2
# DISRUPTIONS
# ============================================================

with tab2:

    st.header(
        "Active Disruptions"
    )

    disruptions_df = (
        load_disruptions()
    )

    active_count = len(
        disruptions_df
    )

    critical_count = len(

        disruptions_df[
            disruptions_df["severity"]
            == "CRITICAL"
        ]
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Active Disruptions",
            active_count
        )

    with col2:

        st.metric(
            "Critical Events",
            critical_count
        )

    st.divider()

    # ============================================================
    # SEVERITY STYLING
    # ============================================================

    def color_severity(value):

        if value == "CRITICAL":

            return (
                "background-color: #8B0000;"
                "color: white;"
                "font-weight: bold;"
            )

        elif value == "HIGH":

            return (
                "background-color: #B8860B;"
                "color: white;"
                "font-weight: bold;"
            )

        elif value == "MEDIUM":

            return (
                "background-color: #556B2F;"
                "color: white;"
                "font-weight: bold;"
            )

        elif value == "LOW":

            return (
                "background-color: #006400;"
                "color: white;"
                "font-weight: bold;"
            )

        return ""


    styled_df = (
        disruptions_df.style.map(
            color_severity,
            subset=["severity"]
        )
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True
    )

# ============================================================
# TAB 3
# OPTIMIZER
# ============================================================

with tab3:

    st.header(
        "Recovery Optimization"
    )

    st.markdown(
        """
        Generate optimal aircraft
        recovery assignments.
        """
    )

    if st.button(
        "Run Recovery Optimization",
        type="primary"
    ):

        with st.spinner(
            "Optimizing recovery plan..."
        ):

            assignments = (
                optimize_recovery()
            )

        results = []

        total_cost = 0

        for assignment in assignments:

            total_cost += (
                assignment.recovery_cost
            )

            results.append({

                "Flight":
                    assignment.flight_id,

                "Recovery Aircraft":
                    assignment.aircraft_id,

                "Recovery Cost":
                    f"${assignment.recovery_cost:,.0f}"
            })

        results_df = pd.DataFrame(
            results
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Flights Recovered",
                len(assignments)
            )

        with col2:

            st.metric(
                "Total Network Cost",
                f"${total_cost:,.0f}"
            )

        st.divider()

        st.subheader(
            "Optimal Recovery Plan"
        )

        st.dataframe(
            results_df,
            use_container_width=True
        )

        st.divider()

        st.info(
            """
            GenAI Recovery Explanation
            will be added in Phase 3.
            """
        )