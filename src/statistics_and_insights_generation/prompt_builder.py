"""
Prompt builder for the Observer agent.

This module populates the observer prompt template with computed statistics
and user profile data. The filled prompt can then be used with any LLM.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional


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

        steps_str = f"{steps:.0f} steps" if steps is not None else "N/A"
        sleep_str = f"{sleep:.1f}h sleep" if sleep is not None else "N/A"

        lines.append(f"  {date_str}: {steps_str}, {sleep_str}")

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

    steps_trend = trends.get('steps', {})
    sleep_trend = trends.get('sleep', {})

    lines = [
        f"Steps trend: {steps_trend.get('trend', 'unknown')} (slope: {steps_trend.get('slope', 0):.4f})",
        f"Sleep trend: {sleep_trend.get('trend', 'unknown')} (slope: {sleep_trend.get('slope', 0):.4f})",
        f"Weekday vs Weekend:",
        f"  Steps: weekday avg={patterns.get('weekday_avg_steps', 0):.0f}, weekend avg={patterns.get('weekend_avg_steps', 0):.0f}",
        f"  Sleep: weekday avg={patterns.get('weekday_avg_sleep', 0):.2f}h, weekend avg={patterns.get('weekend_avg_sleep', 0):.2f}h"
    ]

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
    steps_sleep_corr = corr.get('steps_sleep')

    if steps_sleep_corr is not None:
        return f"Steps vs Sleep: {steps_sleep_corr:.3f}"
    else:
        return "Steps vs Sleep: insufficient data"


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
