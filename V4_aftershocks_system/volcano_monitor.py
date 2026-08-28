
"""Volcano eruption monitor.

This module watches the event catalogue produced by EarthquakeSimulator and
classifies the current state of volcanic unrest.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class VolcanoMonitor:
    short_window_days: float = 30.0
    long_window_days: float = 90.0
    rate_ratio_threshold: float = 3.0
    min_short_count: int = 20
    ash_mag_threshold: float = 4.5
    pdc_mag_threshold: float = 5.0
    eruption_cooldown_days: float = 14.0

    last_eruption_time: float = -np.inf
    last_eruption_type: Optional[str] = None
    eruption_log: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.short_window_days <= 0 or self.long_window_days <= 0:
            raise ValueError('Window lengths must be positive.')
        if self.long_window_days < self.short_window_days:
            raise ValueError('long_window_days should be >= short_window_days.')
        if self.eruption_cooldown_days < 0:
            raise ValueError('eruption_cooldown_days must be non-negative.')
        self.short_window_days = float(self.short_window_days)
        self.long_window_days = float(self.long_window_days)
        self.rate_ratio_threshold = float(self.rate_ratio_threshold)
        self.min_short_count = int(self.min_short_count)
        self.ash_mag_threshold = float(self.ash_mag_threshold)
        self.pdc_mag_threshold = float(self.pdc_mag_threshold)
        self.eruption_cooldown_days = float(self.eruption_cooldown_days)

    def _recent_events(self, events: List[Dict[str, Any]], current_time_years: float, window_days: float) -> List[Dict[str, Any]]:
        window_years = float(window_days) / 365.0
        return [
            e
            for e in events
            if 0.0 <= float(current_time_years) - float(e['time_years']) <= window_years
        ]

    def status(self, events: List[Dict[str, Any]], current_time_years: float) -> Dict[str, Any]:
        short_events = self._recent_events(events, current_time_years, self.short_window_days)
        long_events = self._recent_events(events, current_time_years, self.long_window_days)

        short_count = len(short_events)
        long_count = len(long_events)

        short_rate = short_count / (self.short_window_days / 365.0)
        long_rate = long_count / (self.long_window_days / 365.0)
        rate_ratio = short_rate / max(long_rate, 1e-12)

        recent_magnitudes = [float(e['magnitude']) for e in short_events]
        max_recent_mag = max(recent_magnitudes) if recent_magnitudes else 0.0
        mean_recent_mag = float(np.mean(recent_magnitudes)) if recent_magnitudes else 0.0

        cooldown_years = self.eruption_cooldown_days / 365.0
        cooldown_active = (float(current_time_years) - self.last_eruption_time) < cooldown_years

        return {
            'current_time_years': float(current_time_years),
            'short_count': int(short_count),
            'long_count': int(long_count),
            'short_rate': float(short_rate),
            'long_rate': float(long_rate),
            'rate_ratio': float(rate_ratio),
            'max_recent_mag': float(max_recent_mag),
            'mean_recent_mag': float(mean_recent_mag),
            'cooldown_active': bool(cooldown_active),
            'last_eruption_time_years': None if not np.isfinite(self.last_eruption_time) else float(self.last_eruption_time),
            'last_eruption_type': self.last_eruption_type,
        }

    def check_for_eruption(self, events: List[Dict[str, Any]], current_time_years: float) -> Optional[Dict[str, Any]]:
        status = self.status(events, current_time_years)

        if status['cooldown_active']:
            return None
        if status['short_count'] < self.min_short_count:
            return None
        if status['rate_ratio'] < self.rate_ratio_threshold:
            return None

        max_mag = status['max_recent_mag']
        if max_mag >= self.pdc_mag_threshold:
            eruption_type = 'ash_and_pdc'
        elif max_mag >= self.ash_mag_threshold:
            eruption_type = 'ash'
        else:
            return None

        record = {
            'eruption_type': eruption_type,
            'time_years': float(current_time_years),
            'short_count': status['short_count'],
            'long_count': status['long_count'],
            'rate_ratio': status['rate_ratio'],
            'max_recent_mag': status['max_recent_mag'],
            'mean_recent_mag': status['mean_recent_mag'],
        }

        self.last_eruption_time = float(current_time_years)
        self.last_eruption_type = eruption_type
        self.eruption_log.append(record)
        return record
