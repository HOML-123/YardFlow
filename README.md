# YardFlow 🚢

YardFlow is a container-terminal operations project built to explore how operational delays, transport-capacity constraints, and disruptions affect container evacuation. It combines historical event-log analysis with simulation-based experiments to compare possible recovery strategies.

## Project Objectives

- Analyse container-terminal event data to understand operational activity and delays.
- Identify activity patterns, bottlenecks, and changes in operations over time.
- Simulate container evacuation under different transport-capacity constraints.
- Model operational disruptions and compare recovery strategies.
- Present historical findings and simulation results through an interactive dashboard.

## Key Features

- **Historical Operations Analysis:** Summarises activity patterns, hourly and daily trends, and case-level event sequences.
- **Evacuation Simulation:** Models container evacuation under configurable arrival rates, transport capacity, and service rates.
- **Disruption Analysis:** Examines the effects of reduced transport availability on evacuation performance.
- **Recovery Strategy Comparison:** Compares baseline operations, disruption-only scenarios, and recovery strategies involving additional transport capacity or faster service.
- **Interactive Dashboard:** Uses Streamlit and Plotly to present operational summaries, charts, and simulation results.
- **Data Quality:** Provides dataset profiles and data-quality summaries to support analysis.

## Data Source

**Dataset of Dwelling Time Process Fix — Version 2**

Source: https://data.mendeley.com/datasets/yvp2b4rtp3/2

The project uses container-terminal event-log data for historical analysis. Credit belongs to the dataset's original contributors. Refer to the dataset's licence and attribution requirements when using or redistributing the data.

## Data Integrity and Limitations

YardFlow separates analysis of historical event records from simulated operational scenarios. Transport capacities, disruption settings, and recovery strategies are configurable simulation assumptions, not verified observations of actual terminal operations.

Simulation results are intended for educational and decision-support experimentation. They should not be interpreted as validated forecasts or recommendations for a real container terminal.

## Technology Stack

- Python
- Pandas
- Streamlit
- Plotly
- Excel and CSV datasets and reports

## Run Locally

### 1. Clone or download the repository

Open Command Prompt in the folder where you want to store the project.

If you are cloning the repository, run:

```bash
git clone YOUR_YARDFLOW_REPOSITORY_URL
cd YardFlow
```

Replace `YOUR_YARDFLOW_REPOSITORY_URL` with your actual GitHub repository URL.

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install the required packages

```bash
python -m pip install --upgrade pip
python -m pip install streamlit pandas plotly openpyxl
```

### 4. Launch the dashboard

```bash
python -m streamlit run app.py
```

The dashboard should open in your default browser.

**Note:** The project also requires its expected dataset and generated report files. Raw data and generated outputs may not be included in the repository, depending on the project's `.gitignore` settings.

## Project Status

YardFlow is a student project focused on historical operations analysis and simulation-based comparison of container-terminal disruption and recovery scenarios.