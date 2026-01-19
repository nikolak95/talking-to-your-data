"""
Statistics computation for persona data.

This module calculates correlations, trends, and summary statistics
from the extracted persona JSON files. LLM-based insight generation
is intentionally excluded and can be added as a separate step.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime


def calculate_correlation(df: pd.DataFrame, col1: str, col2: str) -> Optional[float]:
    """
    Calculate Pearson correlation between two columns.

    Args:
        df: DataFrame with the data
        col1: First column name
        col2: Second column name

    Returns:
        Correlation coefficient, or None if cannot be calculated
    """
    if col1 not in df.columns or col2 not in df.columns:
        return None

    valid_data = df[[col1, col2]].dropna()
    if len(valid_data) < 3:
        return None

    corr = valid_data[col1].corr(valid_data[col2])
    return float(corr) if pd.notna(corr) else None


def identify_trend(
    values: pd.Series,
    dates: pd.Series,
    threshold: float = 0.15,
    decay: float = 0.95
) -> Dict[str, Any]:
    """
    Identify trend using weighted linear regression.

    Recent values are weighted more heavily using exponential decay.

    Args:
        values: Series of metric values
        dates: Series of corresponding dates
        threshold: Slope threshold for trend classification
        decay: Exponential decay factor for weighting (0.95 = recent days weighted more)

    Returns:
        Dict with trend classification and slope
    """
    valid_mask = values.notna()
    values = values[valid_mask].astype(float)
    dates = pd.to_datetime(dates[valid_mask])

    if len(values) < 3:
        return {"trend": "insufficient_data", "slope": 0.0}

    # Sort by date
    sorted_idx = dates.argsort()
    values = values.iloc[sorted_idx]
    dates = dates.iloc[sorted_idx]

    # Convert dates to ordinal for regression
    x = dates.map(pd.Timestamp.toordinal).values
    y = values.values
    n = len(x)

    # Exponential decay weights (more recent = higher weight)
    weights = np.array([decay ** (n - i - 1) for i in range(n)])

    # Weighted linear regression
    slope, intercept = np.polyfit(x, y, 1, w=weights)

    # Classify trend
    if slope > threshold:
        trend = "increasing"
    elif slope < -threshold:
        trend = "decreasing"
    else:
        trend = "stable"

    return {
        "trend": trend,
        "slope": float(slope)
    }


def calculate_base_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate base statistics from daily data.

    Args:
        df: DataFrame with 'date', 'steps', 'sleep_hours' columns

    Returns:
        Dict with averages, variance, std, and date range
    """
    stats = {
        "avg_steps": 0.0,
        "avg_sleep": 0.0,
        "steps_variance": 0.0,
        "sleep_variance": 0.0,
        "steps_std": 0.0,
        "sleep_std": 0.0,
        "steps_min": 0.0,
        "steps_max": 0.0,
        "sleep_min": 0.0,
        "sleep_max": 0.0,
        "date_range": {"start": None, "end": None}
    }

    if df.empty:
        return stats

    # Parse dates
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])

    # Date range
    stats["date_range"] = {
        "start": df['date'].min().strftime('%Y-%m-%d'),
        "end": df['date'].max().strftime('%Y-%m-%d')
    }

    # Steps statistics
    if 'steps' in df.columns:
        steps = df['steps'].dropna()
        if len(steps) > 0:
            stats["avg_steps"] = float(steps.mean())
            stats["steps_variance"] = float(steps.var())
            stats["steps_std"] = float(steps.std())
            stats["steps_min"] = float(steps.min())
            stats["steps_max"] = float(steps.max())

    # Sleep statistics
    if 'sleep_hours' in df.columns:
        sleep = df['sleep_hours'].dropna()
        if len(sleep) > 0:
            stats["avg_sleep"] = float(sleep.mean())
            stats["sleep_variance"] = float(sleep.var())
            stats["sleep_std"] = float(sleep.std())
            stats["sleep_min"] = float(sleep.min())
            stats["sleep_max"] = float(sleep.max())

    return stats


def calculate_weekday_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate weekday vs weekend patterns.

    Args:
        df: DataFrame with 'date', 'steps', 'sleep_hours' columns

    Returns:
        Dict with weekday/weekend averages and differences
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['is_weekend'] = df['date'].dt.dayofweek >= 5

    patterns = {
        "weekday_avg_steps": 0.0,
        "weekend_avg_steps": 0.0,
        "weekday_avg_sleep": 0.0,
        "weekend_avg_sleep": 0.0,
        "steps_weekend_diff": 0.0,
        "sleep_weekend_diff": 0.0
    }

    weekday_data = df[~df['is_weekend']]
    weekend_data = df[df['is_weekend']]

    # Steps patterns
    if 'steps' in df.columns:
        wd_steps = weekday_data['steps'].dropna()
        we_steps = weekend_data['steps'].dropna()

        if len(wd_steps) > 0:
            patterns["weekday_avg_steps"] = float(wd_steps.mean())
        if len(we_steps) > 0:
            patterns["weekend_avg_steps"] = float(we_steps.mean())

        patterns["steps_weekend_diff"] = patterns["weekend_avg_steps"] - patterns["weekday_avg_steps"]

    # Sleep patterns
    if 'sleep_hours' in df.columns:
        wd_sleep = weekday_data['sleep_hours'].dropna()
        we_sleep = weekend_data['sleep_hours'].dropna()

        if len(wd_sleep) > 0:
            patterns["weekday_avg_sleep"] = float(wd_sleep.mean())
        if len(we_sleep) > 0:
            patterns["weekend_avg_sleep"] = float(we_sleep.mean())

        patterns["sleep_weekend_diff"] = patterns["weekend_avg_sleep"] - patterns["weekday_avg_sleep"]

    return patterns


def compute_all_statistics(persona_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute all statistics from persona JSON data.

    This is the main entry point for statistics computation.

    Args:
        persona_data: Loaded persona JSON (with 'days' array)

    Returns:
        Complete statistics dict ready for JSON export
    """
    days = persona_data.get('days', [])
    df = pd.DataFrame(days)

    if df.empty:
        return {
            "metadata": {
                "persona": persona_data.get('persona', 'Unknown'),
                "id": persona_data.get('id', 'Unknown'),
                "computed_at": datetime.now().isoformat(),
                "days_count": 0
            },
            "base_stats": calculate_base_stats(df),
            "correlations": {},
            "trends": {},
            "weekday_patterns": {}
        }

    # Parse dates for trend analysis
    df['date'] = pd.to_datetime(df['date'])

    # Calculate correlation
    correlation = calculate_correlation(df, 'steps', 'sleep_hours')

    # Calculate trends
    steps_trend = identify_trend(df['steps'], df['date']) if 'steps' in df.columns else None
    sleep_trend = identify_trend(df['sleep_hours'], df['date']) if 'sleep_hours' in df.columns else None

    # Build output
    return {
        "metadata": {
            "persona": persona_data.get('persona', 'Unknown'),
            "id": persona_data.get('id', 'Unknown'),
            "start_date": persona_data.get('start_date', 'Unknown'),
            "computed_at": datetime.now().isoformat(),
            "days_count": len(days)
        },
        "base_stats": calculate_base_stats(df),
        "correlations": {
            "steps_sleep": correlation
        },
        "trends": {
            "steps": steps_trend,
            "sleep": sleep_trend
        },
        "weekday_patterns": calculate_weekday_patterns(df)
    }


def format_statistics_summary(stats: Dict[str, Any]) -> str:
    """
    Format statistics as a human-readable summary string.

    Args:
        stats: Output from compute_all_statistics()

    Returns:
        Formatted string for console output
    """
    lines = []
    lines.append("=" * 60)
    lines.append(f"Statistics for Persona {stats['metadata']['persona']}")
    lines.append("=" * 60)

    # Base stats
    base = stats['base_stats']
    lines.append(f"\nBase Statistics:")
    lines.append(f"  Steps:  avg={base['avg_steps']:.0f}, std={base['steps_std']:.0f}, range=[{base['steps_min']:.0f}, {base['steps_max']:.0f}]")
    lines.append(f"  Sleep:  avg={base['avg_sleep']:.2f}h, std={base['sleep_std']:.2f}h, range=[{base['sleep_min']:.2f}, {base['sleep_max']:.2f}]")

    # Correlation
    corr = stats['correlations'].get('steps_sleep')
    if corr is not None:
        lines.append(f"\nCorrelation (steps vs sleep): {corr:.3f}")

    # Trends
    lines.append(f"\nTrends:")
    if stats['trends'].get('steps'):
        t = stats['trends']['steps']
        lines.append(f"  Steps: {t['trend']} (slope={t['slope']:.4f})")
    if stats['trends'].get('sleep'):
        t = stats['trends']['sleep']
        lines.append(f"  Sleep: {t['trend']} (slope={t['slope']:.4f})")

    # Weekday patterns
    wp = stats['weekday_patterns']
    lines.append(f"\nWeekday Patterns:")
    lines.append(f"  Steps:  weekday={wp['weekday_avg_steps']:.0f}, weekend={wp['weekend_avg_steps']:.0f}, diff={wp['steps_weekend_diff']:+.0f}")
    lines.append(f"  Sleep:  weekday={wp['weekday_avg_sleep']:.2f}h, weekend={wp['weekend_avg_sleep']:.2f}h, diff={wp['sleep_weekend_diff']:+.2f}h")

    lines.append("=" * 60)

    return "\n".join(lines)
