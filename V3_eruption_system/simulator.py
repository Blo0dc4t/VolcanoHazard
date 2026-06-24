"""Earthquake occurrence simulator.

This module handles:
- non-homogeneous Poisson background occurrence,
- magnitude sampling,
- seismic moment conversion,
- optional aftershock generation,
- state save/load,
- stepping through simulation time.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from location_models import LocationModel


class EarthquakeSimulator:
    """Earthquake generator for game/simulation use."""

    def __init__(
        self,
        lambda0: float = 2.0,
        k: float = 2.0,
        m_min: float = 3.0,
        m_max: float = 7.0,
        b: float = 1.0,
        duration_years: float = 1.0,
        seed: Optional[int] = None,
        location_model: Optional[LocationModel] = None,
    ):
        self.lambda0 = float(lambda0)
        self.k = float(k)
        self.m_min = float(m_min)
        self.m_max = float(m_max)
        self.b = float(b)
        self.duration_years = float(duration_years)
        self.seed = seed
        self.location_model = location_model
        self.rng = np.random.default_rng(seed)
        self.reset(seed=seed)

    # ----------------------------
    # Rate functions
    # ----------------------------

    def rate(self, t: float) -> float:
        return self.lambda0 * np.exp(self.k * t)

    def cumulative_intensity(self, t: float) -> float:
        t = float(t)
        if self.k == 0.0:
            return self.lambda0 * t
        return (self.lambda0 / self.k) * (np.exp(self.k * t) - 1.0)

    def inverse_cumulative_intensity(self, u: float) -> float:
        u = float(u)
        if self.k == 0.0:
            return u / self.lambda0
        return (1.0 / self.k) * np.log(1.0 + (self.k * u) / self.lambda0)

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

        expected = self.cumulative_intensity(t1) - self.cumulative_intensity(t0)
        n_events = self.rng.poisson(expected)

        if n_events == 0:
            self.current_time = t1
            return []

        u = self.rng.uniform(
            self.cumulative_intensity(t0),
            self.cumulative_intensity(t1),
            size=n_events,
        )
        times = np.sort([self.inverse_cumulative_intensity(ui) for ui in u])

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
        self.current_time = 0.0
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

        u0 = self.cumulative_intensity(self.current_time)
        u_next = u0 + e
        u_end = self.cumulative_intensity(self.duration_years)

        if u_next > u_end:
            return None
        return float(self.inverse_cumulative_intensity(u_next))

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
        }

    def serialize_state(self) -> Dict[str, Any]:
        return {
            "lambda0": self.lambda0,
            "k": self.k,
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
        }

    def load_state(self, state: Dict[str, Any]) -> None:
        self.lambda0 = float(state["lambda0"])
        self.k = float(state["k"])
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

    # ----------------------------
    # Aftershocks
    # ----------------------------

    def generate_aftershocks(
        self,
        mainshock_time_years: float,
        mainshock_magnitude: float,
        mainshock_location: Optional[Tuple[float, float]] = None,
        duration_days: float = 14.0,
        c_days: float = 0.1,
        p: float = 1.1,
        productivity: float = 3.0,
        alpha: float = 0.8,
        aftershock_m_min: Optional[float] = None,
        aftershock_m_max: Optional[float] = None,
        record: bool = True,
    ) -> List[Dict[str, Any]]:
        """Generate aftershocks using an Omori-like decay law."""
        mainshock_time_years = float(mainshock_time_years)
        mainshock_magnitude = float(mainshock_magnitude)

        aftershock_m_min = self.m_min if aftershock_m_min is None else float(aftershock_m_min)
        aftershock_m_max = self.m_max if aftershock_m_max is None else float(aftershock_m_max)

        T = float(duration_days) / 365.0
        c = float(c_days) / 365.0

        expected_count = productivity * (10 ** (alpha * (mainshock_magnitude - 4.0)))
        n_after = self.rng.poisson(expected_count)
        if n_after == 0:
            return []

        u = self.rng.uniform(size=n_after)
        if abs(p - 1.0) < 1e-12:
            rel_times = c * (np.exp(u * np.log((c + T) / c)) - 1.0)
        else:
            a = c ** (1.0 - p)
            b = (c + T) ** (1.0 - p)
            rel_times = (u * (b - a) + a) ** (1.0 / (1.0 - p)) - c

        rel_times = np.clip(rel_times, 0.0, T)
        abs_times = np.sort(mainshock_time_years + rel_times)

        parent = None
        if mainshock_location is not None:
            parent = {
                "x": float(mainshock_location[0]),
                "y": float(mainshock_location[1]),
                "magnitude": mainshock_magnitude,
                "time_years": mainshock_time_years,
            }

        events: List[Dict[str, Any]] = []
        for t in abs_times:
            mw = self.sample_magnitude(m_min=aftershock_m_min, m_max=aftershock_m_max)
            event = self._make_event(
                time_years=t,
                magnitude=mw,
                event_type="aftershock",
                anchor=mainshock_location,
                parent=parent,
            )
            if parent is not None:
                event["parent_time_years"] = mainshock_time_years
                event["parent_magnitude"] = mainshock_magnitude
            events.append(event)

        if record:
            self.events.extend(events)
            self.aftershock_event_count += len(events)
            self.total_seismic_moment_Nm += sum(e["seismic_moment_Nm"] for e in events)

        return events
