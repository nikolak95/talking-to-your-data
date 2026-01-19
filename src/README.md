# Source Code

This directory contains the processing pipelines for the user study.

## Persona Extraction

**Directory:** `persona_extraction/`

Pipeline for extracting 14-day data windows from the [LifeSnaps dataset](https://github.com/Kaist-ICLab/LifeSnaps-Fitbit) based on activity and sleep criteria. The pipeline scores participants on sedentary vs. active behavior and sleep patterns to identify candidates matching each persona profile.

**Key files:**
- `extract_personas.py` – Main extraction script
- `persona_scoring.py` – Scoring logic for persona matching
- `window_extraction.py` – 14-day window selection
- `data_validation.py` – Data quality checks
- `visualization.py` – Plotting utilities

**Output:** `persona_a.json`, `persona_b.json` – 14-day health data for each persona.


## Statistics & Insights Generation

**Directory:** `statistics_and_insights_generation/`

Tools to compute descriptive statistics from persona data and generate filled observer prompts for LLM-based insight generation. See the [detailed README](statistics_and_insights_generation/README_STATISTICS.md) for full documentation.

**Key files:**
- `statistics.py` – Core statistical calculations (correlations, trends, weekday patterns)
- `prompt_builder.py` – Populates the observer prompt template with computed statistics
- `generate_prompt.py` – CLI that outputs both statistics JSON and filled prompt

**Usage:**
```bash
python generate_prompt.py persona_a.json --age 28 --gender male
```

**Outputs:**
1. `precomputed_<persona>.json` – Computed statistics
2. `prompt_<persona>.txt` – Filled observer prompt ready for any LLM
