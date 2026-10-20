from pathlib import Path
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent
SRC_DIR = PROJECT_DIR / "src"
OUTPUT_DIR = PROJECT_DIR / "outputs"

sys.path.insert(0, str(SRC_DIR))

from evacuation_simulator import simulate_evacuation

st.set_page_config(
    page_title="YardFlow | Terminal Operations",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("YardFlow")
st.caption("Container Terminal Operations and Disruption Recovery")

st.info(
    "Data integrity notice: Historical Operations uses recorded event-log summaries. "
    "Evacuation Simulation uses configurable simulated demand, fleet capacity, "
    "disruption and recovery assumptions. Simulation outputs are not real terminal observations."
)


def load_csv(filename):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError):
        return None


def show_metric(label, value):
    st.metric(label, value)


with st.sidebar:
    st.header("Simulation Settings")

    total_containers = st.number_input(
        "Total container demand",
        min_value=50,
        max_value=10000,
        value=900,
        step=50
    )

    arrivals_per_hour = st.number_input(
        "Arrivals per hour",
        min_value=1,
        max_value=500,
        value=30
    )

    total_trucks = st.number_input(
        "Baseline trucks",
        min_value=1,
        max_value=100,
        value=8
    )

    service_rate = st.number_input(
        "Containers per truck per hour",
        min_value=1,
        max_value=100,
        value=4
    )

    simulation_limit = st.slider(
        "Simulation limit (hours)",
        min_value=12,
        max_value=120,
        value=48,
        step=12
    )

    st.subheader("Disruption")

    disruption_start = st.slider(
        "Disruption start hour",
        min_value=1,
        max_value=48,
        value=8
    )

    disruption_duration = st.slider(
        "Disruption duration (hours)",
        min_value=1,
        max_value=24,
        value=8
    )

    fleet_availability = st.slider(
        "Fleet availability during disruption",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1,
        format="%.1f"
    )

    st.subheader("Recovery")

    extra_trucks = st.slider(
        "Additional recovery trucks",
        min_value=0,
        max_value=30,
        value=4
    )

    recovery_duration = st.slider(
        "Recovery duration (hours)",
        min_value=1,
        max_value=24,
        value=8
    )

    recovery_multiplier = st.slider(
        "Recovery service multiplier",
        min_value=1.0,
        max_value=2.0,
        value=1.5,
        step=0.1
    )


disruption_end = disruption_start + disruption_duration
recovery_start = disruption_end
recovery_end = recovery_start + recovery_duration

if disruption_end > simulation_limit:
    st.warning(
        "The disruption ends after the simulation limit. "
        "Increase the simulation limit or adjust the disruption settings."
    )

if recovery_end > simulation_limit:
    st.warning(
        "The recovery window extends beyond the simulation limit. "
        "Some recovery actions may not be simulated."
    )

historical_tab, simulation_tab, data_tab = st.tabs(
    ["Historical Operations", "Evacuation Simulation", "Data Quality"]
)

with historical_tab:
    st.header("Historical Terminal Operations")
    st.write(
        "This section summarises the historical event log supplied with the project. "
        "It does not represent live terminal conditions."
    )

    activity_frequency = load_csv("day3_activity_frequency.csv")
    duration_by_activity = load_csv("day3_duration_by_activity.csv")
    daily_activity = load_csv("day3_daily_activity_counts.csv")
    hourly_activity = load_csv("day3_hourly_activity_counts.csv")
    transitions = load_csv("day3_activity_transitions.csv")
    historical_cases = load_csv("day3_case_summary.csv")

    if activity_frequency is None:
        st.warning(
            "The file outputs/day3_activity_frequency.csv is missing or unreadable. "
            "Run the Day 3 analysis script to generate it."
        )
    else:
        st.subheader("Recorded Activity Frequency")
        st.dataframe(activity_frequency.head(30), use_container_width=True)

        text_columns = [
            column for column in activity_frequency.columns
            if activity_frequency[column].dtype == "object"
        ]
        numeric_columns = [
            column for column in activity_frequency.columns
            if pd.api.types.is_numeric_dtype(activity_frequency[column])
        ]

        if text_columns and numeric_columns:
            activity_column = text_columns[0]
            count_column = numeric_columns[0]
            chart_data = activity_frequency.nlargest(15, count_column)

            fig = px.bar(
                chart_data.sort_values(count_column),
                x=count_column,
                y=activity_column,
                orientation="h",
                title="Most Frequently Recorded Activities"
            )
            st.plotly_chart(fig, use_container_width=True)

    if duration_by_activity is not None:
        st.subheader("Recorded Activity Durations")
        st.dataframe(duration_by_activity.head(30), use_container_width=True)
    else:
        st.info(
            "Duration summary is unavailable. Check outputs/day3_duration_by_activity.csv."
        )

    if daily_activity is not None:
        st.subheader("Daily Historical Event Counts")
        st.dataframe(daily_activity.head(30), use_container_width=True)

        date_columns = [
            column for column in daily_activity.columns
            if "date" in column.lower() or "day" in column.lower()
        ]
        daily_numeric = [
            column for column in daily_activity.columns
            if pd.api.types.is_numeric_dtype(daily_activity[column])
        ]

        if date_columns and daily_numeric:
            fig = px.line(
                daily_activity,
                x=date_columns[0],
                y=daily_numeric[0],
                title="Historical Events Over Time"
            )
            st.plotly_chart(fig, use_container_width=True)

    if hourly_activity is not None:
        st.subheader("Historical Events by Hour")
        st.dataframe(hourly_activity.head(30), use_container_width=True)

        hour_columns = [
            column for column in hourly_activity.columns
            if "hour" in column.lower()
        ]
        hourly_numeric = [
            column for column in hourly_activity.columns
            if pd.api.types.is_numeric_dtype(hourly_activity[column])
        ]

        if hour_columns and hourly_numeric:
            fig = px.bar(
                hourly_activity,
                x=hour_columns[0],
                y=hourly_numeric[0],
                title="Recorded Events by Hour"
            )
            st.plotly_chart(fig, use_container_width=True)

    if transitions is not None:
        with st.expander("Recorded Activity Transitions"):
            st.dataframe(transitions.head(50), use_container_width=True)

    if historical_cases is not None:
        with st.expander("Historical Case Summary"):
            st.dataframe(historical_cases.head(50), use_container_width=True)


with simulation_tab:
    st.header("Evacuation Simulation")
    st.write(
        "Explore how an assumed arrival rate, truck fleet, disruption and recovery "
        "strategy affect a simplified hourly queue model."
    )

    scenarios = [
        {
            "name": "Baseline",
            "disruption": False,
            "extra_trucks": 0,
            "multiplier": 1.0
        },
        {
            "name": "Disruption Only",
            "disruption": True,
            "extra_trucks": 0,
            "multiplier": 1.0
        },
        {
            "name": "Extra Trucks",
            "disruption": True,
            "extra_trucks": extra_trucks,
            "multiplier": 1.0
        },
        {
            "name": "Faster Recovery",
            "disruption": True,
            "extra_trucks": 0,
            "multiplier": recovery_multiplier
        },
        {
            "name": "Combined Recovery",
            "disruption": True,
            "extra_trucks": extra_trucks,
            "multiplier": recovery_multiplier
        }
    ]

    hourly_results = []
    summary_results = []

    for scenario in scenarios:
        use_disruption = scenario["disruption"]

        hourly, summary = simulate_evacuation(
            scenario_name=scenario["name"],
            total_containers=int(total_containers),
            arrivals_per_hour=int(arrivals_per_hour),
            total_trucks=int(total_trucks),
            containers_per_truck_per_hour=int(service_rate),
            simulation_limit_hours=int(simulation_limit),
            disruption_start_hour=disruption_start if use_disruption else None,
            disruption_end_hour=disruption_end if use_disruption else None,
            disruption_availability=fleet_availability if use_disruption else 1.0,
            extra_trucks_start_hour=recovery_start if scenario["extra_trucks"] > 0 else None,
            extra_trucks_end_hour=recovery_end if scenario["extra_trucks"] > 0 else None,
            extra_trucks=int(scenario["extra_trucks"]),
            recovery_start_hour=recovery_start if scenario["multiplier"] > 1.0 else None,
            recovery_end_hour=recovery_end if scenario["multiplier"] > 1.0 else None,
            recovery_service_multiplier=float(scenario["multiplier"])
        )

        hourly_results.append(hourly)
        summary_results.append(summary)

    hourly_all = pd.concat(hourly_results, ignore_index=True)
    summary_all = pd.DataFrame(summary_results)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary_all.to_csv(
        OUTPUT_DIR / "day7_dashboard_strategy_comparison.csv",
        index=False
    )
    hourly_all.to_csv(
        OUTPUT_DIR / "day7_dashboard_hourly_results.csv",
        index=False
    )

    st.subheader("Scenario Overview")

    selected_scenario = st.selectbox(
        "Choose a scenario to inspect",
        summary_all["scenario"].tolist(),
        index=4
    )

    selected_summary = summary_all[
        summary_all["scenario"] == selected_scenario
    ].iloc[0]

    selected_hourly = hourly_all[
        hourly_all["scenario"] == selected_scenario
    ]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        show_metric(
            "Containers evacuated",
            f"{int(selected_summary['total_containers_evacuated']):,}"
        )

    with col2:
        show_metric(
            "Containers waiting",
            f"{int(selected_summary['containers_still_waiting']):,}"
        )

    with col3:
        completion = selected_summary["completion_hour"]
        show_metric(
            "Completion hour",
            "Not completed" if pd.isna(completion) else str(int(completion))
        )

    with col4:
        show_metric(
            "Queue-hours",
            f"{int(selected_summary['queue_hours']):,}"
        )

    queue_chart = px.line(
        selected_hourly,
        x="hour",
        y="queue_remaining",
        title=f"Queue Remaining — {selected_scenario}",
        markers=True
    )
    queue_chart.add_vline(
        x=disruption_start,
        line_dash="dash",
        annotation_text="Disruption starts"
    )
    queue_chart.add_vline(
        x=disruption_end,
        line_dash="dash",
        annotation_text="Disruption ends"
    )
    st.plotly_chart(queue_chart, use_container_width=True)

    evacuation_chart = px.line(
        selected_hourly,
        x="hour",
        y="cumulative_evacuated",
        title="Cumulative Containers Evacuated",
        markers=True
    )
    st.plotly_chart(evacuation_chart, use_container_width=True)

    utilisation_chart = px.line(
        selected_hourly,
        x="hour",
        y="resource_utilisation_percent",
        title="Hourly Resource Utilisation",
        markers=True
    )
    st.plotly_chart(utilisation_chart, use_container_width=True)

    st.subheader("Strategy Comparison")
    st.dataframe(summary_all, use_container_width=True)

    st.download_button(
        "Download Strategy Comparison CSV",
        data=summary_all.to_csv(index=False).encode("utf-8"),
        file_name="yardflow_strategy_comparison.csv",
        mime="text/csv"
    )

    st.download_button(
        "Download Hourly Simulation CSV",
        data=hourly_all.to_csv(index=False).encode("utf-8"),
        file_name="yardflow_hourly_simulation.csv",
        mime="text/csv"
    )

    st.caption(
        "This is a simplified hourly queue model, not a live digital twin of a physical terminal."
    )


with data_tab:
    st.header("Historical Data Quality")

    quality = load_csv("day3_data_quality.csv")
    if quality is not None:
        st.dataframe(quality, use_container_width=True)
    else:
        quality = load_csv("data_quality_summary.csv")
        if quality is not None:
            st.dataframe(quality, use_container_width=True)
        else:
            st.warning(
                "No data-quality summary was found. Check the Day 1 and Day 3 outputs."
            )

    profile_path = OUTPUT_DIR / "dataset_profile.txt"
    if profile_path.exists():
        with st.expander("Original Dataset Profile"):
            st.text(profile_path.read_text(encoding="utf-8", errors="replace"))

    st.markdown(
        """
        **Interpretation guidelines**

        - Historical records describe activities recorded in the supplied dataset.
        - Simulated truck capacity, arrivals, disruption availability and recovery multipliers are assumptions.
        - Event duration and case elapsed time must not automatically be described as official container dwell time.
        - Results depend on the chosen simulation inputs and model simplifications.
        """
    )