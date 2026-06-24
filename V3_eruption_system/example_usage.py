"""Example usage for the earthquake simulation package."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from analysis import (
    cumulative_magnitude_frequency,
    expected_monthly_counts,
    fit_gr_line,
    fitted_gr_line,
    monthly_counts,
    theoretical_gr_line,
)
from location_models import (
    FaultLocationModel,
    RandomLocationModel,
    VentCentredLocationModel,
    VolcanicSwarmLocationModel,
)
from simulator import EarthquakeSimulator
from volcano_monitor import VolcanoMonitor


def run_demo(model_name: str, location_model):
    print(f"\n=== {model_name} ===")

    sim = EarthquakeSimulator(
        lambda0=100.0,
        k=4.0,
        m_min=1.0,
        m_max=7.0,
        b=1.0,
        seed=123,
        location_model=location_model,
    )

    monitor = VolcanoMonitor(
        short_window_days=30.0,
        long_window_days=90.0,
        rate_ratio_threshold=2.5,
        min_short_count=8,
        ash_mag_threshold=3.5,
        pdc_mag_threshold=5.0,
        eruption_cooldown_days=30.0,
    )

    all_events = []
    eruption_log = []

    # Generate one year in monthly steps
    for _ in range(12):
        all_events.extend(sim.step(1.0 / 12.0))

        eruption = monitor.check_for_eruption(all_events, sim.current_time)
        if eruption is not None:
            eruption_log.append(eruption)
            print(
                f"  eruption triggered: {eruption['eruption_type']} "
                f"at t={eruption['time_years']:.2f} yr"
            )

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

        eruption = monitor.check_for_eruption(all_events, sim.current_time)
        if eruption is not None:
            eruption_log.append(eruption)
            print(
                f"  eruption triggered after aftershocks: {eruption['eruption_type']} "
                f"at t={eruption['time_years']:.2f} yr"
            )

    print("events generated:", len(all_events))
    print("statistics:", sim.get_statistics())

    return sim, monitor, all_events, eruption_log


def plot_results(results, bounds):
    """
    Left panel:
        locations for the different models, with background / aftershock
        distinguished by symbol

    Middle panel:
        cumulative magnitude-frequency relationship with:
        - observed points
        - theoretical line from the simulator b-value
        - fitted line from the catalogue

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
    for model_name, (_, _, events, _) in results.items():
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
    shared_sim = next(iter(results.values()))[0]
    shared_events = next(iter(results.values()))[2]

    # -------------------------------------------------
    # Middle panel: magnitude-frequency
    # -------------------------------------------------
    thresholds, cumulative_counts = cumulative_magnitude_frequency(
        shared_events,
        step=1.0,
    )

    ax_magfreq.scatter(
        thresholds,
        cumulative_counts,
        color="black",
        s=50,
        label="Observed",
    )

    # Theoretical line from simulator b-value
    if len(thresholds) > 0 and len(cumulative_counts) > 0 and cumulative_counts[0] > 0:
        theoretical_counts = theoretical_gr_line(
            thresholds,
            b_value=shared_sim.b,
            anchor_count=cumulative_counts[0],
            anchor_threshold=thresholds[0],
        )

        ax_magfreq.plot(
            thresholds,
            theoretical_counts,
            "--",
            color="tab:red",
            linewidth=2,
            label=f"Theoretical b={shared_sim.b:.2f}",
        )

    # Fitted line from the catalogue
    a_est, b_est = fit_gr_line(thresholds, cumulative_counts)
    if a_est is not None and b_est is not None:
        fitted_counts = fitted_gr_line(thresholds, a_est, b_est)

        ax_magfreq.plot(
            thresholds,
            fitted_counts,
            "--",
            color="tab:blue",
            linewidth=2,
            label=f"Fitted b={b_est:.2f}",
        )

    ax_magfreq.set_yscale("log")
    ax_magfreq.set_xlabel("Magnitude Threshold (Mw)")
    ax_magfreq.set_ylabel("N(M ≥ m)")
    ax_magfreq.set_title("Cumulative Magnitude-Frequency Relationship")
    ax_magfreq.grid(True, which="both", linestyle=":", alpha=0.4)
    ax_magfreq.legend()

    # -------------------------------------------------
    # Right panel: time-frequency
    # -------------------------------------------------
    counts = monthly_counts(shared_events)
    months = np.arange(1, 13)

    ax_timefreq.bar(
        months,
        counts,
        color="black",
        alpha=0.8,
        label="Observed",
    )

    expected_counts = expected_monthly_counts(
        shared_sim.lambda0,
        shared_sim.k,
        n_months=12,
        duration_years=1.0,
    )

    ax_timefreq.plot(
        months,
        expected_counts,
        linestyle=":",
        color="tab:red",
        marker="o",
        linewidth=2,
        label="Expected",
    )

    ax_timefreq.set_xlabel("Month")
    ax_timefreq.set_ylabel("Number of events")
    ax_timefreq.set_title("Time-Frequency Relationship")
    ax_timefreq.set_xticks(months)
    ax_timefreq.grid(True, axis="y", linestyle=":", alpha=0.4)
    ax_timefreq.legend()

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