"""Volcano eruption monitor.

This module watches seismicity and volcanic pressure, then decides when an
eruption should happen and what type it is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional

import numpy as np

from volcano_state import VolcanoState


def _sigmoid(x: float) -> float:
    x = float(np.clip(x, -60.0, 60.0))
    return float(1.0 / (1.0 + np.exp(-x)))


def _count_in_window(events: Iterable[Dict[str, Any]], current_time_years: float, window_days: float) -> tuple[int, float, float]:
    window_years = float(window_days) / 365.0
    recent = [
        e for e in events
        if 0.0 <= current_time_years - float(e.get("time_years", -1e9)) <= window_years
    ]
    count = len(recent)
    rate = count / max(window_years, 1e-12)
    max_mag = max((float(e.get("magnitude", 0.0)) for e in recent), default=0.0)
    return count, rate, max_mag


@dataclass
class VolcanoMonitor:
    """Probabilistic eruption monitor.

    Eruption likelihood is controlled by seismicity and pressure.
    The eruption type is then chosen probabilistically from the pressure level.
    """

    short_window_days: float = 30.0
    long_window_days: float = 90.0
    eruption_bias: float = -3.0
    eruption_pressure_midpoint: float = 1.6
    eruption_pressure_weight: float = 3.0
    eruption_rate_ratio_weight: float = 1.2
    eruption_count_weight: float = 0.15
    min_short_count: float = 6.0
    pdc_bias: float = -1.2
    pdc_pressure_midpoint: float = 2.4
    pdc_pressure_weight: float = 2.8
    pdc_rate_ratio_weight: float = 0.7
    eruption_cooldown_days: float = 30.0

    last_eruption_time: float = -np.inf
    last_eruption_type: Optional[str] = None
    eruption_log: list[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.short_window_days <= 0:
            raise ValueError("short_window_days must be positive.")
        if self.long_window_days <= 0:
            raise ValueError("long_window_days must be positive.")
        if self.long_window_days < self.short_window_days:
            raise ValueError("long_window_days should be >= short_window_days.")
        if self.eruption_cooldown_days < 0:
            raise ValueError("eruption_cooldown_days must be non-negative.")

    @property
    def eruption_count(self) -> int:
        return len(self.eruption_log)

    def status(
        self,
        events: Iterable[Dict[str, Any]],
        volcano_state: VolcanoState,
        current_time_years: float,
    ) -> Dict[str, Any]:
        """Return a snapshot of the recent seismicity and pressure state."""
        short_count, short_rate, short_max_mag = _count_in_window(events, current_time_years, self.short_window_days)
        long_count, long_rate, long_max_mag = _count_in_window(events, current_time_years, self.long_window_days)
        rate_ratio = short_rate / max(long_rate, 1e-12)
        pressure = volcano_state.current_pressure(current_time_years)
        cooldown_years = self.eruption_cooldown_days / 365.0
        cooldown_active = (float(current_time_years) - self.last_eruption_time) < cooldown_years

        return {
            "current_time_years": float(current_time_years),
            "pressure": float(pressure),
            "short_count": int(short_count),
            "long_count": int(long_count),
            "short_rate": float(short_rate),
            "long_rate": float(long_rate),
            "rate_ratio": float(rate_ratio),
            "max_recent_mag": float(short_max_mag),
            "max_recent_mag_long": float(long_max_mag),
            "cooldown_active": bool(cooldown_active),
            "last_eruption_time_years": None if not np.isfinite(self.last_eruption_time) else float(self.last_eruption_time),
            "last_eruption_type": self.last_eruption_type,
        }

    def eruption_probability(self, status: Dict[str, Any]) -> float:
        score = (
            self.eruption_bias
            + self.eruption_pressure_weight * (status["pressure"] - self.eruption_pressure_midpoint)
            + self.eruption_rate_ratio_weight * (status["rate_ratio"] - 1.0)
            + self.eruption_count_weight * (status["short_count"] - self.min_short_count)
        )
        return _sigmoid(score)

    def pdc_probability(self, status: Dict[str, Any]) -> float:
        score = (
            self.pdc_bias
            + self.pdc_pressure_weight * (status["pressure"] - self.pdc_pressure_midpoint)
            + self.pdc_rate_ratio_weight * (status["rate_ratio"] - 1.0)
        )
        return _sigmoid(score)

    def check_for_eruption(
        self,
        events: Iterable[Dict[str, Any]],
        volcano_state: VolcanoState,
        current_time_years: float,
        rng: Optional[np.random.Generator] = None,
    ) -> Optional[Dict[str, Any]]:
        """Probabilistically decide whether an eruption occurs.

        Seismicity mainly controls whether an eruption is triggered.
        Pressure controls whether the eruption is ash or ash + PDC.
        If an eruption occurs, pressure is immediately reduced.
        """
        if rng is None:
            rng = np.random.default_rng()

        status = self.status(events, volcano_state, current_time_years)
        if status["cooldown_active"]:
            return None

        trigger_prob = self.eruption_probability(status)
        trigger_draw = float(rng.random())
        if trigger_draw >= trigger_prob:
            return None

        pdc_prob = self.pdc_probability(status)
        pdc_draw = float(rng.random())
        eruption_type = "ash_and_pdc" if pdc_draw < pdc_prob else "ash"

        record = volcano_state.release(
            current_time_years,
            eruption_type,
            extra_info={
                "trigger_probability": trigger_prob,
                "trigger_draw": trigger_draw,
                "pdc_probability": pdc_prob,
                "pdc_draw": pdc_draw,
                "short_count": status["short_count"],
                "long_count": status["long_count"],
                "short_rate": status["short_rate"],
                "long_rate": status["long_rate"],
                "rate_ratio": status["rate_ratio"],
                "pressure_at_trigger": status["pressure"],
                "max_recent_mag": status["max_recent_mag"],
            },
        )

        self.last_eruption_time = float(current_time_years)
        self.last_eruption_type = eruption_type
        self.eruption_log.append(record)
        return record
