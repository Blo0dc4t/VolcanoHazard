"""Volcano pressure state.

Pressure increases exponentially with time and is reduced after eruptions.
The earthquake simulator uses the pressure as a multiplier on the
background rate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import numpy as np


@dataclass
class VolcanoState:
    """Exponential pressure model for volcanic unrest.

    Pressure is dimensionless. The background earthquake rate is

        lambda(t) = lambda0 * P(t)

    with

        P(t) = P_ref * exp(g * (t - t_ref))

    where g is the exponential pressure growth rate in 1/years.
    """

    pressure_growth_rate: float = 1.0
    initial_pressure: float = 1.0
    ash_release_fraction: float = 0.75
    pdc_release_fraction: float = 0.45
    min_pressure: float = 0.1
    max_pressure: Optional[float] = None

    last_reference_time: float = 0.0
    last_reference_pressure: float = 1.0
    last_eruption_time: float = -np.inf
    last_eruption_type: Optional[str] = None
    eruption_log: list[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.pressure_growth_rate < 0:
            raise ValueError("pressure_growth_rate must be non-negative.")
        if self.initial_pressure <= 0:
            raise ValueError("initial_pressure must be positive.")
        if self.ash_release_fraction <= 0 or self.pdc_release_fraction <= 0:
            raise ValueError("Release fractions must be positive.")
        if self.ash_release_fraction >= 1 or self.pdc_release_fraction >= 1:
            raise ValueError("Release fractions should be less than 1.")
        if self.min_pressure <= 0:
            raise ValueError("min_pressure must be positive.")
        self.reset()

    @property
    def eruption_count(self) -> int:
        return len(self.eruption_log)

    def reset(self) -> None:
        self.last_reference_time = 0.0
        self.last_reference_pressure = float(self.initial_pressure)
        self.last_eruption_time = -np.inf
        self.last_eruption_type = None
        self.eruption_log = []

    def current_pressure(self, current_time_years: float) -> float:
        dt = float(current_time_years) - self.last_reference_time
        pressure = self.last_reference_pressure * math.exp(self.pressure_growth_rate * max(dt, 0.0))
        if self.max_pressure is not None:
            pressure = min(pressure, float(self.max_pressure))
        return max(self.min_pressure, float(pressure))

    def rate_multiplier(self, current_time_years: float) -> float:
        return self.current_pressure(current_time_years)

    def rate_parameters(self, base_lambda0: float) -> tuple[float, float]:
        """Return the coefficient a and growth rate g for lambda(t)=a*exp(g*t)."""
        g = float(self.pressure_growth_rate)
        a = float(base_lambda0) * self.last_reference_pressure * math.exp(-g * self.last_reference_time)
        return a, g

    def cumulative_multiplier(self, t0: float, t1: float) -> float:
        """Return integral of the pressure multiplier over [t0, t1]."""
        t0 = float(t0)
        t1 = float(t1)
        if t1 < t0:
            t0, t1 = t1, t0
        g = float(self.pressure_growth_rate)
        a = self.last_reference_pressure * math.exp(-g * self.last_reference_time)
        if g == 0.0:
            return a * (t1 - t0)
        return (a / g) * (math.exp(g * t1) - math.exp(g * t0))

    def cumulative_intensity(self, base_lambda0: float, t0: float, t1: float) -> float:
        return float(base_lambda0) * self.cumulative_multiplier(t0, t1)

    def release(self, current_time_years: float, eruption_type: str, extra_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Apply a pressure release at the given time and log it."""
        current_time_years = float(current_time_years)
        pressure_before = self.current_pressure(current_time_years)
        if eruption_type == "ash_and_pdc":
            factor = self.pdc_release_fraction
        else:
            factor = self.ash_release_fraction
        pressure_after = max(self.min_pressure, pressure_before * factor)
        self.last_reference_time = current_time_years
        self.last_reference_pressure = pressure_after
        self.last_eruption_time = current_time_years
        self.last_eruption_type = eruption_type

        record: Dict[str, Any] = {
            "eruption_type": eruption_type,
            "time_years": current_time_years,
            "pressure_before": pressure_before,
            "pressure_after": pressure_after,
            "pressure_drop": pressure_before - pressure_after,
            "release_fraction": factor,
        }
        if extra_info:
            record.update(extra_info)
        self.eruption_log.append(record)
        return record

    def serialize_state(self) -> Dict[str, Any]:
        return {
            "pressure_growth_rate": self.pressure_growth_rate,
            "initial_pressure": self.initial_pressure,
            "ash_release_fraction": self.ash_release_fraction,
            "pdc_release_fraction": self.pdc_release_fraction,
            "min_pressure": self.min_pressure,
            "max_pressure": self.max_pressure,
            "last_reference_time": self.last_reference_time,
            "last_reference_pressure": self.last_reference_pressure,
            "last_eruption_time": self.last_eruption_time,
            "last_eruption_type": self.last_eruption_type,
            "eruption_log": self.eruption_log,
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        self.pressure_growth_rate = float(state["pressure_growth_rate"])
        self.initial_pressure = float(state["initial_pressure"])
        self.ash_release_fraction = float(state["ash_release_fraction"])
        self.pdc_release_fraction = float(state["pdc_release_fraction"])
        self.min_pressure = float(state["min_pressure"])
        self.max_pressure = state.get("max_pressure", None)
        self.last_reference_time = float(state["last_reference_time"])
        self.last_reference_pressure = float(state["last_reference_pressure"])
        self.last_eruption_time = float(state["last_eruption_time"])
        self.last_eruption_type = state["last_eruption_type"]
        self.eruption_log = list(state["eruption_log"])
