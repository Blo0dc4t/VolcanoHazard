"""Analysis helpers for the earthquake simulation package.

This module collects small helper functions used by example scripts and plots.
"""

from __future__ import annotations

from typing import Iterable, Sequence, Tuple

import numpy as np


def _filter_events(events: Iterable[dict], event_types=None) -> list[dict]:
    events = list(events)
    if event_types is None:
        return events
    if isinstance(event_types, str):
        event_types = {event_types}
    else:
        event_types = set(event_types)
    return [e for e in events if e.get("type") in event_types]


def monthly_counts(events: Iterable[dict], num_months: int = 12, event_types=None) -> np.ndarray:
    """Count events in each month of the synthetic year."""
    filtered = _filter_events(events, event_types=event_types)
    counts = np.zeros(num_months, dtype=int)
    for month in range(1, num_months + 1):
        counts[month - 1] = sum(1 for e in filtered if int(e.get("month", 0)) == month)
    return counts


def cumulative_magnitude_frequency(
    events: Iterable[dict],
    min_mag: float | None = None,
    max_mag: float | None = None,
    step: float = 1.0,
    event_types=None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return cumulative counts N(M >= m) at regular magnitude thresholds.

    If min_mag / max_mag are omitted, integer thresholds are taken from the
    observed catalogue range.
    """
    filtered = _filter_events(events, event_types=event_types)
    mags = np.array([float(e["magnitude"]) for e in filtered], dtype=float)
    if mags.size == 0:
        return np.array([]), np.array([])

    if min_mag is None:
        min_mag = float(np.floor(mags.min()))
    if max_mag is None:
        max_mag = float(np.ceil(mags.max()))

    thresholds = np.arange(min_mag, max_mag + step, step, dtype=float)
    cumulative_counts = np.array([np.sum(mags >= thr) for thr in thresholds], dtype=float)
    return thresholds, cumulative_counts


def fit_gr_line(thresholds: np.ndarray, cumulative_counts: np.ndarray):
    """Fit the Gutenberg-Richter relationship log10 N = a - bM to the data."""
    thresholds = np.asarray(thresholds, dtype=float)
    cumulative_counts = np.asarray(cumulative_counts, dtype=float)

    mask = cumulative_counts > 0
    if np.count_nonzero(mask) < 2:
        return None, None

    x = thresholds[mask]
    y = np.log10(cumulative_counts[mask])
    slope, intercept = np.polyfit(x, y, 1)
    return float(intercept), float(-slope)


def theoretical_gr_line(
    thresholds: np.ndarray,
    b_value: float,
    anchor_count: float | None = None,
    anchor_threshold: float | None = None,
    a_value: float | None = None,
) -> np.ndarray:
    """Construct a theoretical Gutenberg-Richter curve.

    Either provide a_value directly, or provide an anchor point to estimate a.
    """
    thresholds = np.asarray(thresholds, dtype=float)
    if thresholds.size == 0:
        return np.array([])

    if a_value is None:
        if anchor_count is None or anchor_threshold is None:
            raise ValueError("Provide either a_value or both anchor_count and anchor_threshold.")
        if anchor_count <= 0:
            return np.zeros_like(thresholds, dtype=float)
        a_value = float(np.log10(anchor_count) + b_value * anchor_threshold)

    return 10.0 ** (float(a_value) - float(b_value) * thresholds)


def fitted_gr_line(thresholds: np.ndarray, a_est, b_est) -> np.ndarray:
    """Gutenberg-Richter curve using fitted a and b values."""
    thresholds = np.asarray(thresholds, dtype=float)
    if a_est is None or b_est is None or thresholds.size == 0:
        return np.array([])
    return 10.0 ** (float(a_est) - float(b_est) * thresholds)


def expected_monthly_counts(
    base_lambda0: float,
    pressure_starts: Sequence[float],
    pressure_growth_rate: float,
    duration_years: float = 1.0,
) -> np.ndarray:
    """Expected background counts in each month for lambda(t) = lambda0 * P(t).

    pressure_starts should contain the pressure multiplier at the start of each
    month. Within each month the pressure is assumed to grow exponentially with
    the same growth rate used by the VolcanoState.
    """
    pressure_starts = np.asarray(list(pressure_starts), dtype=float)
    if pressure_starts.size == 0:
        return np.array([])

    dt = float(duration_years) / float(pressure_starts.size)
    g = float(pressure_growth_rate)

    if g == 0.0:
        return float(base_lambda0) * pressure_starts * dt

    growth_factor = (np.exp(g * dt) - 1.0) / g
    return float(base_lambda0) * pressure_starts * growth_factor
