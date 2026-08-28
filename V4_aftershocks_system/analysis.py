"""Analysis helpers for the earthquake simulation package.

This module collects small helper functions used by example scripts and plots.
"""

from __future__ import annotations

from typing import Iterable, Sequence, Tuple

import numpy as np


def _normalize_event_types(event_types):
    if event_types is None:
        return None
    if isinstance(event_types, str):
        return {event_types}
    return {str(t) for t in event_types}


def filter_events(events: Iterable[dict], event_types=None) -> list[dict]:
    """Return events filtered by type.

    If event_types is None, all events are returned.
    """
    allowed = _normalize_event_types(event_types)
    if allowed is None:
        return list(events)
    return [e for e in events if str(e.get('type')) in allowed]


def monthly_counts(events: Iterable[dict], num_months: int = 12, event_types=None) -> np.ndarray:
    """Count events in each month of the synthetic year."""
    counts = np.zeros(num_months, dtype=int)
    allowed = _normalize_event_types(event_types)
    for month in range(1, num_months + 1):
        counts[month - 1] = sum(
            1
            for e in events
            if int(e.get('month', 0)) == month
            and (allowed is None or str(e.get('type')) in allowed)
        )
    return counts


def expected_monthly_counts(lambda0: float, k: float, n_months: int = 12, duration_years: float = 1.0) -> np.ndarray:
    """Expected number of events in each month for lambda(t) = lambda0 * exp(k t)."""
    month_edges = np.linspace(0.0, duration_years, n_months + 1)
    expected = np.zeros(n_months, dtype=float)

    for i in range(n_months):
        t0 = float(month_edges[i])
        t1 = float(month_edges[i + 1])
        if k == 0.0:
            expected[i] = lambda0 * (t1 - t0)
        else:
            expected[i] = (lambda0 / k) * (np.exp(k * t1) - np.exp(k * t0))
    return expected


def cumulative_magnitude_frequency(
    events: Iterable[dict],
    min_mag: float | None = None,
    max_mag: float | None = None,
    step: float = 1.0,
    event_types=None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return cumulative counts N(M >= m) at regular magnitude thresholds."""
    filtered = filter_events(events, event_types=event_types)
    mags = np.array([float(e['magnitude']) for e in filtered], dtype=float)
    if mags.size == 0:
        return np.array([]), np.array([])

    if min_mag is None:
        min_mag = float(np.floor(mags.min()))
    if max_mag is None:
        max_mag = float(np.ceil(mags.max()))

    thresholds = np.arange(min_mag, max_mag + step, step, dtype=float)
    cumulative_counts = np.array([np.sum(mags >= thr) for thr in thresholds], dtype=float)
    return thresholds, cumulative_counts


def fit_gr_line(thresholds: np.ndarray, cumulative_counts: np.ndarray) -> Tuple[float | None, float | None]:
    """Estimate Gutenberg-Richter a and b from the observed catalogue."""
    thresholds = np.asarray(thresholds, dtype=float)
    cumulative_counts = np.asarray(cumulative_counts, dtype=float)

    mask = cumulative_counts > 0
    if np.count_nonzero(mask) < 2:
        return None, None

    x = thresholds[mask]
    y = np.log10(cumulative_counts[mask])
    slope, intercept = np.polyfit(x, y, 1)
    b_est = -float(slope)
    a_est = float(intercept)
    return a_est, b_est


def theoretical_gr_line(
    thresholds: np.ndarray,
    b_value: float,
    a_value: float | None = None,
    anchor_count: float | None = None,
    anchor_threshold: float | None = None,
) -> np.ndarray:
    """Construct a Gutenberg-Richter curve using a specified b value.

    If a_value is omitted, the line is anchored to a single observed point.
    """
    thresholds = np.asarray(thresholds, dtype=float)
    if thresholds.size == 0:
        return np.array([])

    if a_value is None:
        if anchor_count is None or anchor_threshold is None:
            raise ValueError('Provide either a_value or both anchor_count and anchor_threshold.')
        if anchor_count <= 0:
            return np.zeros_like(thresholds, dtype=float)
        a_value = float(np.log10(anchor_count) + b_value * anchor_threshold)

    return 10.0 ** (a_value - b_value * thresholds)


def fitted_gr_line(thresholds: np.ndarray, a_est: float | None, b_est: float | None) -> np.ndarray:
    """Gutenberg-Richter curve using fitted a and b values."""
    thresholds = np.asarray(thresholds, dtype=float)
    if a_est is None or b_est is None or thresholds.size == 0:
        return np.array([])
    return 10.0 ** (a_est - b_est * thresholds)
