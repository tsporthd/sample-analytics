# sample-analytics

Infrastructure risk analysis tool that processes application infrastructure data, calculates composite risk scores, and produces ranked risk reports.

## What It Does

This tool reads raw infrastructure records from a CSV file, filters them against a list of in-scope applications, and computes risk metrics for each application:

1. **Filters** records to only applications defined in `Apps.csv`
2. **Counts** total infrastructure items per application (AppCode)
3. **Maps** composite scores to numeric values (High=3.0, Moderate High=2.5, Moderate=2.0, Low=1.0)
4. **Calculates** a composite risk score: `CompositeScoreNumber x TotalInfrastructure`
5. **Calculates** risk score percentages relative to the total across all applications
6. **Associates** each application with its responsible executive from `Apps.csv`

### Outputs

- `analyzed_data.csv` — Enhanced data with all calculated fields and executive assignments
- `risk_chart.csv` — Ranked risk chart sorted by composite score (high to low), then by risk percentage
- Console summary report with AppCode counts, score distribution, and a formatted risk chart

## Input Files

### `sampleData.csv`

Raw infrastructure data with columns:

| Column | Description |
|---|---|
| ApplicationService | Application name |
| AppCode | Short application identifier |
| CompositeScore | Risk level (High, Moderate High, Moderate, Low) |
| Class | Infrastructure type (e.g., Windows Server, Kubernetes Node) |

Each row represents one infrastructure item. Multiple rows per AppCode are expected.

### `Apps.csv`

Defines which applications are in scope and their responsible executives:

| Column | Description |
|---|---|
| AppCode | Application identifier (must match values in sampleData.csv) |
| Executive | Responsible executive name |

Only AppCodes listed in this file will be included in the analysis.

## Usage

```bash
python3 analyze_data_solid.py
```

No arguments required. The script reads `sampleData.csv` and `Apps.csv` from the current directory and writes output files to the same directory.

## Project Structure

| File | Purpose |
|---|---|
| `analyze_data_solid.py` | Entry point — wires up dependencies and runs the pipeline |
| `data_models.py` | Data classes, risk calculators, score mappers, and abstract interfaces |
| `data_processors.py` | CSV reader/writer, chart generator, report generator, and the main analysis service |
| `app_filter.py` | AppCode filtering and executive lookup from Apps.csv |
| `test_solid_implementation.py` | Tests for the SOLID implementation |
| `test_app_filter.py` | Tests for the AppCode filter |

## Requirements

- Python 3.10+ (uses `tuple[]` type hint syntax)
- No external dependencies — uses only the Python standard library
