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
from aftershock_model import AftershockModel
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
        m_max=9.0,
        b=1.0,
        seed=123,
        location_model=location_model,
    )

    aftershock_model = AftershockModel(
        productivity=3.0,
        alpha=0.8,
        reference_magnitude=4.0,
        trigger_magnitude=4.0,
        p=1.1,
        c_days=0.1,
        duration_days=14.0,
        bath_offset=1.2,
        bath_offset_std=0.2,
        radius_scale=1.0,
        radius_exponent=0.5,
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

    # Generate one year in monthly steps.
    # After each step, any qualifying background event can trigger its own aftershock sequence.
    for _ in range(12):
        background = sim.step(1.0 / 12.0)
        all_events.extend(background)

        for event in background:
            if aftershock_model.should_trigger(event):
                aftershocks = aftershock_model.generate(
                    simulator=sim,
                    mainshock_event=event,
                    mainshock_location=(
                        event.get('x', 0.0),
                        event.get('y', 0.0),
                    ),
                    duration_days=10.0,
                )
                all_events.extend(aftershocks)

        eruption = monitor.check_for_eruption(all_events, sim.current_time)
        if eruption is not None:
            eruption_log.append(eruption)
            print(
                f"  eruption triggered: {eruption['eruption_type']} "
                f"at t={eruption['time_years']:.2f} yr"
            )

    print("events generated:", len(all_events))
    print("statistics:", sim.get_statistics())

    return sim, aftershock_model, monitor, all_events, eruption_log


def plot_results(results, bounds):
    """
    Left panel:
        locations for the different models, with background / aftershock
        distinguished by symbol.

    Middle panel:
        cumulative magnitude-frequency relationship with observed points,
        theoretical line from simulator b-value, and fitted line from the
        background catalogue; aftershock points are shown separately.

    Right panel:
        observed monthly counts split into background and aftershocks,
        plus expected background monthly counts from the NHPP.
    """

    colours = {
        'Random': 'tab:blue',
        'Vent': 'tab:red',
        'Fault': 'tab:green',
        'Swarm': 'tab:purple',
    }

    markers = {
        'background': 'o',
        'aftershock': 'x',
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
    for model_name, (_, _, _, events, _) in results.items():
        colour = colours[model_name]

        for event_type in ('background', 'aftershock'):
            type_events = [e for e in events if e['type'] == event_type]
            if not type_events:
                continue

            xs = [e['x'] for e in type_events if 'x' in e]
            ys = [e['y'] for e in type_events if 'y' in e]
            mags = [e['magnitude'] for e in type_events]
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
    ax_map.set_xlabel('X Position')
    ax_map.set_ylabel('Y Position')
    ax_map.set_title('Earthquake Locations by Model')

    model_handles = [
        Line2D(
            [0],
            [0],
            marker='o',
            color='w',
            markerfacecolor=colour,
            markersize=8,
            label=model_name,
        )
        for model_name, colour in colours.items()
    ]
    model_legend = ax_map.legend(
        handles=model_handles,
        title='Location Model',
        loc='upper left',
    )
    ax_map.add_artist(model_legend)

    symbol_handles = [
        Line2D([0], [0], marker='o', color='black', linestyle='None', markersize=8, label='Background'),
        Line2D([0], [0], marker='x', color='black', linestyle='None', markersize=8, label='Aftershock'),
    ]
    ax_map.legend(handles=symbol_handles, title='Event Type', loc='upper right')

    # -------------------------------------------------
    # Shared catalogue for the other two panels
    # -------------------------------------------------
    shared_sim = next(iter(results.values()))[0]
    shared_events = next(iter(results.values()))[3]

    background_events = [e for e in shared_events if e['type'] == 'background']
    aftershock_events = [e for e in shared_events if e['type'] == 'aftershock']

    # -------------------------------------------------
    # Middle panel: magnitude-frequency
    # -------------------------------------------------
    bg_thresholds, bg_cumulative = cumulative_magnitude_frequency(
        background_events,
        step=1.0,
    )
    ax_magfreq.scatter(
        bg_thresholds,
        bg_cumulative,
        color='black',
        s=50,
        label='Background observed',
    )

    if len(bg_thresholds) > 0 and len(bg_cumulative) > 0 and bg_cumulative[0] > 0:
        theoretical_counts = theoretical_gr_line(
            bg_thresholds,
            b_value=shared_sim.b,
            anchor_count=bg_cumulative[0],
            anchor_threshold=bg_thresholds[0],
        )
        ax_magfreq.plot(
            bg_thresholds,
            theoretical_counts,
            '--',
            color='tab:red',
            linewidth=2,
            label=f'Theoretical background b={shared_sim.b:.2f}',
        )

    a_est, b_est = fit_gr_line(bg_thresholds, bg_cumulative)
    if a_est is not None and b_est is not None:
        fitted_counts = fitted_gr_line(bg_thresholds, a_est, b_est)
        ax_magfreq.plot(
            bg_thresholds,
            fitted_counts,
            '--',
            color='tab:blue',
            linewidth=2,
            label=f'Fitted background b={b_est:.2f}',
        )

    if aftershock_events:
        after_thresholds, after_cumulative = cumulative_magnitude_frequency(
            aftershock_events,
            step=1.0,
        )
        ax_magfreq.scatter(
            after_thresholds,
            after_cumulative,
            color='grey',
            s=45,
            marker='x',
            label='Aftershock observed',
        )

    ax_magfreq.set_yscale('log')
    ax_magfreq.set_xlabel('Magnitude Threshold (Mw)')
    ax_magfreq.set_ylabel('N(M ≥ m)')
    ax_magfreq.set_title('Cumulative Magnitude-Frequency Relationship')
    ax_magfreq.grid(True, which='both', linestyle=':', alpha=0.4)
    ax_magfreq.legend()

    # -------------------------------------------------
    # Right panel: time-frequency
    # -------------------------------------------------
    months = np.arange(1, 13)
    background_counts = monthly_counts(shared_events, event_types='background')
    aftershock_counts = monthly_counts(shared_events, event_types='aftershock')

    ax_timefreq.bar(
        months,
        background_counts,
        color='black',
        alpha=0.85,
        label='Background',
    )
    ax_timefreq.bar(
        months,
        aftershock_counts,
        bottom=background_counts,
        color='grey',
        alpha=0.65,
        label='Aftershock',
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
        linestyle=':',
        color='tab:red',
        marker='o',
        linewidth=2,
        label='Expected background',
    )

    ax_timefreq.set_xlabel('Month')
    ax_timefreq.set_ylabel('Number of events')
    ax_timefreq.set_title('Time-Frequency Relationship')
    ax_timefreq.set_xticks(months)
    ax_timefreq.grid(True, axis='y', linestyle=':', alpha=0.4)
    ax_timefreq.legend()

    return fig


if __name__ == '__main__':
    bounds = (0.0, 100.0, 0.0, 100.0)

    random_model = RandomLocationModel(bounds)
    vent_model = VentCentredLocationModel(bounds, vent_x=50.0, vent_y=50.0, radial_scale=6.0)
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
        'Random': run_demo('Random', random_model),
        'Vent': run_demo('Vent', vent_model),
        'Fault': run_demo('Fault', fault_model),
        'Swarm': run_demo('Swarm', swarm_model),
    }

    plot_results(results, bounds)
    plt.show()
