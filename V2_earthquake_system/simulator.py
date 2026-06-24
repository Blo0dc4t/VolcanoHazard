"""Earthquake occurrence simulator.

This module handles:
- non-homogeneous Poisson background occurrence,
- magnitude sampling,
- seismic moment conversion,
- optional aftershock generation,
- eruption-state detection,
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
        short_window_days: float = 30.0,
        long_window_days: float = 90.0,
        rate_ratio_threshold: float = 3.0,
        min_short_count: int = 20,
        ash_mag_threshold: float = 4.5,
        pdc_mag_threshold: float = 5.0,
        eruption_cooldown_days: float = 14.0,
    ):
        self.lambda0 = float(lambda0)
        self.k = float(k)
        self.m_min = float(m_min)
        self.m_max = float(m_max)
        self.b = float(b)
        self.duration_years = float(duration_years)
        self.seed = seed
        self.location_model = location_model

        self.short_window_days = float(short_window_days)
        self.long_window_days = float(long_window_days)
        self.rate_ratio_threshold = float(rate_ratio_threshold)
        self.min_short_count = int(min_short_count)
        self.ash_mag_threshold = float(ash_mag_threshold)
        self.pdc_mag_threshold = float(pdc_mag_threshold)
        self.eruption_cooldown_days = float(eruption_cooldown_days)

        if self.short_window_days <= 0 or self.long_window_days <= 0:
            raise ValueError("Window lengths must be positive.")
        if self.long_window_days < self.short_window_days:
            raise ValueError("long_window_days should be >= short_window_days.")
        if self.eruption_cooldown_days < 0:
            raise ValueError("eruption_cooldown_days must be non-negative.")

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

        self.last_eruption_time = -np.inf
        self.last_eruption_type: Optional[str] = None
        self.eruption_log: List[Dict[str, Any]] = []

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

    def _recent_events(self, window_days: float) -> List[Dict[str, Any]]:
        window_years = float(window_days) / 365.0
        return [
            e
            for e in self.events
            if 0.0 <= self.current_time - float(e["time_years"]) <= window_years
        ]

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

    # ----------------------------
    # Eruption logic
    # ----------------------------

    def volcano_status(self) -> Dict[str, Any]:
        short_events = self._recent_events(self.short_window_days)
        long_events = self._recent_events(self.long_window_days)

        short_count = len(short_events)
        long_count = len(long_events)

        short_rate = short_count / (self.short_window_days / 365.0)
        long_rate = long_count / (self.long_window_days / 365.0)

        recent_magnitudes = [float(e["magnitude"]) for e in short_events]
        max_recent_mag = max(recent_magnitudes) if recent_magnitudes else 0.0
        mean_recent_mag = float(np.mean(recent_magnitudes)) if recent_magnitudes else 0.0

        rate_ratio = short_rate / max(long_rate, 1e-12)

        cooldown_years = self.eruption_cooldown_days / 365.0
        cooldown_active = (self.current_time - self.last_eruption_time) < cooldown_years

        return {
            "current_time_years": float(self.current_time),
            "short_window_days": float(self.short_window_days),
            "long_window_days": float(self.long_window_days),
            "short_count": int(short_count),
            "long_count": int(long_count),
            "short_rate": float(short_rate),
            "long_rate": float(long_rate),
            "rate_ratio": float(rate_ratio),
            "max_recent_mag": float(max_recent_mag),
            "mean_recent_mag": float(mean_recent_mag),
            "cooldown_active": bool(cooldown_active),
            "last_eruption_time_years": None if not np.isfinite(self.last_eruption_time) else float(self.last_eruption_time),
            "last_eruption_type": self.last_eruption_type,
        }

    def check_for_eruption(self) -> Optional[Dict[str, Any]]:
        """
        Check whether recent seismicity is high enough to trigger an eruption.

        Returns a dict describing the eruption if one is triggered, otherwise None.
        """
        status = self.volcano_status()

        if status["cooldown_active"]:
            return None
        if status["short_count"] < self.min_short_count:
            return None
        if status["rate_ratio"] < self.rate_ratio_threshold:
            return None

        max_mag = status["max_recent_mag"]
        if max_mag >= self.pdc_mag_threshold:
            eruption_type = "ash_and_pdc"
        elif max_mag >= self.ash_mag_threshold:
            eruption_type = "ash"
        else:
            return None

        record = {
            "eruption_type": eruption_type,
            "time_years": float(self.current_time),
            "short_count": status["short_count"],
            "long_count": status["long_count"],
            "rate_ratio": status["rate_ratio"],
            "max_recent_mag": status["max_recent_mag"],
            "mean_recent_mag": status["mean_recent_mag"],
        }

        self.last_eruption_time = float(self.current_time)
        self.last_eruption_type = eruption_type
        self.eruption_log.append(record)
        return record

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
            "eruption_count": int(len(self.eruption_log)),
            "last_eruption_type": self.last_eruption_type,
            "last_eruption_time_years": None if not np.isfinite(self.last_eruption_time) else float(self.last_eruption_time),
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
            "short_window_days": self.short_window_days,
            "long_window_days": self.long_window_days,
            "rate_ratio_threshold": self.rate_ratio_threshold,
            "min_short_count": self.min_short_count,
            "ash_mag_threshold": self.ash_mag_threshold,
            "pdc_mag_threshold": self.pdc_mag_threshold,
            "eruption_cooldown_days": self.eruption_cooldown_days,
            "current_time": self.current_time,
            "background_event_count": self.background_event_count,
            "aftershock_event_count": self.aftershock_event_count,
            "total_seismic_moment_Nm": self.total_seismic_moment_Nm,
            "last_eruption_time": self.last_eruption_time,
            "last_eruption_type": self.last_eruption_type,
            "eruption_log": self.eruption_log,
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

        self.short_window_days = float(state["short_window_days"])
        self.long_window_days = float(state["long_window_days"])
        self.rate_ratio_threshold = float(state["rate_ratio_threshold"])
        self.min_short_count = int(state["min_short_count"])
        self.ash_mag_threshold = float(state["ash_mag_threshold"])
        self.pdc_mag_threshold = float(state["pdc_mag_threshold"])
        self.eruption_cooldown_days = float(state["eruption_cooldown_days"])

        self.current_time = float(state["current_time"])
        self.background_event_count = int(state["background_event_count"])
        self.aftershock_event_count = int(state["aftershock_event_count"])
        self.total_seismic_moment_Nm = float(state["total_seismic_moment_Nm"])
        self.last_eruption_time = float(state["last_eruption_time"])
        self.last_eruption_type = state["last_eruption_type"]
        self.eruption_log = list(state["eruption_log"])
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