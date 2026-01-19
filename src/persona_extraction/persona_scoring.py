"""
Persona fitness scoring functions.

This module defines scoring functions for two distinct health personas:
- Persona A: Sleep-deprived, irregular schedule with weekend recovery
- Persona B: Active lifestyle with moderate routine irregularity
"""

import numpy as np
import pandas as pd


def clamp01(x: float) -> float:
    """Clamp value to [0, 1] range."""
    return max(0.0, min(1.0, x))


def gaussian(x: float, mu: float, sigma: float) -> float:
    """Gaussian function for smooth scoring around a target value."""
    return np.exp(-((x - mu) ** 2) / (2 * sigma ** 2))


def score_persona_a(window: pd.DataFrame, col_steps: str, col_sleep: str) -> float:
    """
    Score window fit for Persona A: Sleep-deprived with weekend recovery.

    Characteristics:
    - Low-to-moderate activity (around 5000 steps)
    - Short sleep duration (around 5.75 hours)
    - Weekend sleep rebound (more sleep on weekends than weekdays)
    - Moderate step variability

    Args:
        window: DataFrame with daily data (14 days)
        col_steps: Column name for step counts
        col_sleep: Column name for sleep in minutes

    Returns:
        Fitness score in [0, 1] range
    """
    mean_steps = window[col_steps].mean()
    activity_fit = clamp01(1 - abs(mean_steps - 5000) / 5000)

    mean_sleep_h = window[col_sleep].mean() / 60
    sleep_fit = clamp01(1 - abs(mean_sleep_h - 5.75) / 2)

    wd_sleep = window.loc[~window["is_weekend"], col_sleep].mean()
    we_sleep = window.loc[window["is_weekend"], col_sleep].mean()
    weekend_fit = clamp01((we_sleep - wd_sleep) / 120 if pd.notna(we_sleep) else 0)

    step_var = window[col_steps].std() / max(mean_steps, 1)
    variability_fit = clamp01(step_var)

    return (
        0.35 * activity_fit +
        0.35 * sleep_fit +
        0.20 * weekend_fit +
        0.10 * variability_fit
    )


def score_persona_b(window: pd.DataFrame, col_steps: str, col_sleep: str, col_rhr: str) -> float:
    """
    Score window fit for Persona B: Active with irregular routine.

    Characteristics:
    - Moderately active (around 11000 steps)
    - Moderate step irregularity (CV around 0.45)
    - Moderate sleep irregularity (CV around 0.35)
    - Moderate resting heart rate (around 72 bpm)

    Args:
        window: DataFrame with daily data (14 days)
        col_steps: Column name for step counts
        col_sleep: Column name for sleep in minutes
        col_rhr: Column name for resting heart rate

    Returns:
        Fitness score in [0, 1] range
    """
    steps = window[col_steps].astype(float)
    sleep = window[col_sleep].astype(float) / 60.0
    rhr = window[col_rhr].astype(float)

    mean_steps = steps.mean()
    cv_steps = steps.std() / max(mean_steps, 1.0)

    mean_sleep = sleep.mean()
    cv_sleep = sleep.std() / max(mean_sleep, 1e-6)

    mean_rhr = rhr.mean()

    activity_fit = gaussian(mean_steps, mu=11000, sigma=3000)
    step_irregularity_fit = gaussian(cv_steps, mu=0.45, sigma=0.15)
    sleep_irregularity_fit = gaussian(cv_sleep, mu=0.35, sigma=0.15)
    rhr_fit = gaussian(mean_rhr, mu=72, sigma=6)

    return (
        0.40 * activity_fit +
        0.25 * step_irregularity_fit +
        0.20 * sleep_irregularity_fit +
        0.15 * rhr_fit
    )
