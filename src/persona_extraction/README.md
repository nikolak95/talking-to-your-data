# LifeSnaps Persona Extraction Pipeline

A modular Python pipeline for extracting representative health personas from the LifeSnaps dataset. This tool identifies 14-day time windows that best match predefined persona profiles and randomly selects viable candidates for study purposes.

## Overview

The pipeline extracts two distinct health personas from wearable health tracking data:

- **Persona A**: Sleep-deprived individual with weekend recovery pattern
  - Low-to-moderate activity (~5000 steps/day)
  - Short sleep duration (~5.75 hours/night)
  - Weekend sleep rebound
  - Moderate activity variability

- **Persona B**: Active lifestyle with irregular stress-causing routine
  - Moderately active (~11000 steps/day)
  - Irregular step patterns (CV ~0.45)
  - Irregular sleep patterns (CV ~0.35)
  - Moderate resting heart rate (~72 bpm)

## Installation

### Requirements

- Python 3.8+
- pandas
- numpy
- matplotlib

### Setup

```bash
# Using pip directly
pip install pandas numpy matplotlib
```

## Usage

### Basic Usage

```bash
python extract_personas.py daily.csv
```

This will:
1. Extract all viable 14-day windows from the dataset
2. Score each window against persona profiles
3. Select the best candidate for each persona (top-k=1, default)
4. Generate `persona_a.json` and `persona_b.json`

Note: the file `daily.csv` must previously be downloaded from the [LifeSnaps repository](https://zenodo.org/records/7229547).

### Advanced Options

```bash
python extract_personas.py daily.csv --top-k 5 --seed 42 --plot
```

#### Command-line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `csv_path` | Path to daily.csv file | Required |
| `--top-k N` | Selection pool size: 1=best, >1=random from top k | 1 |
| `--seed S` | Random seed for reproducibility (when top-k > 1) | None |
| `--window-days N` | Window size in days | 14 |
| `--min-days N` | Minimum days with valid data | 12 |
| `--output-dir DIR` | Output directory | Current directory |
| `--plot` | Generate comparison visualization | False |


## Input Data Format

The input CSV file (`daily.csv`) from LifeSnaps contains the following columns:

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Participant identifier |
| `date` | date | Date (YYYY-MM-DD) |
| `steps` | int | Daily step count |
| `minutesAsleep` | int | Sleep duration in minutes |
| `resting_hr` | float | Resting heart rate (bpm) |

Example:
```csv
id,date,steps,minutesAsleep,resting_hr
621e2f9167b776a240011ccb,2022-01-07,4823,342,68
621e2f9167b776a240011ccb,2022-01-08,5234,356,70
...
```

## Output Files

### persona_a.json / persona_b.json

JSON files containing the selected 14-day window:

```json
{
  "persona": "A",
  "id": "621e2f9167b776a240011ccb",
  "start_date": "2022-01-07",
  "days": [
    {
      "date": "Friday, 2022-01-07",
      "steps": 4823,
      "sleep_hours": 5.7
    },
    ...
  ]
}
```

### Key Components

#### 1. Persona Scoring (`persona_scoring.py`)

Defines fitness functions that score how well a time window matches each persona profile:

- `score_persona_a()`: Scores based on low activity, short sleep, weekend rebound
- `score_persona_b()`: Scores based on high activity, routine irregularity, heart rate

Scores range from 0 (poor match) to 1 (excellent match).

#### 2. Data Validation (`data_validation.py`)

Ensures data quality through:

- **Contiguity checking**: Validates 14 consecutive days with no gaps
- **Coverage validation**: Requires ≥12 days with valid step and sleep data
- **Data cleaning**: Handles missing values and invalid entries
- **Feature engineering**: Adds derived features (day of week, weekend indicator)

#### 3. Window Extraction (`window_extraction.py`)

Handles sliding window extraction:

- `extract_candidates()`: Slides 14-day window across all participants
- `select_top_candidates()`: Ranks candidates by fit score
- `select_random_from_viable()`: Randomly selects from viable candidates (score ≥ threshold)
- `extract_window_data()`: Extracts specific window for final output

#### 4. Visualization (`visualization.py`)

Provides output formatting:

- `plot_comparison()`: Creates side-by-side comparison plots
- `window_to_json()`: Converts DataFrames to JSON format
- `print_candidate_summary()`: Formats candidate tables for stdout

## Methodology

### Sliding Window Approach

For each participant:
1. Extract all possible 14-day contiguous windows
2. Validate data quality (contiguity, coverage)
3. Score window against both persona profiles
4. Collect viable candidates (score ≥ threshold)

### Random Selection

From the viable candidates (those meeting the threshold):
1. Sort by fit score
2. Display top K candidates
3. **Randomly select one** from viable candidates using Python's NumPy random generator
4. Optional seed parameter ensures reproducibility

This approach ensures:
- Selected personas are **representative** (meet quality threshold)
- Selection is **unbiased** (random among viable candidates)
- Process is **reproducible** (when using --seed)

## Scoring Details

### Persona A Scoring Components

| Component | Weight | Target |
|-----------|--------|--------|
| Activity level | 35% | ~5000 steps |
| Sleep duration | 35% | ~5.75 hours |
| Weekend rebound | 20% | +2 hours on weekends |
| Activity variability | 10% | Moderate CV |

### Persona B Scoring Components

| Component | Weight | Target |
|-----------|--------|--------|
| Activity level | 40% | ~11000 steps |
| Step irregularity | 25% | CV ~0.45 |
| Sleep irregularity | 20% | CV ~0.35 |
| Resting heart rate | 15% | ~72 bpm |

## Validation Criteria

### Window Requirements

- **Length**: Exactly 14 consecutive days
- **Contiguity**: No gaps in date sequence
- **Step coverage**: ≥12 days with valid step data
- **Sleep coverage**: ≥12 days with valid sleep data

### Data Quality

- Negative values are treated as missing
- At least 12 out of 14 days must have valid data for both metrics
- Windows with insufficient data are automatically excluded

## Limitations

- Requires at least 14 consecutive days of data per participant
- Personas are predefined (not learned from data)
- Focuses on step count and sleep duration only, though other attributes are available
