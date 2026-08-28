"""Location models for synthetic earthquake catalogues.

These models handle where earthquakes occur. They are designed to be paired with
an external earthquake-time simulator.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Sequence, Tuple

import numpy as np

MapBounds = Tuple[float, float, float, float]  # (x_min, x_max, y_min, y_max)


class LocationModel(ABC):
    """Base class for all location models.

    The public `sample_location` method enforces map bounds using rejection
    sampling. Subclasses only need to implement `_sample_location`.
    """

    def __init__(self, map_bounds: MapBounds):
        self.x_min, self.x_max, self.y_min, self.y_max = map_bounds
        if self.x_min >= self.x_max or self.y_min >= self.y_max:
            raise ValueError("Invalid map bounds: expected (x_min < x_max, y_min < y_max).")

    def _in_bounds(self, x: float, y: float) -> bool:
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max

    def sample_location(
        self,
        rng: np.random.Generator,
        event_type: str = "background",
        anchor: Optional[Tuple[float, float]] = None,
        parent: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, float]:
        """Return an in-bounds (x, y) location."""
        for _ in range(10_000):
            x, y = self._sample_location(rng=rng, event_type=event_type, anchor=anchor, parent=parent)
            if self._in_bounds(x, y):
                return float(x), float(y)
        raise RuntimeError("Could not sample a valid in-bounds location.")

    @abstractmethod
    def _sample_location(
        self,
        rng: np.random.Generator,
        event_type: str = "background",
        anchor: Optional[Tuple[float, float]] = None,
        parent: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, float]:
        raise NotImplementedError


class RandomLocationModel(LocationModel):
    """Uniform random locations inside the map."""

    def _sample_location(
        self,
        rng: np.random.Generator,
        event_type: str = "background",
        anchor: Optional[Tuple[float, float]] = None,
        parent: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, float]:
        x = rng.uniform(self.x_min, self.x_max)
        y = rng.uniform(self.y_min, self.y_max)
        return float(x), float(y)


class VentCentredLocationModel(LocationModel):
    """Locations clustered around a vent or anchor point."""

    def __init__(self, map_bounds: MapBounds, vent_x: float, vent_y: float, radial_scale: float = 5.0):
        super().__init__(map_bounds)
        self.vent_x = float(vent_x)
        self.vent_y = float(vent_y)
        self.radial_scale = float(radial_scale)

    def _sample_location(
        self,
        rng: np.random.Generator,
        event_type: str = "background",
        anchor: Optional[Tuple[float, float]] = None,
        parent: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, float]:
        cx, cy = anchor if anchor is not None else (self.vent_x, self.vent_y)
        u = max(rng.uniform(), 1e-12)
        theta = rng.uniform(0.0, 2.0 * np.pi)
        r = -self.radial_scale * np.log(u)
        x = cx + r * np.cos(theta)
        y = cy + r * np.sin(theta)
        return float(x), float(y)


class FaultLocationModel(LocationModel):
    """Sample earthquakes along one of several fault segments.

    Each segment is defined as (x1, y1, x2, y2, weight).
    """

    def __init__(
        self,
        map_bounds: MapBounds,
        segments: Sequence[Tuple[float, float, float, float, float]],
        perpendicular_sigma: float = 1.0,
    ):
        super().__init__(map_bounds)
        if len(segments) == 0:
            raise ValueError("FaultLocationModel requires at least one segment.")
        self.segments = [(float(x1), float(y1), float(x2), float(y2), float(w)) for x1, y1, x2, y2, w in segments]
        self.perpendicular_sigma = float(perpendicular_sigma)

    def _sample_location(
        self,
        rng: np.random.Generator,
        event_type: str = "background",
        anchor: Optional[Tuple[float, float]] = None,
        parent: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, float]:
        weights = np.array([max(seg[4], 0.0) for seg in self.segments], dtype=float)
        if weights.sum() == 0:
            weights[:] = 1.0
        weights /= weights.sum()

        idx = rng.choice(len(self.segments), p=weights)
        x1, y1, x2, y2, _ = self.segments[idx]

        s = rng.uniform(0.0, 1.0)
        x = x1 + s * (x2 - x1)
        y = y1 + s * (y2 - y1)

        dx = x2 - x1
        dy = y2 - y1
        length = np.hypot(dx, dy)
        if length > 0:
            ux = -dy / length
            uy = dx / length
            offset = rng.normal(0.0, self.perpendicular_sigma)
            x += offset * ux
            y += offset * uy

        return float(x), float(y)


class VolcanicSwarmLocationModel(LocationModel):
    """Mixture model for volcanic swarms.

    Supports points clustered around the vent, the magma chamber, the edifice,
    or a fault system. The chosen source is then sampled and clipped by the
    base rejection sampler to remain within map bounds.
    """

    def __init__(
        self,
        map_bounds: MapBounds,
        vent_x: float,
        vent_y: float,
        chamber_x: float,
        chamber_y: float,
        vent_weight: float = 0.4,
        chamber_weight: float = 0.3,
        edifice_weight: float = 0.2,
        fault_weight: float = 0.1,
        vent_scale: float = 1.0,
        chamber_scale: float = 2.0,
        edifice_scale: float = 4.0,
        fault_segments: Optional[Sequence[Tuple[float, float, float, float, float]]] = None,
        fault_perpendicular_sigma: float = 1.0,
    ):
        super().__init__(map_bounds)
        self.vent_x = float(vent_x)
        self.vent_y = float(vent_y)
        self.chamber_x = float(chamber_x)
        self.chamber_y = float(chamber_y)

        self.vent_weight = float(vent_weight)
        self.chamber_weight = float(chamber_weight)
        self.edifice_weight = float(edifice_weight)
        self.fault_weight = float(fault_weight)

        self.vent_scale = float(vent_scale)
        self.chamber_scale = float(chamber_scale)
        self.edifice_scale = float(edifice_scale)

        self.fault_model = None
        if fault_segments is not None and len(fault_segments) > 0:
            self.fault_model = FaultLocationModel(
                map_bounds=map_bounds,
                segments=fault_segments,
                perpendicular_sigma=fault_perpendicular_sigma,
            )

    @staticmethod
    def _sample_around_point(rng: np.random.Generator, cx: float, cy: float, scale: float) -> Tuple[float, float]:
        u = max(rng.uniform(), 1e-12)
        theta = rng.uniform(0.0, 2.0 * np.pi)
        r = -scale * np.log(u)
        x = cx + r * np.cos(theta)
        y = cy + r * np.sin(theta)
        return float(x), float(y)

    def _sample_location(
        self,
        rng: np.random.Generator,
        event_type: str = "background",
        anchor: Optional[Tuple[float, float]] = None,
        parent: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, float]:
        weights = np.array(
            [self.vent_weight, self.chamber_weight, self.edifice_weight, self.fault_weight],
            dtype=float,
        )
        if weights.sum() == 0:
            weights[:] = 1.0
        weights /= weights.sum()

        source = rng.choice(["vent", "chamber", "edifice", "fault"], p=weights)

        if anchor is not None:
            ax, ay = anchor
        elif parent is not None and "x" in parent and "y" in parent:
            ax, ay = float(parent["x"]), float(parent["y"])
        else:
            ax, ay = self.vent_x, self.vent_y

        if source == "vent":
            return self._sample_around_point(rng, ax, ay, self.vent_scale)
        if source == "chamber":
            return self._sample_around_point(rng, self.chamber_x, self.chamber_y, self.chamber_scale)
        if source == "edifice":
            return self._sample_around_point(rng, ax, ay, self.edifice_scale)

        if self.fault_model is not None:
            return self.fault_model._sample_location(rng, event_type=event_type, anchor=anchor, parent=parent)

        return self._sample_around_point(rng, ax, ay, self.edifice_scale)
