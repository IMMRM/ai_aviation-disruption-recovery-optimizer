import pandas as pd
from src.optimization.build_assignment_matrix import build_assignment_matrix
import streamlit as st
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
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Aviation Recovery Control Tower",
    page_icon="✈️",
    layout="wide"
)
# ============================================================
# CHAT STATE
# ============================================================

if "messages" not in st.session_state:

    st.session_state.messages = []
if "show_copilot" not in st.session_state:

    st.session_state.show_copilot = False

if "optimization_completed" not in st.session_state:

    st.session_state.optimization_completed = False

if "results_df" not in st.session_state:

    st.session_state.results_df = None

if "recovery_context" not in st.session_state:

    st.session_state.recovery_context = None

if "total_cost" not in st.session_state:

    st.session_state.total_cost = 0

if "flights_recovered" not in st.session_state:

    st.session_state.flights_recovered = 0

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

@st.cache_data(ttl=60)
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


@st.cache_data(ttl=60)
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
# RECOVERY OPTIMIZER
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

        try:

            progress_bar = st.progress(0)

            status_text = st.empty()

            # ----------------------------------------------------
            # STEP 1
            # ----------------------------------------------------

            status_text.text(
                "Building assignment matrix..."
            )

            assignment_matrix = (
                build_assignment_matrix()
            )

            # Validate non-empty assignment matrix
            if not assignment_matrix:

                st.info(
                    "✅ No active disruptions - "
                    "network operating normally"
                )

                st.stop()

            progress_bar.progress(25)

            # ----------------------------------------------------
            # STEP 2
            # ----------------------------------------------------

            status_text.text(
                "Initializing optimizer..."
            )

            optimizer = RecoveryOptimizer(
                assignment_matrix
            )

            progress_bar.progress(50)

            # ----------------------------------------------------
            # STEP 3
            # ----------------------------------------------------

            status_text.text(
                "Running OR-Tools solver..."
            )

            assignments = (
                optimizer.solve()
            )
            st.session_state.messages = []

            progress_bar.progress(90)

            # ----------------------------------------------------
            # STEP 4
            # ----------------------------------------------------

            status_text.text(
                "Preparing recovery plan..."
            )

            progress_bar.progress(100)

            status_text.success(
                "Optimization Complete"
            )

            # ====================================================
            # DISRUPTION LOOKUP
            # ====================================================

            disruptions_df = (
                load_disruptions()
            )

            flights_df = (
                load_flights()
            )

            disrupted_aircraft_lookup = {

                row["flight_id"]:
                row["aircraft_id"]

                for _, row
                in disruptions_df.iterrows()
            }

            # ====================================================
            # BUILD RESULT TABLE WITH COST DETAILS
            # ====================================================

            # Create lookup for proximity scores from assignment matrix
            proximity_lookup = {
                (opt.flight_id, opt.aircraft_id): {
                    'proximity_score': opt.proximity_score,
                    'estimated_delay': opt.estimated_delay,
                    'sla_impact': opt.sla_impact
                }
                for opt in assignment_matrix
            }

            results = []

            total_cost = 0

            for assignment in assignments:

                total_cost += (
                    assignment.recovery_cost
                )

                # Get detailed cost info if available
                lookup_key = (
                    assignment.flight_id,
                    assignment.aircraft_id
                )
                details = proximity_lookup.get(
                    lookup_key,
                    {
                        'proximity_score': 'N/A',
                        'estimated_delay': 'N/A',
                        'sla_impact': 'N/A'
                    }
                )

                results.append({

                    "Flight":
                        assignment.flight_id,

                    "Failed Aircraft":
                        disrupted_aircraft_lookup.get(
                            assignment.flight_id,
                            "Unknown"
                        ),

                    "Recovery Aircraft":
                        assignment.aircraft_id,

                    "Recovery Cost":
                        f"${assignment.recovery_cost:,.0f}",

                    "Proximity Score":
                        details['proximity_score'],

                    "Estimated Delay":
                        details['estimated_delay'],

                    "Reposition Minutes":
                        details['estimated_delay'],

                    "SLA Impact":
                        details['sla_impact']
                })

            results_df = pd.DataFrame(
                results
            )
            st.session_state.results_df = results_df

            st.session_state.optimization_completed = True
            
            st.session_state.total_cost = total_cost
            
            st.session_state.flights_recovered = len(
                assignments
            )
            # ============================================================
            # BUILD RECOVERY CONTEXT WITH ENRICHED DATA
            # ============================================================

            # Create enriched dataframe by merging with flight and disruption data
            enriched_df = results_df.copy()

            # Merge with disruptions data (Disruption Type, Severity)
            disruptions_subset = disruptions_df[[
                'flight_id',
                'disruption_type',
                'severity'
            ]].copy()
            disruptions_subset.columns = [
                'Flight',
                'Disruption Type',
                'Severity'
            ]
            enriched_df = enriched_df.merge(
                disruptions_subset,
                on='Flight',
                how='left'
            )

            # Merge with flights data (Passenger Count, Airports)
            flights_subset = flights_df[[
                'flight_id',
                'passenger_count',
                'departure_airport',
                'arrival_airport'
            ]].copy()
            flights_subset.columns = [
                'Flight',
                'Passenger Count',
                'Departure Airport',
                'Arrival Airport'
            ]
            enriched_df = enriched_df.merge(
                flights_subset,
                on='Flight',
                how='left'
            )

            recovery_context = (
                RecoveryContextBuilder.build(
                    enriched_df
                )
            )

            st.session_state.recovery_context = (
                recovery_context
            )

            st.session_state.enriched_df = enriched_df

        except Exception as e:

            st.error(
                f"❌ Optimization Failed\n\n{str(e)}"
            )

            st.stop()

    # ====================================================
    # RENDER RESULTS OUTSIDE BUTTON
    # ====================================================

    if st.session_state.optimization_completed:

        results_df = (
            st.session_state.results_df
        )

        total_cost = (
            st.session_state.total_cost
        )

        flights_recovered = (
            st.session_state.flights_recovered
        )

        st.divider()

        metric_col1, metric_col2 = (
            st.columns(2)
        )

        with metric_col1:

            st.metric(
                "Flights Recovered",
                flights_recovered
            )

        with metric_col2:

            st.metric(
                "Total Network Cost",
                f"${total_cost:,.0f}"
            )

        st.subheader(
            "Optimal Recovery Plan"
        )

        # Display only essential columns
        display_df = results_df[[
            'Flight',
            'Failed Aircraft',
            'Recovery Aircraft',
            'Recovery Cost'
        ]]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        col1, col2 = st.columns([8, 2])

        with col2:

            if st.button(
                "🤖 Recovery Copilot"
            ):

                st.session_state.show_copilot = True

        st.download_button(
            label=
            "📥 Download Recovery Plan",

            data=
            results_df.to_csv(
                index=False
            ),

            file_name=
            "recovery_plan.csv",

            mime=
            "text/csv"
        )
        
# ============================================================
# RECOVERY COPILOT SIDEBAR
# ============================================================

if (
    st.session_state.optimization_completed
    and
    st.session_state.show_copilot
):

    with st.sidebar:

        col1, col2 = st.columns([4, 1])

        with col2:

            if st.button("❌"):

                st.session_state.show_copilot = False
                st.rerun()

        st.header(
            "🤖 Recovery Copilot"
        )

        st.metric(
            "Recovered Flights",
            st.session_state.flights_recovered
        )

        st.metric(
            "Total Cost",
            f"${st.session_state.total_cost:,.0f}"
        )

        st.caption(
            """
            Ask questions about
            the recovery plan.
            """
        )

        for message in st.session_state.messages:

            with st.chat_message(
                message["role"]
            ):

                st.markdown(
                    message["content"]
                )

        question = st.chat_input(
            "Ask a question..."
        )

        if question:

            st.session_state.messages.append({

                "role": "user",

                "content": question
            })

            try:

                with st.spinner(
                    "Thinking..."
                ):

                    # Validate recovery context
                    if not st.session_state.recovery_context:

                        raise ValueError(
                            "Recovery context is empty. "
                            "Please run optimization first."
                        )

                    answer = (

                        RecoveryChatService()

                        .ask(

                            question=question,

                            recovery_context=

                            st.session_state
                            .recovery_context
                        )
                    )

            except Exception as e:

                answer = (
                    f"❌ Error: {str(e)}\n\n"
                    f"Please check if the "
                    f"GROQ_API_KEY is configured "
                    f"in your environment."
                )

            st.session_state.messages.append({

                "role": "assistant",

                "content": answer
            })

            st.rerun()