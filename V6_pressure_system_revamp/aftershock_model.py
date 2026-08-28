"""Aftershock sequence generator.

This module applies:
- the productivity law for the number of aftershocks,
- Omori's law for the timing,
- Gutenberg-Richter sampling for the magnitudes,
- Båth's law as an upper magnitude guide,
- parent-centred spatial clustering.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

from simulator import EarthquakeSimulator


@dataclass
class AftershockModel:
    trigger_magnitude: float = 4.0
    productivity: float = 3.0
    alpha: float = 0.8
    reference_magnitude: float = 4.0
    p: float = 1.1
    c_days: float = 0.1
    duration_days: float = 14.0
    bath_offset: float = 1.2
    bath_offset_std: float = 0.2
    radius_scale: float = 1.0
    radius_exponent: float = 0.5
    min_aftershock_magnitude: Optional[float] = None

    generated_count: int = 0
    generation_log: list[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.trigger_magnitude <= 0:
            raise ValueError("trigger_magnitude must be positive.")
        if self.productivity <= 0:
            raise ValueError("productivity must be positive.")
        if self.duration_days <= 0:
            raise ValueError("duration_days must be positive.")
        if self.c_days <= 0:
            raise ValueError("c_days must be positive.")
        if self.bath_offset < 0:
            raise ValueError("bath_offset must be non-negative.")
        if self.bath_offset_std < 0:
            raise ValueError("bath_offset_std must be non-negative.")
        if self.radius_scale <= 0:
            raise ValueError("radius_scale must be positive.")
        if self.radius_exponent < 0:
            raise ValueError("radius_exponent must be non-negative.")

    def should_trigger(self, mainshock_magnitude: float) -> bool:
        return float(mainshock_magnitude) >= self.trigger_magnitude

    def _sample_omori_times(self, rng: np.random.Generator, n_after: int) -> np.ndarray:
        T = float(self.duration_days) / 365.0
        c = float(self.c_days) / 365.0
        u = rng.uniform(size=n_after)

        if abs(self.p - 1.0) < 1e-12:
            rel_times = c * (np.exp(u * np.log((c + T) / c)) - 1.0)
        else:
            a = c ** (1.0 - self.p)
            b = (c + T) ** (1.0 - self.p)
            rel_times = (u * (b - a) + a) ** (1.0 / (1.0 - self.p)) - c

        return np.clip(rel_times, 0.0, T)

    def _sample_location(
        self,
        rng: np.random.Generator,
        simulator: EarthquakeSimulator,
        mainshock_event: Dict[str, Any],
        mainshock_location: Optional[Tuple[float, float]],
    ) -> Tuple[float, float]:
        parent_x, parent_y = mainshock_location if mainshock_location is not None else (
            float(mainshock_event.get("x", 0.0)),
            float(mainshock_event.get("y", 0.0)),
        )
        parent_mag = float(mainshock_event.get("magnitude", self.reference_magnitude))
        mean_radius = self.radius_scale * (10 ** (self.radius_exponent * (parent_mag - 3.0)))

        bounds = None
        if simulator.location_model is not None:
            loc = simulator.location_model
            if all(hasattr(loc, attr) for attr in ("x_min", "x_max", "y_min", "y_max")):
                bounds = (float(loc.x_min), float(loc.x_max), float(loc.y_min), float(loc.y_max))

        for _ in range(1000):
            r = rng.exponential(scale=mean_radius)
            theta = rng.uniform(0.0, 2.0 * math.pi)
            x = parent_x + r * math.cos(theta)
            y = parent_y + r * math.sin(theta)
            if bounds is None:
                return float(x), float(y)
            x_min, x_max, y_min, y_max = bounds
            if x_min <= x <= x_max and y_min <= y <= y_max:
                return float(x), float(y)
        return float(parent_x), float(parent_y)

    def generate(
        self,
        simulator: EarthquakeSimulator,
        mainshock_event: Dict[str, Any],
        mainshock_location: Optional[Tuple[float, float]] = None,
        record: bool = True,
    ) -> List[Dict[str, Any]]:
        """Generate an aftershock sequence for a single qualifying mainshock."""
        mainshock_magnitude = float(mainshock_event["magnitude"])
        if not self.should_trigger(mainshock_magnitude):
            return []

        expected_count = self.productivity * (10 ** (self.alpha * (mainshock_magnitude - self.reference_magnitude)))
        n_after = simulator.rng.poisson(expected_count)
        if n_after == 0:
            return []

        rel_times = self._sample_omori_times(simulator.rng, n_after)
        abs_times = np.sort(float(mainshock_event["time_years"]) + rel_times)

        bath_noise = simulator.rng.normal(0.0, self.bath_offset_std) if self.bath_offset_std > 0 else 0.0
        bath_gap = max(0.0, self.bath_offset + bath_noise)
        max_aftershock_mag = min(simulator.m_max, mainshock_magnitude - bath_gap)
        min_aftershock_mag = self.min_aftershock_magnitude if self.min_aftershock_magnitude is not None else simulator.m_min
        if max_aftershock_mag <= min_aftershock_mag:
            return []

        events: List[Dict[str, Any]] = []
        for t in abs_times:
            mw = simulator.sample_magnitude(m_min=min_aftershock_mag, m_max=max_aftershock_mag)
            x, y = self._sample_location(simulator.rng, simulator, mainshock_event, mainshock_location)
            event = {
                "type": "aftershock",
                "time_years": float(t),
                "month": min(int(np.floor(float(t) * 12.0)) + 1, 12),
                "magnitude": float(mw),
                "seismic_moment_Nm": float(simulator.magnitude_to_seismic_moment(mw)),
                "x": float(x),
                "y": float(y),
                "parent_time_years": float(mainshock_event["time_years"]),
                "parent_magnitude": mainshock_magnitude,
            }
            events.append(event)

        if record:
            simulator.events.extend(events)
            simulator.aftershock_event_count += len(events)
            simulator.total_seismic_moment_Nm += sum(e["seismic_moment_Nm"] for e in events)

        self.generated_count += len(events)
        self.generation_log.append(
            {
                "mainshock_time_years": float(mainshock_event["time_years"]),
                "mainshock_magnitude": mainshock_magnitude,
                "count": len(events),
            }
        )
        return events

    def generate_for_catalogue(
        self,
        events: Iterable[Dict[str, Any]],
        simulator: EarthquakeSimulator,
        record: bool = True,
    ) -> List[Dict[str, Any]]:
        """Generate aftershocks for each qualifying background event in a catalogue."""
        aftershocks: List[Dict[str, Any]] = []
        for event in events:
            if event.get("type") != "background":
                continue
            if not self.should_trigger(float(event.get("magnitude", 0.0))):
                continue
            generated = self.generate(simulator=simulator, mainshock_event=event, mainshock_location=(event.get("x", 0.0), event.get("y", 0.0)), record=record)
            aftershocks.extend(generated)
        return aftershocks
