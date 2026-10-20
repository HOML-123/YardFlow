
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = ROOT / "data" / "raw" / "Dataset of Dwelling Time Process Fix.xlsx"
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "outputs"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not RAW_FILE.exists():
    raise FileNotFoundError(
        f"Dataset not found: {RAW_FILE}\n"
        "Check that the Excel file is inside data/raw and that its filename matches exactly."
    )

print("Loading the historical terminal event dataset...")
df = pd.read_excel(RAW_FILE, sheet_name="Sheet1", engine="openpyxl")

required_columns = [
    "case_id",
    "activity",
    "Start Timestamp",
    "End Timestamp",
    "Role",
]

missing_columns = [column for column in required_columns if column not in df.columns]

if missing_columns:
    raise ValueError(f"Required columns are missing: {missing_columns}")

df["Start Timestamp"] = pd.to_datetime(
    df["Start Timestamp"], errors="coerce"
)
df["End Timestamp"] = pd.to_datetime(
    df["End Timestamp"], errors="coerce"
)

df["activity"] = df["activity"].astype("string").str.strip()
df["case_id"] = df["case_id"].astype("string").str.strip()
df["Role"] = df["Role"].astype("string").str.strip()

df["Duration Minutes"] = (
    df["End Timestamp"] - df["Start Timestamp"]
).dt.total_seconds() / 60

df["Duration Validity"] = "valid"
df.loc[df["Start Timestamp"].isna(), "Duration Validity"] = "missing_start"
df.loc[df["End Timestamp"].isna(), "Duration Validity"] = "missing_end"
df.loc[
    df["Start Timestamp"].isna() | df["End Timestamp"].isna(),
    "Duration Minutes"
] = pd.NA
df.loc[
    df["Duration Minutes"] < 0, "Duration Validity"
] = "negative_duration"
df.loc[
    df["Duration Minutes"] < 0, "Duration Minutes"
] = pd.NA

df["Event Date"] = df["Start Timestamp"].dt.date

cleaned_file = PROCESSED_DIR / "yardflow_cleaned_events.csv"
df.to_csv(cleaned_file, index=False)

activity_summary = (
    df.groupby("activity", dropna=False)
    .agg(
        event_count=("activity", "size"),
        unique_cases=("case_id", "nunique"),
        valid_duration_count=("Duration Minutes", "count"),
        average_duration_minutes=("Duration Minutes", "mean"),
        median_duration_minutes=("Duration Minutes", "median"),
        maximum_duration_minutes=("Duration Minutes", "max"),
    )
    .reset_index()
    .sort_values("event_count", ascending=False)
)

activity_summary.to_csv(
    OUTPUT_DIR / "activity_summary.csv", index=False
)

role_summary = (
    df.groupby("Role", dropna=False)
    .agg(
        event_count=("Role", "size"),
        unique_cases=("case_id", "nunique"),
    )
    .reset_index()
    .sort_values("event_count", ascending=False)
)

role_summary.to_csv(
    OUTPUT_DIR / "role_summary.csv", index=False
)

case_summary = (
    df.groupby("case_id", dropna=False)
    .agg(
        event_count=("activity", "size"),
        first_event=("Start Timestamp", "min"),
        last_event=("End Timestamp", "max"),
        unique_activities=("activity", "nunique"),
        total_valid_event_minutes=("Duration Minutes", "sum"),
    )
    .reset_index()
)

case_summary["Elapsed Span Hours"] = (
    case_summary["last_event"] - case_summary["first_event"]
).dt.total_seconds() / 3600

case_summary.to_csv(
    OUTPUT_DIR / "case_summary.csv", index=False
)

sequence_df = df.sort_values(
    ["case_id", "Start Timestamp", "End Timestamp"],
    na_position="last"
).copy()

sequence_summary = (
    sequence_df.groupby("case_id", dropna=False)["activity"]
    .agg(lambda values: " -> ".join(values.dropna().astype(str)))
    .reset_index(name="activity_sequence")
)

sequence_summary.to_csv(
    OUTPUT_DIR / "case_activity_sequences.csv", index=False
)

quality_summary = pd.DataFrame({
    "metric": [
        "total_rows",
        "total_columns",
        "exact_duplicate_rows",
        "missing_case_id",
        "missing_activity",
        "missing_start_timestamp",
        "missing_end_timestamp",
        "missing_role",
        "valid_duration_rows",
        "missing_or_invalid_duration_rows",
        "negative_duration_rows",
        "unique_cases",
        "unique_activities",
        "earliest_start_timestamp",
        "latest_end_timestamp",
    ],
    "value": [
        len(df),
        len(df.columns),
        int(df.duplicated().sum()),
        int(df["case_id"].isna().sum()),
        int(df["activity"].isna().sum()),
        int(df["Start Timestamp"].isna().sum()),
        int(df["End Timestamp"].isna().sum()),
        int(df["Role"].isna().sum()),
        int(df["Duration Minutes"].notna().sum()),
        int(df["Duration Minutes"].isna().sum()),
        int((df["Duration Validity"] == "negative_duration").sum()),
        int(df["case_id"].nunique()),
        int(df["activity"].nunique()),
        str(df["Start Timestamp"].min()),
        str(df["End Timestamp"].max()),],})
quality_summary.to_csv(
    OUTPUT_DIR / "data_quality_summary.csv", index=False)
print("\nDay 2 analysis completed.")
print(f"Rows analysed: {len(df):,}")
print(f"Unique cases: {df['case_id'].nunique():,}")
print(f"Unique activities: {df['activity'].nunique():,}")
print(f"Cleaned dataset: {cleaned_file}")
print(f"Reports saved in: {OUTPUT_DIR}")
print("\nMost frequent activities:")
print(activity_summary.head(10).to_string(index=False))
print("\nData quality overview:")
print(quality_summary.to_string(index=False))
