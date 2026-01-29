"""
Prompt builder for the Observer agent.

This module populates the observer prompt template with computed statistics
and user profile data. The filled prompt can then be used with any LLM.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

from statistics import EXTRA_METRICS


def get_prompt_template() -> str:
    """
    Load the observer prompt template from the prompts directory.

    Returns:
        The raw prompt template string with placeholders
    """
    # Navigate from this file to the prompts directory
    module_dir = Path(__file__).parent
    repo_root = module_dir.parent.parent
    prompt_path = repo_root / "prompts" / "observer_prompt.txt"

    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def format_raw_health_data(persona_data: Dict[str, Any]) -> str:
    """
    Format the raw health data for inclusion in the prompt.

    Args:
        persona_data: The persona JSON with 'days' array

    Returns:
        Formatted string with one line per day
    """
    days = persona_data.get('days', [])
    if not days:
        return "No data available"

    lines = []
    for day in days:
        date_str = day.get('date', 'Unknown')
        steps = day.get('steps')
        sleep = day.get('sleep_hours')

        parts = [
            f"{steps:.0f} steps" if steps is not None else "steps: N/A",
            f"{sleep:.1f}h sleep" if sleep is not None else "sleep: N/A",
        ]

        rhr = day.get('resting_hr')
        if rhr is not None:
            parts.append(f"RHR {rhr:.0f}bpm")

        cal = day.get('calories')
        if cal is not None:
            parts.append(f"{cal:.0f}kcal")

        active = day.get('active_minutes')
        if active is not None:
            parts.append(f"{active:.0f}min active")

        sedentary = day.get('sedentary_minutes')
        if sedentary is not None:
            parts.append(f"{sedentary:.0f}min sedentary")

        eff = day.get('sleep_efficiency')
        if eff is not None:
            parts.append(f"sleep eff {eff:.0f}%")

        lines.append(f"  {date_str}: {', '.join(parts)}")

    return "\n".join(lines)


def format_variance_data(statistics: Dict[str, Any]) -> str:
    """
    Format variance/variability statistics for the prompt.

    Args:
        statistics: Computed statistics from compute_all_statistics()

    Returns:
        Formatted string describing data variance
    """
    base = statistics.get('base_stats', {})

    lines = [
        f"Steps: std={base.get('steps_std', 0):.0f}, range=[{base.get('steps_min', 0):.0f}, {base.get('steps_max', 0):.0f}]",
        f"Sleep: std={base.get('sleep_std', 0):.2f}h, range=[{base.get('sleep_min', 0):.2f}h, {base.get('sleep_max', 0):.2f}h]"
    ]

    label_map = {
        "resting_hr": ("Resting HR", "bpm"),
        "calories": ("Calories", "kcal"),
        "active_minutes": ("Active Minutes", "min"),
        "sedentary_minutes": ("Sedentary Minutes", "min"),
        "sleep_efficiency": ("Sleep Efficiency", "%"),
    }
    for metric in EXTRA_METRICS:
        ms = base.get(metric)
        if ms:
            label, unit = label_map.get(metric, (metric, ""))
            lines.append(f"{label}: std={ms['std']:.1f}{unit}, range=[{ms['min']:.1f}, {ms['max']:.1f}]")

    return "\n".join(lines)


def format_trends_data(statistics: Dict[str, Any]) -> str:
    """
    Format trend data for the prompt.

    Args:
        statistics: Computed statistics from compute_all_statistics()

    Returns:
        Formatted string describing trends
    """
    trends = statistics.get('trends', {})
    patterns = statistics.get('weekday_patterns', {})

    lines = []

    for key, trend_data in trends.items():
        if trend_data:
            lines.append(f"{key} trend: {trend_data.get('trend', 'unknown')} (slope: {trend_data.get('slope', 0):.4f})")

    lines.append(f"Weekday vs Weekend:")
    lines.append(f"  Steps: weekday avg={patterns.get('weekday_avg_steps', 0):.0f}, weekend avg={patterns.get('weekend_avg_steps', 0):.0f}")
    lines.append(f"  Sleep: weekday avg={patterns.get('weekday_avg_sleep', 0):.2f}h, weekend avg={patterns.get('weekend_avg_sleep', 0):.2f}h")

    label_map = {
        "resting_hr": "Resting HR",
        "calories": "Calories",
        "active_minutes": "Active Minutes",
        "sedentary_minutes": "Sedentary Minutes",
        "sleep_efficiency": "Sleep Efficiency",
    }
    for metric in EXTRA_METRICS:
        mp = patterns.get(metric)
        if mp:
            label = label_map.get(metric, metric)
            lines.append(f"  {label}: weekday avg={mp['weekday_avg']:.1f}, weekend avg={mp['weekend_avg']:.1f}")

    return "\n".join(lines)


def format_correlations_data(statistics: Dict[str, Any]) -> str:
    """
    Format correlation data for the prompt.

    Args:
        statistics: Computed statistics from compute_all_statistics()

    Returns:
        Formatted string describing correlations
    """
    corr = statistics.get('correlations', {})

    lines = []
    label_map = {
        "steps_sleep": "Steps vs Sleep",
        "steps_resting_hr": "Steps vs Resting HR",
        "active_minutes_sleep_hours": "Active Minutes vs Sleep",
        "active_minutes_resting_hr": "Active Minutes vs Resting HR",
        "calories_steps": "Calories vs Steps",
        "sleep_hours_sleep_efficiency": "Sleep Duration vs Sleep Efficiency",
    }
    for key, val in corr.items():
        if val is not None:
            label = label_map.get(key, key)
            lines.append(f"{label}: {val:.3f}")

    return "\n".join(lines) if lines else "Insufficient data for correlations"


def build_observer_prompt(
    persona_data: Dict[str, Any],
    statistics: Dict[str, Any],
    user_age: str,
    user_gender: str
) -> str:
    """
    Build a complete observer prompt with all placeholders filled.

    Args:
        persona_data: The persona JSON with 'days' array
        statistics: Computed statistics from compute_all_statistics()
        user_age: User's age (e.g., "28" or "late 20s")
        user_gender: User's gender (e.g., "male", "female", "non-binary")

    Returns:
        Complete prompt string ready for LLM consumption
    """
    template = get_prompt_template()

    prompt = template.replace("{USER_AGE}", user_age)
    prompt = prompt.replace("{USER_GENDER}", user_gender)
    prompt = prompt.replace("{RAW_HEALTH_DATA}", format_raw_health_data(persona_data))
    prompt = prompt.replace("{PRECOMPUTED_VARIANCE}", format_variance_data(statistics))
    prompt = prompt.replace("{PRECOMPUTED_TRENDS}", format_trends_data(statistics))
    prompt = prompt.replace("{PRECOMPUTED_CORRELATIONS}", format_correlations_data(statistics))

    return prompt
