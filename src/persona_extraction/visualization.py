"""
Visualization utilities for health data windows.

This module provides functions to create comparison plots and
Apple Health-style charts for persona data.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional


def plot_comparison(
    window_a: pd.DataFrame,
    window_b: pd.DataFrame,
    window_c: Optional[pd.DataFrame] = None,
    col_date: str = "date",
    col_steps: str = "steps",
    col_sleep: str = "minutesAsleep",
    title_a: str = "Persona A",
    title_b: str = "Persona B",
    title_c: str = "Persona C",
    output_path: Optional[str] = None
) -> None:
    """
    Create a side-by-side comparison plot of two or three windows.

    Args:
        window_a: DataFrame for Persona A
        window_b: DataFrame for Persona B
        window_c: Optional DataFrame for Persona C
        col_date: Column name for date
        col_steps: Column name for step counts
        col_sleep: Column name for sleep in minutes
        title_a: Title for Persona A subplot
        title_b: Title for Persona B subplot
        title_c: Title for Persona C subplot
        output_path: Optional path to save figure
    """
    def plot_single(ax, window, title):
        dates = window[col_date].dt.strftime("%m-%d").tolist()
        steps = window[col_steps].astype(float).values
        sleep_h = window[col_sleep].astype(float).values / 60.0
        is_weekend = window["is_weekend"].tolist()

        ax.bar(range(len(window)), steps, color="#FF6A2A", alpha=0.8)
        ax.set_xticks(range(len(window)))
        ax.set_xticklabels(dates, rotation=45, ha="right")
        ax.set_ylabel("Steps", color="#FF6A2A")
        ax.tick_params(axis='y', labelcolor="#FF6A2A")
        ax.set_title(title, fontsize=14, fontweight="bold")

        # Weekend shading
        for i, we in enumerate(is_weekend):
            if we:
                ax.axvspan(i - 0.5, i + 0.5, alpha=0.15, color="gray")

        # Sleep on twin axis
        ax2 = ax.twinx()
        ax2.plot(range(len(window)), sleep_h, marker="o", color="#006B67", linewidth=2)
        ax2.set_ylabel("Sleep (hours)", color="#006B67")
        ax2.tick_params(axis='y', labelcolor="#006B67")

        # Statistics
        mean_steps = np.nanmean(steps)
        mean_sleep = np.nanmean(sleep_h)
        ax.text(
            0.02, 0.98,
            f"Avg: {mean_steps:.0f} steps | {mean_sleep:.1f}h sleep",
            transform=ax.transAxes,
            va="top",
            fontsize=10,
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
        )

    n_panels = 3 if window_c is not None else 2
    fig, axes = plt.subplots(1, n_panels, figsize=(8 * n_panels, 5))
    plot_single(axes[0], window_a, title_a)
    plot_single(axes[1], window_b, title_b)
    if window_c is not None:
        plot_single(axes[2], window_c, title_c)
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=200, bbox_inches="tight")
        print(f"Saved comparison plot to: {output_path}")
    else:
        plt.show()

    plt.close()


def _safe_float(row: pd.Series, col: str) -> Optional[float]:
    """Extract a float value from a row, returning None if missing or NaN."""
    if col not in row.index:
        return None
    val = row[col]
    return float(val) if pd.notna(val) else None


def window_to_json(
    window: pd.DataFrame,
    persona: str,
    participant_id: str,
    col_date: str = "date",
    col_steps: str = "steps",
    col_sleep: str = "minutesAsleep"
) -> dict:
    """
    Convert a window DataFrame to JSON format.

    Args:
        window: DataFrame with health data
        persona: Persona label (A, B, or C)
        participant_id: Participant identifier
        col_date: Column name for date
        col_steps: Column name for step counts
        col_sleep: Column name for sleep in minutes

    Returns:
        Dictionary in persona JSON format
    """
    start_date = window[col_date].iloc[0]

    payload = {
        "persona": persona,
        "id": str(participant_id),
        "start_date": start_date.strftime("%Y-%m-%d"),
        "days": []
    }

    for _, row in window.iterrows():
        steps_val = float(row[col_steps]) if pd.notna(row[col_steps]) else None
        sleep_min = float(row[col_sleep]) if pd.notna(row[col_sleep]) else None
        sleep_hours = sleep_min / 60.0 if sleep_min is not None else None

        date_obj = pd.to_datetime(row[col_date])
        date_with_weekday = date_obj.strftime("%A, %Y-%m-%d")

        # Compute active_minutes as sum of activity levels
        lightly = _safe_float(row, "lightly_active_minutes")
        moderately = _safe_float(row, "moderately_active_minutes")
        very = _safe_float(row, "very_active_minutes")
        active_minutes = None
        if any(v is not None for v in (lightly, moderately, very)):
            active_minutes = sum(v for v in (lightly, moderately, very) if v is not None)

        day_entry = {
            "date": date_with_weekday,
            "steps": steps_val,
            "sleep_hours": sleep_hours,
            "resting_hr": _safe_float(row, "resting_hr"),
            "calories": _safe_float(row, "calories"),
            "active_minutes": active_minutes,
            "sedentary_minutes": _safe_float(row, "sedentary_minutes"),
            "sleep_efficiency": _safe_float(row, "sleep_efficiency"),
        }

        payload["days"].append(day_entry)

    return payload


def print_candidate_summary(candidates: list, persona: str, count: int = 5) -> None:
    """
    Print a formatted summary of top candidates.

    Args:
        candidates: List of WindowCandidate objects
        persona: Persona label for header
        count: Number of candidates to display
    """
    print(f"\n{'='*70}")
    print(f"Top {count} Candidates for Persona {persona}")
    print(f"{'='*70}")
    print(f"{'Rank':<6} {'ID':<25} {'Start Date':<12} {'Fit Score':<10}")
    print(f"{'-'*70}")

    for i, candidate in enumerate(candidates[:count], 1):
        print(f"{i:<6} {candidate.participant_id:<25} {candidate.start_date.date()} {candidate.fit_score:.4f}")

    print(f"{'='*70}")
