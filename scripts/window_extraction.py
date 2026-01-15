"""
Time window extraction and candidate selection.

This module handles sliding window extraction over participant timelines,
scoring each window against persona profiles, and selecting the best candidates.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple

try:
    from .data_validation import prepare_window
    from .persona_scoring import score_persona_a, score_persona_b
except ImportError:
    from data_validation import prepare_window
    from persona_scoring import score_persona_a, score_persona_b


class WindowCandidate:
    """Represents a candidate time window with its persona fit score."""

    def __init__(self, participant_id: str, start_date: pd.Timestamp, persona: str, fit_score: float):
        self.participant_id = participant_id
        self.start_date = start_date
        self.persona = persona
        self.fit_score = fit_score

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "id": self.participant_id,
            "start_date": self.start_date.strftime("%Y-%m-%d"),
            "persona": self.persona,
            "fit_score": round(self.fit_score, 4)
        }

    def __repr__(self) -> str:
        return (
            f"Candidate(id={self.participant_id}, "
            f"start={self.start_date.date()}, "
            f"persona={self.persona}, "
            f"score={self.fit_score:.4f})"
        )


def extract_candidates(
    df: pd.DataFrame,
    col_id: str = "id",
    col_date: str = "date",
    col_steps: str = "steps",
    col_sleep: str = "minutesAsleep",
    col_rhr: str = "resting_hr",
    window_days: int = 14,
    min_present_days: int = 12
) -> List[WindowCandidate]:
    """
    Extract all viable window candidates from the dataset.

    This function slides a time window over each participant's timeline,
    validates data quality, and scores each window against both persona profiles.

    Args:
        df: DataFrame with participant health data
        col_id: Column name for participant ID
        col_date: Column name for date
        col_steps: Column name for step counts
        col_sleep: Column name for sleep in minutes
        col_rhr: Column name for resting heart rate
        window_days: Window size in days
        min_present_days: Minimum days with valid data

    Returns:
        List of WindowCandidate objects with fit scores
    """
    df = df.copy()
    df[col_date] = pd.to_datetime(df[col_date])
    df = df.sort_values([col_id, col_date])

    candidates = []

    for pid, group in df.groupby(col_id):
        group = group.sort_values(col_date).reset_index(drop=True)

        if len(group) < window_days:
            continue

        for i in range(len(group) - window_days + 1):
            window = group.iloc[i:i + window_days].copy()

            window_prepared, is_valid, error = prepare_window(
                window, col_date, col_steps, col_sleep, window_days, min_present_days
            )

            if not is_valid:
                continue

            start_date = window_prepared[col_date].iloc[0]

            # Score against Persona A
            score_a = score_persona_a(window_prepared, col_steps, col_sleep)
            candidates.append(WindowCandidate(str(pid), start_date, "A", score_a))

            # Score against Persona B
            score_b = score_persona_b(window_prepared, col_steps, col_sleep, col_rhr)
            candidates.append(WindowCandidate(str(pid), start_date, "B", score_b))

    return candidates


def select_top_candidates(
    candidates: List[WindowCandidate],
    top_k: int = 5
) -> Tuple[List[WindowCandidate], List[WindowCandidate]]:
    """
    Select top K candidates for each persona.

    Args:
        candidates: List of all window candidates
        top_k: Number of top candidates to select per persona

    Returns:
        Tuple of (top_persona_a, top_persona_b) candidate lists
    """
    persona_a = [c for c in candidates if c.persona == "A"]
    persona_b = [c for c in candidates if c.persona == "B"]

    persona_a.sort(key=lambda x: x.fit_score, reverse=True)
    persona_b.sort(key=lambda x: x.fit_score, reverse=True)

    return persona_a[:top_k], persona_b[:top_k]


def select_random_from_viable(
    candidates: List[WindowCandidate],
    threshold: float = 0.5,
    seed: int = None
) -> WindowCandidate:
    """
    Select a random candidate from those above the viability threshold.

    Args:
        candidates: List of candidates to choose from
        threshold: Minimum fit score to be considered viable
        seed: Random seed for reproducibility

    Returns:
        Randomly selected viable candidate

    Raises:
        ValueError: If no viable candidates found
    """
    viable = [c for c in candidates if c.fit_score >= threshold]

    if not viable:
        raise ValueError(f"No viable candidates found (threshold={threshold})")

    if seed is not None:
        np.random.seed(seed)

    return np.random.choice(viable)


def extract_window_data(
    df: pd.DataFrame,
    participant_id: str,
    start_date: str,
    col_id: str = "id",
    col_date: str = "date",
    col_steps: str = "steps",
    col_sleep: str = "minutesAsleep",
    window_days: int = 14
) -> pd.DataFrame:
    """
    Extract a specific time window for a participant.

    Args:
        df: DataFrame with participant health data
        participant_id: Target participant ID
        start_date: Start date of window (YYYY-MM-DD)
        col_id: Column name for participant ID
        col_date: Column name for date
        col_steps: Column name for step counts
        col_sleep: Column name for sleep in minutes
        window_days: Window size in days

    Returns:
        DataFrame with the extracted window

    Raises:
        ValueError: If window cannot be extracted or validated
    """
    df = df.copy()
    df[col_date] = pd.to_datetime(df[col_date])

    start = pd.to_datetime(start_date)
    end = start + pd.Timedelta(days=window_days)

    participant_data = df[df[col_id].astype(str) == str(participant_id)].sort_values(col_date)
    window = participant_data[(participant_data[col_date] >= start) & (participant_data[col_date] < end)].copy()

    window_prepared, is_valid, error = prepare_window(
        window, col_date, col_steps, col_sleep, window_days
    )

    if not is_valid:
        raise ValueError(f"Invalid window for id={participant_id}, start={start_date}: {error}")

    return window_prepared
