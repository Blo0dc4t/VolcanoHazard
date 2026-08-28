"""Aftershock sequence model.

This module handles:
- productivity law for aftershock counts,
- Omori-style decay for aftershock timing,
- Gutenberg-Richter sampling for aftershock magnitudes,
- Bath's law magnitude cap,
- parent-centred aftershock locations,
- trigger threshold for deciding whether a mainshock spawns aftershocks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class AftershockModel:
    productivity: float = 3.0
    alpha: float = 0.8
    reference_magnitude: float = 4.0
    trigger_magnitude: float = 4.0
    p: float = 1.1
    c_days: float = 0.1
    duration_days: float = 14.0
    bath_offset: float = 1.2
    bath_offset_std: float = 0.2
    radius_scale: float = 1.0
    radius_exponent: float = 0.5
    radius_reference_magnitude: float = 3.0

    def __post_init__(self) -> None:
        if self.productivity < 0:
            raise ValueError('productivity must be non-negative.')
        if self.duration_days <= 0:
            raise ValueError('duration_days must be positive.')
        if self.c_days < 0:
            raise ValueError('c_days must be non-negative.')
        if self.bath_offset < 0:
            raise ValueError('bath_offset must be non-negative.')
        if self.bath_offset_std < 0:
            raise ValueError('bath_offset_std must be non-negative.')
        if self.radius_scale <= 0:
            raise ValueError('radius_scale must be positive.')
        if self.trigger_magnitude < 0:
            raise ValueError('trigger_magnitude must be non-negative.')

    @staticmethod
    def _map_bounds(simulator) -> Optional[Tuple[float, float, float, float]]:
        loc = getattr(simulator, 'location_model', None)
        if loc is None:
            return None
        if all(hasattr(loc, attr) for attr in ('x_min', 'x_max', 'y_min', 'y_max')):
            return (float(loc.x_min), float(loc.x_max), float(loc.y_min), float(loc.y_max))
        return None

    def _sample_location_around_parent(
        self,
        rng: np.random.Generator,
        parent_location: Tuple[float, float],
        parent_magnitude: float,
        simulator,
    ) -> Tuple[float, float]:
        x0, y0 = float(parent_location[0]), float(parent_location[1])
        scale = self.radius_scale * (10 ** (self.radius_exponent * (float(parent_magnitude) - self.radius_reference_magnitude)))
        scale = max(scale, 1e-6)

        bounds = self._map_bounds(simulator)
        for _ in range(1000):
            u = max(rng.uniform(), 1e-12)
            theta = rng.uniform(0.0, 2.0 * np.pi)
            r = -scale * np.log(u)
            x = x0 + r * np.cos(theta)
            y = y0 + r * np.sin(theta)

            if bounds is None:
                return float(x), float(y)

            x_min, x_max, y_min, y_max = bounds
            if x_min <= x <= x_max and y_min <= y <= y_max:
                return float(x), float(y)

        if bounds is not None:
            x_min, x_max, y_min, y_max = bounds
            return float(np.clip(x0, x_min, x_max)), float(np.clip(y0, y_min, y_max))

        return float(x0), float(y0)

    def should_trigger(self, mainshock_event: Dict[str, Any]) -> bool:
        """Return True if the mainshock is large enough to trigger aftershocks."""
        return float(mainshock_event['magnitude']) >= self.trigger_magnitude

    def generate(
        self,
        simulator,
        mainshock_event: Dict[str, Any],
        mainshock_location: Optional[Tuple[float, float]] = None,
        duration_days: Optional[float] = None,
        c_days: Optional[float] = None,
        p: Optional[float] = None,
        productivity: Optional[float] = None,
        alpha: Optional[float] = None,
        aftershock_m_min: Optional[float] = None,
        aftershock_m_max: Optional[float] = None,
        bath_offset: Optional[float] = None,
        bath_offset_std: Optional[float] = None,
        radius_scale: Optional[float] = None,
        radius_exponent: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Generate an aftershock sequence for one mainshock event."""
        rng = simulator.rng

        mainshock_time_years = float(mainshock_event['time_years'])
        mainshock_magnitude = float(mainshock_event['magnitude'])

        if not self.should_trigger(mainshock_event):
            return []

        if mainshock_location is None and 'x' in mainshock_event and 'y' in mainshock_event:
            mainshock_location = (float(mainshock_event['x']), float(mainshock_event['y']))

        duration_days = self.duration_days if duration_days is None else float(duration_days)
        c_days = self.c_days if c_days is None else float(c_days)
        p = self.p if p is None else float(p)
        productivity = self.productivity if productivity is None else float(productivity)
        alpha = self.alpha if alpha is None else float(alpha)
        bath_offset = self.bath_offset if bath_offset is None else float(bath_offset)
        bath_offset_std = self.bath_offset_std if bath_offset_std is None else float(bath_offset_std)
        radius_scale = self.radius_scale if radius_scale is None else float(radius_scale)
        radius_exponent = self.radius_exponent if radius_exponent is None else float(radius_exponent)

        aftershock_m_min = simulator.m_min if aftershock_m_min is None else float(aftershock_m_min)
        aftershock_m_min = max(aftershock_m_min, simulator.m_min)

        offset = bath_offset
        if bath_offset_std > 0:
            offset = max(0.0, bath_offset + rng.normal(0.0, bath_offset_std))

        aftershock_m_max = min(simulator.m_max, mainshock_magnitude - offset)
        if aftershock_m_max <= aftershock_m_min:
            return []

        T = float(duration_days) / 365.0
        c = float(c_days) / 365.0
        if T <= 0:
            return []

        expected_count = productivity * (10 ** (alpha * (mainshock_magnitude - self.reference_magnitude)))
        n_after = rng.poisson(expected_count)
        if n_after == 0:
            return []

        u = rng.uniform(size=n_after)
        if abs(p - 1.0) < 1e-12:
            rel_times = c * (np.exp(u * np.log((c + T) / c)) - 1.0)
        else:
            a = c ** (1.0 - p)
            b = (c + T) ** (1.0 - p)
            rel_times = (u * (b - a) + a) ** (1.0 / (1.0 - p)) - c

        rel_times = np.clip(rel_times, 0.0, T)
        abs_times = np.sort(mainshock_time_years + rel_times)

        events: List[Dict[str, Any]] = []
        parent = None
        if mainshock_location is not None:
            parent = {
                'x': float(mainshock_location[0]),
                'y': float(mainshock_location[1]),
                'magnitude': mainshock_magnitude,
                'time_years': mainshock_time_years,
            }

        for t in abs_times:
            mw = simulator.sample_magnitude(m_min=aftershock_m_min, m_max=aftershock_m_max)
            event: Dict[str, Any] = {
                'type': 'aftershock',
                'time_years': float(t),
                'month': min(int(np.floor(t * 12.0)) + 1, 12),
                'magnitude': float(mw),
                'seismic_moment_Nm': float(simulator.magnitude_to_seismic_moment(mw)),
            }

            if mainshock_location is not None:
                x, y = self._sample_location_around_parent(
                    rng=rng,
                    parent_location=mainshock_location,
                    parent_magnitude=mainshock_magnitude,
                    simulator=simulator,
                )
                event['x'] = float(x)
                event['y'] = float(y)

            if parent is not None:
                event['parent_time_years'] = parent['time_years']
                event['parent_magnitude'] = parent['magnitude']

            events.append(event)

        return events
