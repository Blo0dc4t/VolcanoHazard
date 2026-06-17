"""Volcano expansion: place a main volcano and select hazards with distance-weighted probabilities.

This module is an optional add-on for the base game. It exposes a small API:
- VolcanoExpansion(): create expansion with tunable weights
- place_volcano(island_mask) -> (col,row)
- choose_hazard(volcano_pos, island_mask, round_number) -> (spec_dict, epicenter)

The expansion returns hazard specs as plain dicts so the base game can
instantiate its own `Hazard` dataclass without creating a tight coupling.
"""

from __future__ import annotations

import math
import random
from typing import Tuple, List

R = random.Random()

# Base hazard catalog (this can be extended)
EXP_HAZARDS = [
    {"name": "Ashfall", "damage": 60, "pattern": "diamond", "spread": 1, "base": 1.0},
    {"name": "Lava Spur", "damage": 110, "pattern": "square", "spread": 1, "base": 0.9},
    {"name": "Bomb Shower", "damage": 140, "pattern": "cross", "spread": 2, "base": 0.8},
    {"name": "Pyroclastic Surge", "damage": 180, "pattern": "diamond", "spread": 2, "base": 0.7},
    {"name": "Mudflow", "damage": 120, "pattern": "line", "spread": 4, "base": 0.6},
    {"name": "Radius Blast", "damage": 220, "pattern": "square", "spread": 1, "base": 0.5},
]


class VolcanoExpansion:
    def __init__(self, rng_seed: int | None = None):
        self.rng = random.Random(rng_seed)
        self.volcano_pos: Tuple[int, int] | None = None

    def place_volcano(self, island_mask: List[List[bool]]) -> Tuple[int, int]:
        """Choose a sensible volcano cell from the land mask.

        Strategy: prefer central land cells, but pick randomly among candidates.
        """
        rows = len(island_mask)
        cols = len(island_mask[0]) if rows else 0
        center = ((cols - 1) / 2.0, (rows - 1) / 2.0)
        candidates = []
        for y in range(rows):
            for x in range(cols):
                if not island_mask[y][x]:
                    continue
                # distance penalty from center: prefer central standing land
                dx = (x - center[0])
                dy = (y - center[1])
                dist = math.hypot(dx, dy)
                candidates.append(((x, y), dist))

        if not candidates:
            raise RuntimeError("No land to place a volcano")

        # sort by distance and sample from the inner half more often
        candidates.sort(key=lambda t: t[1])
        cutoff = max(1, len(candidates) // 2)
        pool = [c[0] for c in candidates[:cutoff]] + [c[0] for c in candidates[cutoff:]]
        self.volcano_pos = self.rng.choice(pool)
        return self.volcano_pos

    def _distance_norm(self, a: Tuple[int, int], b: Tuple[int, int], island_mask: List[List[bool]]) -> float:
        rows = len(island_mask)
        cols = len(island_mask[0]) if rows else 0
        maxd = math.hypot(cols, rows)
        return min(1.0, math.hypot(a[0] - b[0], a[1] - b[1]) / (maxd or 1.0))

    def choose_hazard(
        self,
        volcano_pos: Tuple[int, int],
        island_mask: List[List[bool]],
        round_number: int = 1,
        weights: dict | None = None,
    ):
        """Select a hazard and an epicenter.

        If `weights` is provided it should map hazard name -> multiplier (float).
        Returns (hazard_spec_dict, epicenter, probs) where `probs` is a dict of hazard name -> probability.
        """
        rows = len(island_mask)
        cols = len(island_mask[0]) if rows else 0
        land_cells = [(x, y) for y in range(rows) for x in range(cols) if island_mask[y][x]]
        if not land_cells:
            raise RuntimeError("No land available for hazard epicenter")

        # precompute per-hazard per-cell weights
        hazard_cell_weights: dict[str, list[float]] = {}
        hazard_totals: dict[str, float] = {}
        for spec in EXP_HAZARDS:
            name = spec["name"]
            base = spec.get("base", 1.0)
            override = float(weights.get(name, 1.0)) if weights else 1.0
            cells_w: list[float] = []
            total = 0.0
            for c in land_cells:
                dnorm = self._distance_norm(volcano_pos, c, island_mask)
                # distance modifier per hazard name
                ln = name.lower()
                if ln.startswith("ash"):
                    modifier = 0.6 + 1.4 * dnorm
                elif "pyro" in ln or "radius" in ln:
                    modifier = 1.6 - 1.2 * dnorm
                elif "lava" in ln or "mud" in ln:
                    modifier = 1.4 - 0.9 * dnorm
                else:
                    modifier = 1.0
                round_boost = 1.0 + max(0.0, (round_number - 1)) * 0.03
                w = max(0.0, base * modifier * round_boost) * override
                cells_w.append(w)
                total += w
            hazard_cell_weights[name] = cells_w
            hazard_totals[name] = total

        # aggregate to hazard probabilities
        total_all = sum(hazard_totals.values())
        probs: dict[str, float] = {}
        if total_all <= 0:
            # fallback uniform
            for spec in EXP_HAZARDS:
                probs[spec["name"]] = 1.0 / len(EXP_HAZARDS)
        else:
            for name, t in hazard_totals.items():
                probs[name] = t / total_all

        # sample hazard (two-stage)
        hazard_names = list(hazard_totals.keys())
        hazard_weights = [hazard_totals[n] for n in hazard_names]
        if sum(hazard_weights) <= 0:
            chosen_name = self.rng.choice(hazard_names)
        else:
            chosen_name = self.rng.choices(hazard_names, weights=hazard_weights, k=1)[0]

        # sample epicenter for chosen hazard using per-cell weights
        chosen_cells = hazard_cell_weights[chosen_name]
        if sum(chosen_cells) <= 0:
            epicenter = self.rng.choice(land_cells)
        else:
            epicenter = self.rng.choices(land_cells, weights=chosen_cells, k=1)[0]

        # find spec dict
        for spec in EXP_HAZARDS:
            if spec["name"] == chosen_name:
                return spec, epicenter, probs
        return EXP_HAZARDS[-1], epicenter, probs
