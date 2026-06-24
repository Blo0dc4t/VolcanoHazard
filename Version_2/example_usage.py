"""Example usage for the earthquake simulation package."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from location_models import (
    FaultLocationModel,
    RandomLocationModel,
    VentCentredLocationModel,
    VolcanicSwarmLocationModel,
)
from simulator import EarthquakeSimulator


def run_demo(model_name: str, location_model):
    sim = EarthquakeSimulator(
        lambda0=2.0,
        k=2.0,
        m_min=3.0,
        m_max=7.0,
        b=1.0,
        seed=123,
        location_model=location_model,
    )

    all_events = []

    # Generate one year in monthly steps
    for _ in range(12):
        all_events.extend(sim.step(1.0 / 12.0))

    # Add aftershocks for the first background event, if one exists
    background_events = [e for e in all_events if e["type"] == "background"]
    if background_events:
        first_background = background_events[0]

        aftershocks = sim.generate_aftershocks(
            mainshock_time_years=first_background["time_years"],
            mainshock_magnitude=first_background["magnitude"],
            mainshock_location=(
                first_background.get("x", 0.0),
                first_background.get("y", 0.0),
            ),
            duration_days=10.0,
        )
        all_events.extend(aftershocks)

    return sim, all_events


def monthly_counts(events):
    counts = np.zeros(12, dtype=int)
    for month in range(1, 13):
        counts[month - 1] = sum(1 for e in events if e["month"] == month)
    return counts


def cumulative_magnitude_frequency(events, min_mag=3.0, max_mag=7.0, step=0.1):
    mags = np.array([e["magnitude"] for e in events])
    thresholds = np.arange(min_mag, max_mag + step, step)
    cumulative_counts = np.array([(mags >= thr).sum() for thr in thresholds])
    return thresholds, cumulative_counts


def plot_results(results, bounds):
    """
    Left panel:
        locations for the different models, with background / aftershock
        distinguished by symbol

    Middle panel:
        shared magnitude-frequency relationship

    Right panel:
        shared time-frequency relationship
    """

    colours = {
        "Random": "tab:blue",
        "Vent": "tab:red",
        "Fault": "tab:green",
        "Swarm": "tab:purple",
    }

    markers = {
        "background": "o",
        "aftershock": "x",
    }

    fig, (ax_map, ax_magfreq, ax_timefreq) = plt.subplots(
        1,
        3,
        figsize=(18, 6),
        constrained_layout=True,
    )

    # -------------------------------------------------
    # Left panel: location map for each model
    # -------------------------------------------------
    for model_name, (_, events) in results.items():
        colour = colours[model_name]

        for event_type in ("background", "aftershock"):
            type_events = [e for e in events if e["type"] == event_type]
            if not type_events:
                continue

            xs = [e["x"] for e in type_events if "x" in e]
            ys = [e["y"] for e in type_events if "y" in e]
            mags = [e["magnitude"] for e in type_events]
            sizes = [10 * (m ** 1.5) for m in mags]

            ax_map.scatter(
                xs,
                ys,
                s=sizes,
                alpha=0.75,
                color=colour,
                marker=markers[event_type],
            )

    ax_map.set_xlim(bounds[0], bounds[1])
    ax_map.set_ylim(bounds[2], bounds[3])
    ax_map.set_xlabel("X Position")
    ax_map.set_ylabel("Y Position")
    ax_map.set_title("Earthquake Locations by Model")

    # Two legends: one for colour, one for symbol
    model_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            markerfacecolor=colour,
            markersize=8,
            label=model_name,
        )
        for model_name, colour in colours.items()
    ]
    model_legend = ax_map.legend(
        handles=model_handles,
        title="Location Model",
        loc="upper left",
    )
    ax_map.add_artist(model_legend)

    symbol_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="black",
            linestyle="None",
            markersize=8,
            label="Background",
        ),
        Line2D(
            [0],
            [0],
            marker="x",
            color="black",
            linestyle="None",
            markersize=8,
            label="Aftershock",
        ),
    ]
    ax_map.legend(
        handles=symbol_handles,
        title="Event Type",
        loc="upper right",
    )

    # -------------------------------------------------
    # Shared catalogue for the other two panels
    # -------------------------------------------------
    # Only the spatial location changes between models. Use one representative
    # catalogue for the shared magnitude/time relationships.
    shared_events = next(iter(results.values()))[1]

    # -------------------------------------------------
    # Middle panel: magnitude-frequency
    # -------------------------------------------------
    thresholds, cumulative_counts = cumulative_magnitude_frequency(shared_events)

    ax_magfreq.scatter(
        thresholds,
        cumulative_counts,
        color="black",
    )
    ax_magfreq.set_yscale("log")
    ax_magfreq.set_xlabel("Magnitude (Mw)")
    ax_magfreq.set_ylabel("Cumulative number of events")
    ax_magfreq.set_title("Magnitude-Frequency Relationship")
    ax_magfreq.grid(True, which="both", linestyle=":", alpha=0.4)

    # -------------------------------------------------
    # Right panel: time-frequency
    # -------------------------------------------------
    counts = monthly_counts(shared_events)
    months = np.arange(1, 13)

    ax_timefreq.bar(months, counts, color="black", alpha=0.8)
    ax_timefreq.set_xlabel("Month")
    ax_timefreq.set_ylabel("Number of events")
    ax_timefreq.set_title("Time-Frequency Relationship")
    ax_timefreq.set_xticks(months)
    ax_timefreq.grid(True, axis="y", linestyle=":", alpha=0.4)

    return fig


if __name__ == "__main__":
    bounds = (0.0, 100.0, 0.0, 100.0)

    random_model = RandomLocationModel(bounds)

    vent_model = VentCentredLocationModel(
        bounds,
        vent_x=50.0,
        vent_y=50.0,
        radial_scale=6.0,
    )

    fault_model = FaultLocationModel(
        bounds,
        segments=[
            (10.0, 20.0, 85.0, 25.0, 1.0),
            (25.0, 60.0, 90.0, 90.0, 2.0),
        ],
        perpendicular_sigma=1.5,
    )

    swarm_model = VolcanicSwarmLocationModel(
        bounds,
        vent_x=50.0,
        vent_y=50.0,
        chamber_x=48.0,
        chamber_y=42.0,
        fault_segments=[
            (10.0, 20.0, 85.0, 25.0, 1.0),
        ],
    )

    results = {
        "Random": run_demo("Random", random_model),
        "Vent": run_demo("Vent", vent_model),
        "Fault": run_demo("Fault", fault_model),
        "Swarm": run_demo("Swarm", swarm_model),
    }

    plot_results(results, bounds)
    plt.show()