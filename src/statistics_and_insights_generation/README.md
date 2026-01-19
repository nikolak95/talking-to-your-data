# Persona Statistics & Insights Pipeline

A modular Python pipeline for computing statistics and generating insights from extracted persona data. This tool calculates correlations, trends, and weekday patterns, with optional LLM-based insight generation.

## Overview

The pipeline processes persona JSON files (output from the extraction pipeline) and computes:

- **Base Statistics**: Averages, variance, standard deviation, min/max for steps and sleep
- **Correlations**: Pearson correlation between steps and sleep duration
- **Trends**: Weighted linear regression to detect increasing/decreasing/stable patterns
- **Weekday Patterns**: Weekday vs weekend differences for both metrics

Optionally, LLM-based insights can be generated using any provider (OpenAI, Anthropic, local models, etc.).

## Installation

### Requirements

- Python 3.8+
- pandas
- numpy

### Setup

```bash
# Using pip directly
pip install pandas numpy
```

## Usage

### Generate Statistics and LLM Prompt (Recommended)

The `generate_prompt.py` script computes statistics and generates a filled observer prompt ready for any LLM:

```bash
python generate_prompt.py persona_a.json --age 28 --gender male
```

This will:
1. Load the persona JSON file
2. Compute all statistics (correlations, trends, patterns)
3. Display a formatted summary to console
4. Generate two output files:
   - `precomputed_a.json` - Computed statistics
   - `prompt_a.txt` - Filled observer prompt ready for LLM

#### Command-line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `input_files` | Input persona JSON file(s) | Required |
| `--age` | User's age (e.g., "28" or "late 20s") | Required |
| `--gender` | User's gender (e.g., "male", "female") | Required |
| `--output-dir` | Output directory | Current directory |
| `--quiet, -q` | Suppress console output | False |

#### Example Workflow

```bash
# Generate statistics and prompt
python generate_prompt.py persona_a.json --age 28 --gender male --output-dir ./output

# The generated prompt_a.txt can now be used with any LLM
# The LLM should return a JSON array of 5 insights
```

### Statistics Only

If you only need statistics without the observer prompt:

```bash
python compute_statistics.py persona_a.json
```

### Processing Multiple Files

```bash
python generate_prompt.py persona_a.json persona_b.json --age 25 --gender female
```

## Input Data Format

The input JSON files (`persona_a.json`, `persona_b.json`) are output from the extraction pipeline:

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

## Output Files

### precomputed_a.json / precomputed_b.json

JSON files containing computed statistics:

```json
{
  "metadata": {
    "persona": "A",
    "id": "621e2f9167b776a240011ccb",
    "start_date": "2022-01-07",
    "computed_at": "2024-01-15T10:30:00",
    "days_count": 14
  },
  "base_stats": {
    "avg_steps": 4823.5,
    "avg_sleep": 5.7,
    "steps_variance": 1234567,
    "steps_std": 1111,
    "steps_min": 2000,
    "steps_max": 8000,
    "sleep_variance": 0.85,
    "sleep_std": 0.92,
    "sleep_min": 4.5,
    "sleep_max": 7.2,
    "date_range": {
      "start": "2022-01-07",
      "end": "2022-01-20"
    }
  },
  "correlations": {
    "steps_sleep": 0.32
  },
  "trends": {
    "steps": {"trend": "stable", "slope": 0.05},
    "sleep": {"trend": "decreasing", "slope": -0.18}
  },
  "weekday_patterns": {
    "weekday_avg_steps": 5200,
    "weekend_avg_steps": 3800,
    "weekday_avg_sleep": 5.5,
    "weekend_avg_sleep": 6.8,
    "steps_weekend_diff": -1400,
    "sleep_weekend_diff": 1.3
  }
}
```

## Key Components

### 1. Statistics Computation (`statistics.py`)

Core statistical calculations without any LLM dependency:

- `calculate_correlation()`: Pearson correlation between two metrics
- `identify_trend()`: Weighted linear regression with exponential decay
- `calculate_base_stats()`: Comprehensive summary statistics
- `calculate_weekday_patterns()`: Weekday vs weekend analysis
- `compute_all_statistics()`: Main entry point combining all calculations
- `format_statistics_summary()`: Human-readable console output

### 2. Prompt Builder (`prompt_builder.py`)

Populates the observer prompt template with computed statistics:

- `get_prompt_template()`: Loads the observer prompt from `prompts/observer_prompt.txt`
- `format_raw_health_data()`: Formats daily data for the prompt
- `format_variance_data()`: Formats variance/variability statistics
- `format_trends_data()`: Formats trend and weekday pattern data
- `format_correlations_data()`: Formats correlation values
- `build_observer_prompt()`: Main function that fills all template placeholders

### 3. Generate Prompt CLI (`generate_prompt.py`)

Main command-line tool that produces both statistics and the filled prompt:

- Takes health data JSON + user profile (age, gender)
- Outputs `precomputed_<persona>.json` with statistics
- Outputs `prompt_<persona>.txt` ready for any LLM

### 4. Insight Generation (`insights.py`)

Optional alternative for LLM-based insight generation, provider-agnostic:

- `build_insight_prompt()`: Constructs an alternative prompt format
- `parse_insights_response()`: Parses LLM JSON response
- `generate_insights()`: Main function accepting any LLM callable
- `add_insights_to_statistics()`: Merges insights into statistics dict
- `mock_llm_function()`: For testing without API calls

### 5. Statistics CLI (`compute_statistics.py`)

Command-line interface for statistics-only processing:

- Processes one or multiple persona files
- Outputs formatted console summary
- Generates JSON files for downstream use

## Methodology

### Trend Detection

Trends are identified using weighted linear regression:

1. Convert dates to ordinal values for x-axis
2. Apply exponential decay weights (recent days weighted more)
3. Fit linear regression with weights
4. Classify based on slope threshold (±0.15)

```
trend = "increasing"  if slope > 0.15
trend = "decreasing"  if slope < -0.15
trend = "stable"      otherwise
```

### Correlation Analysis

Pearson correlation coefficient between steps and sleep:

- Positive correlation: More steps associated with more sleep
- Negative correlation: More steps associated with less sleep
- Near zero: No linear relationship

### Weekday Pattern Analysis

Compares weekday (Mon-Fri) vs weekend (Sat-Sun) averages:

- `steps_weekend_diff`: Weekend steps minus weekday steps
- `sleep_weekend_diff`: Weekend sleep minus weekday sleep

Positive sleep difference indicates weekend recovery pattern.

## Two-Step Workflow

The pipeline separates statistics from insights for flexibility:

### Step 1: Compute Statistics (Always)

```python
from statistics import compute_all_statistics
import json

with open('persona_a.json') as f:
    persona_data = json.load(f)

stats = compute_all_statistics(persona_data)
```

### Step 2: Generate Insights (Optional)

```python
from insights import generate_insights, add_insights_to_statistics

# Provide your own LLM function
def my_llm(prompt):
    # Call OpenAI, Anthropic, local model, etc.
    return response_text

insights = generate_insights(persona_data, stats, my_llm)
final = add_insights_to_statistics(stats, insights)
```

## LLM Integration

The insights module is provider-agnostic. Implement a function matching this signature:

```python
def llm_function(prompt: str) -> str:
    """Takes prompt, returns LLM response as string."""
    pass
```

### Example: OpenAI

```python
import openai

def call_openai(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

insights = generate_insights(persona_data, stats, call_openai)
```

### Example: Mock (Testing)

```python
from insights import mock_llm_function

insights = generate_insights(persona_data, stats, mock_llm_function)
```

## Statistics Details

### Base Statistics

| Statistic | Description |
|-----------|-------------|
| `avg_steps` | Mean daily step count |
| `avg_sleep` | Mean daily sleep hours |
| `steps_variance` | Variance of step counts |
| `sleep_variance` | Variance of sleep hours |
| `steps_std` | Standard deviation of steps |
| `sleep_std` | Standard deviation of sleep |
| `steps_min/max` | Range of step counts |
| `sleep_min/max` | Range of sleep hours |

### Trend Classification

| Trend | Condition | Interpretation |
|-------|-----------|----------------|
| `increasing` | slope > 0.15 | Metric rising over time |
| `decreasing` | slope < -0.15 | Metric falling over time |
| `stable` | -0.15 ≤ slope ≤ 0.15 | No significant change |

### Correlation Interpretation

| Range | Interpretation |
|-------|----------------|
| 0.7 to 1.0 | Strong positive |
| 0.3 to 0.7 | Moderate positive |
| -0.3 to 0.3 | Weak/no correlation |
| -0.7 to -0.3 | Moderate negative |
| -1.0 to -0.7 | Strong negative |

## Language Support

The insight generation supports multiple languages:

```python
# English (default)
insights = generate_insights(persona_data, stats, llm_fn, language="en")

# German
insights = generate_insights(persona_data, stats, llm_fn, language="de")
```

## Limitations

- Correlation limited to steps vs sleep (only two metrics available)
- Trend detection assumes linear patterns
- Insights quality depends on LLM provider
- Requires minimum 3 data points for trend calculation

## Citation

If you use this pipeline in your research, please cite:

```
[TBD]
```
