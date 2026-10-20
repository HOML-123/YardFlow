
from pathlib import Path
import pandas as pd
import plotly.express as px

from evacuation_simulator import simulate_evacuation

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "outputs"
CHART_DIR = OUTPUT_DIR / "day4_charts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

scenarios = [
    {
        "scenario_name": "Baseline",
        "total_containers": 500,
        "arrivals_per_hour": 30,
        "total_trucks": 8,
        "containers_per_truck_per_hour": 4,
        "simulation_limit_hours": 48,
    },
    {
        "scenario_name": "Reduced Capacity",
        "total_containers": 500,
        "arrivals_per_hour": 30,
        "total_trucks": 8,
        "containers_per_truck_per_hour": 4,
        "simulation_limit_hours": 48,
        "disruption_start_hour": 8,
        "disruption_end_hour": 13,
        "disruption_availability": 0.5,
    },
]

all_hourly_results = []
all_summaries = []

for scenario in scenarios:
    hourly_results, summary = simulate_evacuation(**scenario)
    all_hourly_results.append(hourly_results)
    all_summaries.append(summary)

hourly_data = pd.concat(all_hourly_results, ignore_index=True)
summary_data = pd.DataFrame(all_summaries)

hourly_data.to_csv(
    OUTPUT_DIR / "day4_hourly_simulation.csv",
    index=False,
)

summary_data.to_csv(
    OUTPUT_DIR / "day4_simulation_summary.csv",
    index=False,
)

queue_chart = px.line(
    hourly_data,
    x="hour",
    y="queue_remaining",
    color="scenario",
    markers=True,
    title="Simulated Container Queue by Hour",
    labels={
        "hour": "Simulation hour",
        "queue_remaining": "Containers waiting",
        "scenario": "Scenario",
    },
)

queue_chart.write_html(
    str(CHART_DIR / "queue_comparison.html")
)

evacuation_chart = px.line(
    hourly_data,
    x="hour",
    y="cumulative_evacuated",
    color="scenario",
    markers=True,
    title="Cumulative Simulated Container Evacuation",
    labels={
        "hour": "Simulation hour",
        "cumulative_evacuated": "Containers evacuated",
        "scenario": "Scenario",
    },
)

evacuation_chart.write_html(
    str(CHART_DIR / "evacuation_comparison.html")
)

utilisation_chart = px.line(
    hourly_data,
    x="hour",
    y="resource_utilisation_percent",
    color="scenario",
    markers=True,
    title="Simulated Transport Resource Utilisation",
    labels={
        "hour": "Simulation hour",
        "resource_utilisation_percent": "Capacity utilisation (%)",
        "scenario": "Scenario",
    },
)

utilisation_chart.write_html(
    str(CHART_DIR / "resource_utilisation.html")
)

findings = [
    "YARDFLOW DAY 4 — SIMULATION RESULTS",
    "",
    "All results below are simulated, not observed terminal performance.",
    "",
    summary_data.to_string(index=False),
    "",
    "MODEL ASSUMPTIONS",
    "Total demand: 500 containers per scenario.",
    "Container arrivals: up to 30 containers per hour.",
    "Baseline resources: 8 trucks.",
    "Assumed service rate: 4 containers per truck per hour.",
    "Reduced-capacity scenario: 50% resource availability during hours 8–12.",
    "Simulation limit: 48 hours.",
    "",
    "LIMITATIONS",
    "The model uses a simplified hourly queue and constant service rates.",
    "It does not represent the full physical layout of a real terminal.",
    "The simulation inputs must not be described as historical measurements.",
]

(OUTPUT_DIR / "day4_simulation_findings.txt").write_text(
    "\n".join(findings),
    encoding="utf-8",
)

print("\nDay 4 simulation completed.")
print("\nScenario summary:")
print(summary_data.to_string(index=False))
print(f"\nHourly results: {OUTPUT_DIR / 'day4_hourly_simulation.csv'}")
print(f"Summary report: {OUTPUT_DIR / 'day4_simulation_summary.csv'}")
print(f"Charts: {CHART_DIR}")
