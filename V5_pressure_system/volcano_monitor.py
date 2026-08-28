"""Volcano eruption monitor.

This module watches the volcanic pressure state and decides when an eruption
should be triggered.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import numpy as np

from volcano_state import VolcanoState


@dataclass
class VolcanoMonitor:
    pressure_ash_threshold: float = 2.0
    pressure_pdc_threshold: float = 3.5
    eruption_cooldown_days: float = 14.0

    last_eruption_time: float = -np.inf
    last_eruption_type: Optional[str] = None
    eruption_log: list[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.pressure_ash_threshold <= 0 or self.pressure_pdc_threshold <= 0:
            raise ValueError("Pressure thresholds must be positive.")
        if self.pressure_pdc_threshold < self.pressure_ash_threshold:
            raise ValueError("pressure_pdc_threshold should be >= pressure_ash_threshold.")
        if self.eruption_cooldown_days < 0:
            raise ValueError("eruption_cooldown_days must be non-negative.")
        self.pressure_ash_threshold = float(self.pressure_ash_threshold)
        self.pressure_pdc_threshold = float(self.pressure_pdc_threshold)
        self.eruption_cooldown_days = float(self.eruption_cooldown_days)

    def status(self, volcano_state: VolcanoState, current_time_years: float) -> Dict[str, Any]:
        pressure = volcano_state.current_pressure(current_time_years)
        cooldown_years = self.eruption_cooldown_days / 365.0
        cooldown_active = (float(current_time_years) - self.last_eruption_time) < cooldown_years

        return {
            "current_time_years": float(current_time_years),
            "pressure": float(pressure),
            "cooldown_active": bool(cooldown_active),
            "last_eruption_time_years": None if not np.isfinite(self.last_eruption_time) else float(self.last_eruption_time),
            "last_eruption_type": self.last_eruption_type,
        }

    def check_for_eruption(self, volcano_state: VolcanoState, current_time_years: float) -> Optional[Dict[str, Any]]:
        status = self.status(volcano_state, current_time_years)
        if status["cooldown_active"]:
            return None

        pressure = status["pressure"]
        if pressure >= self.pressure_pdc_threshold:
            eruption_type = "ash_and_pdc"
        elif pressure >= self.pressure_ash_threshold:
            eruption_type = "ash"
        else:
            return None

        record = volcano_state.release(current_time_years, eruption_type, extra_info={
            "pressure_at_trigger": pressure,
        })
        self.last_eruption_time = float(current_time_years)
        self.last_eruption_type = eruption_type
        self.eruption_log.append(record)
        return record
