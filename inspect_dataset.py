from pathlib import Path
import pandas as pd
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
supported_extensions = {".xlsx", ".xls", ".csv"}
files = sorted(
    file for file in RAW_DIR.iterdir()
    if file.is_file() and file.suffix.lower() in supported_extensions)
if not files:
    raise FileNotFoundError(
        "No Excel or CSV dataset found in data/raw. "
        "Download the dataset and place it there")
dataset_file = next(
    (file for file in files if file.suffix.lower() == ".xlsx"),
    files[0])
if dataset_file.suffix.lower() == ".csv":
    df = pd.read_csv(dataset_file)
else:
    excel_file = pd.ExcelFile(dataset_file)
    print("Available sheets:", excel_file.sheet_names)
    df = pd.read_excel(dataset_file, sheet_name=excel_file.sheet_names[0])
print("\nDataset file:", dataset_file.name)
print("Number of rows:", df.shape[0])
print("Number of columns:", df.shape[1])
print("\nColumn names:")
for column in df.columns:
    print("-", column)
print("\nColumn data types:")
print(df.dtypes.to_string())
print("\nFirst five rows:")
print(df.head().to_string(index=False))
print("\nMissing values per column:")
print(df.isna().sum().to_string())
print("\nDuplicate rows:", df.duplicated().sum())
report = [
    f"Dataset file: {dataset_file.name}",
    f"Rows: {df.shape[0]}",
    f"Columns: {df.shape[1]}",
    "",
    "Column names:",
    *[str(column) for column in df.columns],
    "",
    "Column data types:",
    df.dtypes.to_string(),
    "",
    "Missing values per column:",
    df.isna().sum().to_string(),
    "",
    f"Duplicate rows: {df.duplicated().sum()}",
    "",
    "First five rows:",
    df.head().to_string(index=False)]
report_path = OUTPUT_DIR / "dataset_profile.txt"
report_path.write_text("\n".join(report), encoding="utf-8")
print("\nDataset inspection completed.")
print("Report saved to:", report_path)