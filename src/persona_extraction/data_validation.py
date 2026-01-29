"""
Data validation utilities for window extraction.

This module handles validation of time windows from health tracking data,
ensuring data quality, contiguity, and coverage requirements.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def validate_window_contiguity(window: pd.DataFrame, col_date: str, window_days: int) -> Tuple[bool, str]:
    """
    Check if window has strictly contiguous daily data.

    Args:
        window: DataFrame with date column
        col_date: Name of date column
        window_days: Expected number of days

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(window) != window_days:
        return False, f"Window has {len(window)} rows, expected {window_days}"

    diffs = window[col_date].diff().dt.days.dropna()
    if (diffs != 1).any():
        return False, "Non-contiguous days detected (gaps in date sequence)"

    return True, ""


def clean_numeric_columns(window: pd.DataFrame, col_steps: str, col_sleep: str) -> pd.DataFrame:
    """
    Clean numeric columns by coercing invalid values to NaN.

    Args:
        window: DataFrame with health metrics
        col_steps: Column name for step counts
        col_sleep: Column name for sleep minutes

    Returns:
        DataFrame with cleaned numeric columns
    """
    window = window.copy()

    # Required columns
    window[col_steps] = pd.to_numeric(window[col_steps], errors="coerce")
    window[col_sleep] = pd.to_numeric(window[col_sleep], errors="coerce")

    window.loc[window[col_steps] < 0, col_steps] = np.nan
    window.loc[window[col_sleep] < 0, col_sleep] = np.nan

    # Optional columns — clean if present
    optional_cols = [
        "resting_hr", "calories",
        "lightly_active_minutes", "moderately_active_minutes",
        "very_active_minutes", "sedentary_minutes",
        "sleep_efficiency"
    ]
    for col in optional_cols:
        if col in window.columns:
            window[col] = pd.to_numeric(window[col], errors="coerce")
            window.loc[window[col] < 0, col] = np.nan

    return window


def validate_data_coverage(
    window: pd.DataFrame,
    col_steps: str,
    col_sleep: str,
    min_present_days: int
) -> Tuple[bool, str]:
    """
    Check if window has sufficient non-null data for both metrics.

    Args:
        window: DataFrame with health metrics
        col_steps: Column name for step counts
        col_sleep: Column name for sleep minutes
        min_present_days: Minimum required days with valid data

    Returns:
        Tuple of (is_valid, error_message)
    """
    steps_ok = (window[col_steps].notna() & (window[col_steps] > 0)).sum()
    sleep_ok = window[col_sleep].notna().sum()

    if steps_ok < min_present_days:
        return False, f"Insufficient step data: {steps_ok}/{len(window)} days (need >={min_present_days})"

    if sleep_ok < min_present_days:
        return False, f"Insufficient sleep data: {sleep_ok}/{len(window)} days (need >={min_present_days})"

    return True, ""


def add_derived_features(window: pd.DataFrame, col_date: str) -> pd.DataFrame:
    """
    Add derived features to window (day of week, weekend indicator).

    Args:
        window: DataFrame with date column
        col_date: Column name for date

    Returns:
        DataFrame with additional derived columns
    """
    window = window.copy()
    window["dow"] = window[col_date].dt.dayofweek
    window["is_weekend"] = window["dow"] >= 5
    return window


def prepare_window(
    window: pd.DataFrame,
    col_date: str,
    col_steps: str,
    col_sleep: str,
    window_days: int = 14,
    min_present_days: int = 12
) -> Tuple[pd.DataFrame, bool, str]:
    """
    Full validation and preparation pipeline for a time window.

    Args:
        window: Raw window DataFrame
        col_date: Column name for date
        col_steps: Column name for step counts
        col_sleep: Column name for sleep minutes
        window_days: Expected window size in days
        min_present_days: Minimum days with valid data

    Returns:
        Tuple of (prepared_window, is_valid, error_message)
    """
    is_valid, error = validate_window_contiguity(window, col_date, window_days)
    if not is_valid:
        return window, False, error

    window = clean_numeric_columns(window, col_steps, col_sleep)

    is_valid, error = validate_data_coverage(window, col_steps, col_sleep, min_present_days)
    if not is_valid:
        return window, False, error

    window = add_derived_features(window, col_date)

    return window, True, ""
