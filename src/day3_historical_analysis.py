
from pathlib import Path
import pandas as pd
import plotly.express as px

ROOT = Path(__file__).resolve().parent.parent
PROCESSED_FILE = ROOT / "data" / "processed" / "yardflow_cleaned_events.csv"
OUTPUT_DIR = ROOT / "outputs"
CHART_DIR = OUTPUT_DIR / "day3_charts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

if not PROCESSED_FILE.exists():
    raise FileNotFoundError(
        f"Processed dataset not found: {PROCESSED_FILE}\n"
        "Run src/day2_operational_analysis.py first."
    )

print("Loading processed historical events...")

columns = [
    "case_id",
    "activity",
    "Start Timestamp",
    "End Timestamp",
    "Role",
    "Duration Minutes",
]

df = pd.read_csv(
    PROCESSED_FILE,
    usecols=columns,
    parse_dates=["Start Timestamp", "End Timestamp"],
    low_memory=False,
)

df["Duration Minutes"] = pd.to_numeric(
    df["Duration Minutes"], errors="coerce"
)

df["activity"] = df["activity"].astype("string").str.strip()
df["case_id"] = df["case_id"].astype("string").str.strip()
df["Role"] = df["Role"].astype("string").str.strip()

valid_duration = df["Duration Minutes"].notna()
valid_duration &= df["Duration Minutes"] >= 0

df["Event Date"] = df["Start Timestamp"].dt.strftime("%Y-%m-%d")
df["Event Hour"] = df["Start Timestamp"].dt.hour

activity_frequency = (
    df.groupby("activity", dropna=False)
    .agg(
        event_count=("activity", "size"),
        unique_cases=("case_id", "nunique"),
    )
    .reset_index()
    .sort_values("event_count", ascending=False)
)

activity_frequency["event_percentage"] = (
    activity_frequency["event_count"] / len(df) * 100
).round(3)

activity_frequency.to_csv(
    OUTPUT_DIR / "day3_activity_frequency.csv", index=False
)

duration_df = df.loc[
    valid_duration & df["activity"].notna(),
    ["activity", "Duration Minutes"],
].copy()

duration_summary = (
    duration_df.groupby("activity")["Duration Minutes"]
    .agg(
        valid_duration_count="count",
        mean_minutes="mean",
        median_minutes="median",
        p90_minutes=lambda values: values.quantile(0.90),
        maximum_minutes="max",
    )
    .reset_index()
    .sort_values("median_minutes", ascending=False)
)

duration_summary.to_csv(
    OUTPUT_DIR / "day3_duration_by_activity.csv", index=False
)

daily_activity = (
    df.dropna(subset=["Event Date"])
    .groupby("Event Date")
    .agg(
        event_count=("activity", "size"),
        unique_cases=("case_id", "nunique"),
    )
    .reset_index()
    .sort_values("Event Date")
)

daily_activity.to_csv(
    OUTPUT_DIR / "day3_daily_activity_counts.csv", index=False
)

hourly_activity = (
    df.dropna(subset=["Event Hour"])
    .groupby("Event Hour")
    .agg(
        event_count=("activity", "size"),
        unique_cases=("case_id", "nunique"),
    )
    .reset_index()
    .sort_values("Event Hour")
)

hourly_activity.to_csv(
    OUTPUT_DIR / "day3_hourly_activity_counts.csv", index=False
)

case_summary = (
    df.groupby("case_id", dropna=False)
    .agg(
        event_count=("activity", "size"),
        unique_activities=("activity", "nunique"),
        first_start=("Start Timestamp", "min"),
        last_end=("End Timestamp", "max"),
    )
    .reset_index()
)

case_summary["elapsed_span_hours"] = (
    case_summary["last_end"] - case_summary["first_start"]
).dt.total_seconds() / 3600

case_summary.to_csv(
    OUTPUT_DIR / "day3_case_summary.csv", index=False
)

ordered = df.sort_values(
    ["case_id", "Start Timestamp", "End Timestamp"],
    na_position="last",
).copy()

ordered["next_activity"] = ordered.groupby("case_id")["activity"].shift(-1)

transitions = ordered.dropna(
    subset=["activity", "next_activity"]
).copy()

transition_summary = (
    transitions.groupby(["activity", "next_activity"])
    .size()
    .reset_index(name="transition_count")
    .sort_values("transition_count", ascending=False)
)

transition_summary.to_csv(
    OUTPUT_DIR / "day3_activity_transitions.csv", index=False
)

quality_summary = pd.DataFrame({
    "metric": [
        "total_event_rows",
        "unique_cases",
        "unique_activities",
        "missing_case_id",
        "missing_activity",
        "missing_start_timestamp",
        "missing_end_timestamp",
        "missing_duration",
        "negative_duration_rows",
        "duration_rows_over_24_hours",
        "events_without_start_date",
        "exact_duplicate_rows",
    ],
    "value": [
        len(df),
        df["case_id"].nunique(),
        df["activity"].nunique(),
        int(df["case_id"].isna().sum()),
        int(df["activity"].isna().sum()),
        int(df["Start Timestamp"].isna().sum()),
        int(df["End Timestamp"].isna().sum()),
        int(df["Duration Minutes"].isna().sum()),
        int((df["Duration Minutes"] < 0).sum()),
        int((df["Duration Minutes"] > 1440).sum()),
        int(df["Event Date"].isna().sum()),
        int(df.duplicated().sum()),
    ],
})

quality_summary.to_csv(
    OUTPUT_DIR / "day3_data_quality.csv", index=False
)

top_activities = activity_frequency.head(15)

activity_chart = px.bar(
    top_activities.sort_values("event_count"),
    x="event_count",
    y="activity",
    orientation="h",
    title="Most Frequently Recorded Terminal Activities",
    labels={
        "event_count": "Recorded event count",
        "activity": "Activity",
    },
)

activity_chart.write_html(
    str(CHART_DIR / "activity_frequency.html")
)

duration_chart_data = duration_summary.dropna(
    subset=["median_minutes"]
).sort_values("median_minutes", ascending=True).tail(15)

duration_chart = px.bar(
    duration_chart_data,
    x="median_minutes",
    y="activity",
    orientation="h",
    title="Median Recorded Event Duration by Activity",
    labels={
        "median_minutes": "Median duration (minutes)",
        "activity": "Activity",
    },
)

duration_chart.write_html(
    str(CHART_DIR / "activity_duration.html")
)

daily_chart = px.line(
    daily_activity,
    x="Event Date",
    y="event_count",
    title="Recorded Events Over Time",
    labels={
        "Event Date": "Date",
        "event_count": "Recorded event count",
    },
)

daily_chart.write_html(
    str(CHART_DIR / "daily_event_trend.html")
)

hourly_chart = px.bar(
    hourly_activity,
    x="Event Hour",
    y="event_count",
    title="Recorded Events by Start Hour",
    labels={
        "Event Hour": "Hour of day",
        "event_count": "Recorded event count",
    },
)

hourly_chart.update_xaxes(dtick=1)

hourly_chart.write_html(
    str(CHART_DIR / "hourly_event_pattern.html")
)

findings = []

findings.append("YARDFLOW DAY 3 — HISTORICAL DATA ANALYSIS")
findings.append("")
findings.append("DATASET OVERVIEW")
findings.append(f"Event rows analysed: {len(df):,}")
findings.append(f"Unique cases: {df['case_id'].nunique():,}")
findings.append(f"Unique activities: {df['activity'].nunique():,}")
findings.append(
    f"Earliest recorded start: {df['Start Timestamp'].min()}"
)
findings.append(
    f"Latest recorded end: {df['End Timestamp'].max()}"
)
findings.append("")
findings.append("TOP 10 ACTIVITIES BY EVENT COUNT")

for _, row in activity_frequency.head(10).iterrows():
    findings.append(
        f"{row['activity']}: {int(row['event_count']):,} events "
        f"({row['event_percentage']:.2f}%)"
    )

findings.append("")
findings.append("TOP 10 MOST FREQUENT ACTIVITY TRANSITIONS")

for _, row in transition_summary.head(10).iterrows():
    findings.append(
        f"{row['activity']} -> {row['next_activity']}: "
        f"{int(row['transition_count']):,} occurrences"
    )

findings.append("")
findings.append("DURATION INTERPRETATION")
findings.append(
    "Duration is calculated from each event's start and end timestamps."
)
findings.append(
    "A case's elapsed span is the time between its first recorded start "
    "and last recorded end; it is not necessarily continuous processing "
    "or official container dwell time."
)
findings.append(
    "Long durations require investigation and have not been automatically removed."
)
findings.append("")
findings.append("DATA QUALITY")
findings.append(quality_summary.to_string(index=False))
findings.append("")
findings.append("LIMITATIONS")
findings.append(
    "These are historical records, not a live terminal feed. "
    "Event frequency does not directly measure congestion, available "
    "transport capacity, or operational efficiency."
)

(OUTPUT_DIR / "day3_findings.txt").write_text(
    "\n".join(findings),
    encoding="utf-8",
)

print("\nDay 3 analysis completed.")
print(f"Events analysed: {len(df):,}")
print(f"Unique cases: {df['case_id'].nunique():,}")
print(f"Unique activities: {df['activity'].nunique():,}")

print("\nTop 10 activities:")
print(activity_frequency.head(10).to_string(index=False))

print("\nTop 10 activity transitions:")
print(transition_summary.head(10).to_string(index=False))

print("\nData quality:")
print(quality_summary.to_string(index=False))

print(f"\nReports saved in: {OUTPUT_DIR}")
print(f"Interactive charts saved in: {CHART_DIR}")
