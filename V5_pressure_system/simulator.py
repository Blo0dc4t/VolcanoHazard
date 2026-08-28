"""Earthquake occurrence simulator.

This module handles:
- non-homogeneous Poisson background occurrence,
- magnitude sampling,
- seismic moment conversion,
- state save/load,
- stepping through simulation time.

The background rate is modulated by a separate VolcanoState object when
present. That state tracks an exponentially growing pressure variable that
can be reduced after eruptions.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from location_models import LocationModel
from volcano_state import VolcanoState


class EarthquakeSimulator:
    """Earthquake generator for game/simulation use."""

    def __init__(
        self,
        lambda0: float = 2.0,
        m_min: float = 3.0,
        m_max: float = 7.0,
        b: float = 1.0,
        duration_years: float = 1.0,
        seed: Optional[int] = None,
        location_model: Optional[LocationModel] = None,
        volcano_state: Optional[VolcanoState] = None,
    ):
        self.lambda0 = float(lambda0)
        self.m_min = float(m_min)
        self.m_max = float(m_max)
        self.b = float(b)
        self.duration_years = float(duration_years)
        self.seed = seed
        self.location_model = location_model
        self.volcano_state = volcano_state
        self.rng = np.random.default_rng(seed)
        self.reset(seed=seed)

    # ----------------------------
    # Rate functions
    # ----------------------------

    def _rate_parameters(self) -> tuple[float, float]:
        """Return the exponential intensity coefficient a and growth rate g.

        The background rate is written as:

            lambda(t) = a * exp(g * t)

        with t measured in years from the start of the current pressure
        regime. When no VolcanoState is attached, the rate is constant.
        """
        if self.volcano_state is None:
            return self.lambda0, 0.0
        return self.volcano_state.rate_parameters(self.lambda0)

    def rate(self, t: float) -> float:
        a, g = self._rate_parameters()
        if g == 0.0:
            return a
        return a * math.exp(g * float(t))

    def cumulative_intensity(self, t: float) -> float:
        a, g = self._rate_parameters()
        t = float(t)
        if g == 0.0:
            return a * t
        return (a / g) * (math.exp(g * t) - 1.0)

    def interval_intensity(self, t0: float, t1: float) -> float:
        t0 = float(t0)
        t1 = float(t1)
        a, g = self._rate_parameters()
        if g == 0.0:
            return a * (t1 - t0)
        return (a / g) * (math.exp(g * t1) - math.exp(g * t0))

    def inverse_cumulative_intensity(self, u: float) -> float:
        a, g = self._rate_parameters()
        u = float(u)
        if g == 0.0:
            return u / a
        return math.log1p(g * u / a) / g

    # ----------------------------
    # Magnitude and moment
    # ----------------------------

    def sample_magnitude(self, m_min: Optional[float] = None, m_max: Optional[float] = None) -> float:
        m_min = self.m_min if m_min is None else float(m_min)
        m_max = self.m_max if m_max is None else float(m_max)
        u = self.rng.uniform()
        tail = 10 ** (-self.b * (m_max - m_min))
        return m_min - (1.0 / self.b) * np.log10(1.0 - u * (1.0 - tail))

    @staticmethod
    def magnitude_to_seismic_moment(mw: float) -> float:
        return 10 ** (1.5 * float(mw) + 9.1)

    # ----------------------------
    # State helpers
    # ----------------------------

    def reset(self, seed: Optional[int] = None) -> None:
        if seed is not None:
            self.seed = seed
        self.rng = np.random.default_rng(self.seed)
        self.current_time = 0.0
        self.events: List[Dict[str, Any]] = []
        self.background_event_count = 0
        self.aftershock_event_count = 0
        self.total_seismic_moment_Nm = 0.0
        if self.volcano_state is not None:
            self.volcano_state.reset()

    def _make_event(
        self,
        time_years: float,
        magnitude: float,
        event_type: str = "background",
        anchor: Optional[Tuple[float, float]] = None,
        parent: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        time_years = float(time_years)
        magnitude = float(magnitude)
        month = min(int(np.floor(time_years * 12.0)) + 1, 12)

        event = {
            "type": event_type,
            "time_years": time_years,
            "month": month,
            "magnitude": magnitude,
            "seismic_moment_Nm": float(self.magnitude_to_seismic_moment(magnitude)),
        }

        if self.location_model is not None:
            x, y = self.location_model.sample_location(
                rng=self.rng,
                event_type=event_type,
                anchor=anchor,
                parent=parent,
            )
            event["x"] = float(x)
            event["y"] = float(y)

        return event

    # ----------------------------
    # Simulation methods
    # ----------------------------

    def step(self, dt: float) -> List[Dict[str, Any]]:
        """Advance by dt years and generate background earthquakes in that interval."""
        if dt <= 0:
            return []

        t0 = self.current_time
        t1 = min(self.current_time + float(dt), self.duration_years)

        if t0 >= self.duration_years:
            self.current_time = self.duration_years
            return []

        expected = self.interval_intensity(t0, t1)
        n_events = self.rng.poisson(expected)

        if n_events == 0:
            self.current_time = t1
            return []

        a, g = self._rate_parameters()
        I0 = self.cumulative_intensity(t0)
        I1 = self.cumulative_intensity(t1)
        u = self.rng.uniform(I0, I1, size=n_events)
        if g == 0.0:
            times = np.sort(u / a)
        else:
            times = np.sort(np.log1p(g * u / a) / g)

        generated: List[Dict[str, Any]] = []
        for t in times:
            mw = self.sample_magnitude()
            event = self._make_event(time_years=t, magnitude=mw, event_type="background")
            generated.append(event)

        self.events.extend(generated)
        self.background_event_count += len(generated)
        self.total_seismic_moment_Nm += sum(e["seismic_moment_Nm"] for e in generated)
        self.current_time = t1
        return generated

    def generate_until(self, t_end: float) -> List[Dict[str, Any]]:
        t_end = min(float(t_end), self.duration_years)
        if t_end <= self.current_time:
            return []
        return self.step(t_end - self.current_time)

    def generate_year(self) -> List[Dict[str, Any]]:
        self.reset(seed=self.seed)
        return self.generate_until(self.duration_years)

    def get_current_rate(self) -> float:
        return float(self.rate(self.current_time))

    def get_next_event_time(self) -> Optional[float]:
        """Peek at the next background event time without changing state."""
        if self.current_time >= self.duration_years:
            return None

        rng_copy = np.random.default_rng()
        rng_copy.bit_generator.state = copy.deepcopy(self.rng.bit_generator.state)
        e = rng_copy.exponential(scale=1.0)

        a, g = self._rate_parameters()
        if g == 0.0:
            u0 = a * self.current_time
            u_next = u0 + e
            if u_next > a * self.duration_years:
                return None
            return float(u_next / a)

        u0 = (a / g) * (math.exp(g * self.current_time) - 1.0)
        u_next = u0 + e
        u_end = (a / g) * (math.exp(g * self.duration_years) - 1.0)

        if u_next > u_end:
            return None
        return float(math.log1p(g * u_next / a) / g)

    def get_statistics(self) -> Dict[str, Any]:
        magnitudes = [e["magnitude"] for e in self.events]
        seismic_moments = [e["seismic_moment_Nm"] for e in self.events]

        return {
            "current_time_years": float(self.current_time),
            "duration_years": float(self.duration_years),
            "background_event_count": int(self.background_event_count),
            "aftershock_event_count": int(self.aftershock_event_count),
            "total_event_count": int(len(self.events)),
            "mean_magnitude": float(np.mean(magnitudes)) if magnitudes else None,
            "max_magnitude": float(np.max(magnitudes)) if magnitudes else None,
            "total_seismic_moment_Nm": float(np.sum(seismic_moments)) if seismic_moments else 0.0,
            "current_rate": float(self.get_current_rate()),
            "pressure": None if self.volcano_state is None else float(self.volcano_state.current_pressure(self.current_time)),
        }

    def serialize_state(self) -> Dict[str, Any]:
        return {
            "lambda0": self.lambda0,
            "m_min": self.m_min,
            "m_max": self.m_max,
            "b": self.b,
            "duration_years": self.duration_years,
            "seed": self.seed,
            "current_time": self.current_time,
            "background_event_count": self.background_event_count,
            "aftershock_event_count": self.aftershock_event_count,
            "total_seismic_moment_Nm": self.total_seismic_moment_Nm,
            "events": self.events,
            "rng_state": copy.deepcopy(self.rng.bit_generator.state),
            "volcano_state": None if self.volcano_state is None else self.volcano_state.serialize_state(),
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        self.lambda0 = float(state["lambda0"])
        self.m_min = float(state["m_min"])
        self.m_max = float(state["m_max"])
        self.b = float(state["b"])
        self.duration_years = float(state["duration_years"])
        self.seed = state.get("seed", None)

        self.current_time = float(state["current_time"])
        self.background_event_count = int(state["background_event_count"])
        self.aftershock_event_count = int(state["aftershock_event_count"])
        self.total_seismic_moment_Nm = float(state["total_seismic_moment_Nm"])
        self.events = list(state["events"])

        self.rng = np.random.default_rng()
        self.rng.bit_generator.state = copy.deepcopy(state["rng_state"])

        volcano_state_data = state.get("volcano_state")
        if self.volcano_state is not None and volcano_state_data is not None:
            self.volcano_state.load_state(volcano_state_data)
