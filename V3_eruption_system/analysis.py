"""Analysis helpers for the earthquake simulation package."""

from __future__ import annotations

from typing import Sequence, Tuple

import numpy as np


def cumulative_magnitude_frequency(events, step: float = 1.0):
    """
    Compute the cumulative Gutenberg-Richter distribution.

    Returns:
        thresholds:
            magnitude thresholds used for N(M >= m)

        cumulative_counts:
            counts of events with magnitude >= each threshold
    """
    mags = np.array([e["magnitude"] for e in events], dtype=float)

    if mags.size == 0:
        return np.array([]), np.array([])

    min_mag = int(np.floor(mags.min()))
    max_mag = int(np.ceil(mags.max()))

    thresholds = np.arange(min_mag, max_mag + step, step, dtype=float)
    cumulative_counts = np.array([np.sum(mags >= thr) for thr in thresholds], dtype=float)

    return thresholds, cumulative_counts


def fit_gr_line(thresholds, cumulative_counts):
    """
    Fit the Gutenberg-Richter relationship

        log10 N = a - bM

    to the observed cumulative counts.

    Returns:
        a_est, b_est
    """
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


def theoretical_gr_line(thresholds, b_value, a_value=None, anchor_count=None, anchor_threshold=None):
    """
    Build a theoretical Gutenberg-Richter curve.

    You can either:
    - pass `a_value` directly, or
    - pass `anchor_count` and `anchor_threshold` to estimate a by anchoring
      the line to one observed point.

    Returns:
        predicted cumulative counts
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

    return 10 ** (a_value - b_value * thresholds)


def fitted_gr_line(thresholds, a_est, b_est):
    """
    Gutenberg-Richter curve using fitted a and b values.
    """
    thresholds = np.asarray(thresholds, dtype=float)

    if a_est is None or b_est is None or thresholds.size == 0:
        return np.array([])

    return 10 ** (a_est - b_est * thresholds)


def monthly_counts(events):
    """
    Count events in each month of the year.
    """
    counts = np.zeros(12, dtype=int)

    for month in range(1, 13):
        counts[month - 1] = sum(1 for e in events if e.get("month") == month)

    return counts


def expected_monthly_counts(lambda0, k, n_months=12, duration_years=1.0):
    """
    Expected number of events in each month for
    lambda(t) = lambda0 * exp(k t).

    Returns an array of length n_months.
    """
    month_edges = np.linspace(0.0, duration_years, n_months + 1)
    expected = np.zeros(n_months, dtype=float)

    for i in range(n_months):
        t0 = month_edges[i]
        t1 = month_edges[i + 1]

        if k == 0.0:
            expected[i] = lambda0 * (t1 - t0)
        else:
            expected[i] = (lambda0 / k) * (np.exp(k * t1) - np.exp(k * t0))

    return expected