
from pathlib import Path
import pandas as pd
import plotly.express as px

from evacuation_simulator import simulate_evacuation

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "outputs"
CHART_DIR = OUTPUT_DIR / "day5_charts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

common_settings = {
    "total_containers": 900,
    "arrivals_per_hour": 30,
    "total_trucks": 8,
    "containers_per_truck_per_hour": 4,
    "simulation_limit_hours": 48,
}

scenarios = [
    {
        "scenario_name": "Baseline",
    },
    {
        "scenario_name": "Disruption Only",
        "disruption_start_hour": 8,
        "disruption_end_hour": 16,
        "disruption_availability": 0.5,
    },
    {
        "scenario_name": "Extra Trucks During Recovery",
        "disruption_start_hour": 8,
        "disruption_end_hour": 16,
        "disruption_availability": 0.5,
        "extra_trucks_start_hour": 16,
        "extra_trucks_end_hour": 24,
        "extra_trucks": 4,
    },
    {
        "scenario_name": "Faster Service During Recovery",
        "disruption_start_hour": 8,
        "disruption_end_hour": 16,
        "disruption_availability": 0.5,
        "recovery_start_hour": 16,
        "recovery_end_hour": 24,
        "recovery_service_multiplier": 1.5,
    },
    {
        "scenario_name": "Combined Recovery",
        "disruption_start_hour": 8,
        "disruption_end_hour": 16,
        "disruption_availability": 0.5,
        "extra_trucks_start_hour": 16,
        "extra_trucks_end_hour": 24,
        "extra_trucks": 4,
        "recovery_start_hour": 16,
        "recovery_end_hour": 24,
        "recovery_service_multiplier": 1.5,
    },
]

hourly_results_list = []
summary_list = []

for scenario in scenarios:
    settings = common_settings | scenario

    hourly_results, summary = simulate_evacuation(**settings)

    hourly_results_list.append(hourly_results)
    summary_list.append(summary)

hourly_data = pd.concat(
    hourly_results_list,
    ignore_index=True,
)

summary_data = pd.DataFrame(summary_list)

summary_data.to_csv(
    OUTPUT_DIR / "day5_strategy_comparison.csv",
    index=False,
)

hourly_data.to_csv(
    OUTPUT_DIR / "day5_hourly_results.csv",
    index=False,
)

queue_chart = px.line(
    hourly_data,
    x="hour",
    y="queue_remaining",
    color="scenario",
    title="Container Queue Under Different Recovery Strategies",
    labels={
        "hour": "Simulation hour",
        "queue_remaining": "Containers waiting",
        "scenario": "Scenario",
    },
)

queue_chart.write_html(
    str(CHART_DIR / "strategy_queue_comparison.html")
)

evacuation_chart = px.line(
    hourly_data,
    x="hour",
    y="cumulative_evacuated",
    color="scenario",
    title="Cumulative Evacuation by Recovery Strategy",
    labels={
        "hour": "Simulation hour",
        "cumulative_evacuated": "Containers evacuated",
        "scenario": "Scenario",
    },
)

evacuation_chart.write_html(
    str(CHART_DIR / "strategy_evacuation_comparison.html")
)

summary_chart = px.bar(
    summary_data,
    x="scenario",
    y="queue_hours",
    title="Total Queue Exposure by Strategy",
    labels={
        "scenario": "Scenario",
        "queue_hours": "Queue-hours",
    },
)

summary_chart.update_layout(
    xaxis_tickangle=-25,
)

summary_chart.write_html(
    str(CHART_DIR / "strategy_queue_hours.html")
)

findings = [
    "YARDFLOW DAY 5 — DISRUPTION AND RECOVERY COMPARISON",
    "",
    "All scenario inputs and outcomes are simulated.",
    "",
    "COMMON ASSUMPTIONS",
    "Total demand: 900 containers.",
    "Arrivals: up to 30 containers per hour.",
    "Baseline fleet: 8 trucks.",
    "Baseline service rate: 4 containers per truck per hour.",
    "Simulation limit: 48 hours.",
    "",
    "DISRUPTION ASSUMPTION",
    "50% of the baseline truck fleet is available during hours 8–15.",
    "",
    "RECOVERY ASSUMPTIONS",
    "Extra-resource strategy: 4 additional trucks during hours 16–23.",
    "Faster-service strategy: 1.5 times the baseline service rate during hours 16–23.",
    "Combined strategy applies both recovery measures.",
    "",
    "SCENARIO RESULTS",
    summary_data.to_string(index=False),
    "",
    "INTERPRETATION",
    "Lower queue-hours indicates less accumulated waiting in the simulated queue.",
    "Earlier completion indicates faster clearance of all demand.",
    "A strategy is not necessarily better on every measure.",
    "",
    "LIMITATIONS",
    "Service rates and disruption settings are assumptions, not measured terminal data.",
    "The model uses a simplified hourly queue and does not model individual truck routes.",
]

(OUTPUT_DIR / "day5_strategy_findings.txt").write_text(
    "\n".join(findings),
    encoding="utf-8",
)

print("\nDay 5 analysis completed.")

print("\nStrategy comparison:")
print(
    summary_data[
        [
            "scenario",
            "total_containers_evacuated",
            "containers_still_waiting",
            "maximum_queue",
            "queue_hours",
            "completion_hour",
            "completed_within_limit",
        ]
    ].to_string(index=False)
)

print(f"\nSummary: {OUTPUT_DIR / 'day5_strategy_comparison.csv'}")
print(f"Hourly results: {OUTPUT_DIR / 'day5_hourly_results.csv'}")
print(f"Findings: {OUTPUT_DIR / 'day5_strategy_findings.txt'}")
print(f"Charts: {CHART_DIR}")
