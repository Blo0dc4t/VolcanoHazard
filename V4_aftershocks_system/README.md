# Earthquake Simulation Package

This project generates synthetic earthquake catalogues for games, simulations, or visualisation. The package separates earthquake generation, aftershocks, spatial location modelling, eruption detection, and catalogue analysis into independent modules.

## Files

- `simulator.py` — handles background earthquake occurrence, magnitudes, seismic moments, and state management.
- `location_models.py` — handles where background earthquakes occur on the map.
- `aftershock_model.py` — generates aftershock sequences using productivity, Omori decay, Båth-style magnitude limits, parent-centred locations, and a trigger threshold for qualifying mainshocks.
- `volcano_monitor.py` — detects volcanic unrest and eruption conditions from earthquake activity.
- `analysis.py` — helper functions for magnitude-frequency analysis, Gutenberg–Richter fitting, expected occurrence rates, and plot support.
- `example_usage.py` — demonstrates how all components work together.

---

# 1. `simulator.py`

This file contains the `EarthquakeSimulator` class.

It models the **background earthquake process** only.

The simulator does **not** generate aftershocks or decide eruption state.

## Earthquake occurrence model

Background earthquakes are generated using a non-homogeneous Poisson process (NHPP).

The earthquake occurrence rate is:

```math
\lambda(t)=\lambda_0 e^{kt}
```

where:

- `t` is time in years
- `lambda0` is the initial earthquake rate
- `k` controls how quickly the rate increases

The expected number of earthquakes over a time interval is the integral of the rate.

## Magnitude model

Magnitudes are sampled using a truncated Gutenberg–Richter distribution.

```math
\log_{10}N(M\ge m)=a-bm
```

where:

- `N(M ≥ m)` is the cumulative number of earthquakes larger than magnitude `m`
- `a` controls the overall seismicity level
- `b` controls the ratio of small to large earthquakes

## Seismic moment

Moment magnitude is converted into seismic moment using:

```math
M_0 = 10^{1.5M_w + 9.1}
```

where `M_w` is moment magnitude and `M_0` is seismic moment in N·m.

## Main features

- generates background earthquakes
- converts magnitude to seismic moment
- supports save/load of simulation state
- supports stepping through time

## Key parameters

### `lambda0`
Initial earthquake rate.

Higher values generate more background earthquakes overall.

### `k`
Rate growth parameter.

Higher values produce stronger increases in seismicity through time.

### `m_min`
Minimum generated magnitude.

### `m_max`
Maximum generated magnitude.

### `b`
Gutenberg–Richter b-value.

Higher values produce more small earthquakes and fewer large earthquakes.

### `duration_years`
Length of simulation.

### `seed`
Random seed used for reproducibility.

## Main methods

### `step(dt)`
Advance the simulation by `dt` years and generate any earthquakes occurring in that interval.

### `generate_until(t_end)`
Generate earthquakes up to a specific time.

### `generate_year()`
Generate earthquakes for the entire simulation period.

### `get_current_rate()`
Return `lambda(t)` at the current simulation time.

### `get_next_event_time()`
Peek at the next event time without modifying simulator state.

### `get_statistics()`
Return summary statistics of the generated catalogue.

### `serialize_state()` / `load_state()`
Save and restore simulator state.

## Event structure

Each background event contains fields such as:

- `type` — `background`
- `time_years` — time of the event in years
- `month` — month number derived from the event time
- `magnitude` — moment magnitude
- `seismic_moment_Nm` — seismic moment in N·m
- `x`, `y` — location, if a location model is attached

---

# 2. `location_models.py`

This file contains the models that control **where background earthquakes occur** on the map.

The location models do not change the timing, magnitude distribution, or eruption logic.

All location models inherit from the base `LocationModel` class.

## Shared behaviour

Every location model is given map bounds:

```python
(x_min, x_max, y_min, y_max)
```

The public `sample_location()` method uses rejection sampling to ensure the returned point stays inside the map bounds.

## Classes

### `RandomLocationModel`
Samples locations uniformly across the map.

### `VentCentredLocationModel`
Samples locations clustered around a vent or anchor point.

#### `radial_scale`
Controls how quickly locations spread away from the vent.

### `FaultLocationModel`
Samples earthquakes along one or more fault segments.

Each fault segment is specified as:

```python
(x1, y1, x2, y2, weight)
```

#### `perpendicular_sigma`
Controls how far events are allowed to deviate sideways from the fault line.

### `VolcanicSwarmLocationModel`
A mixture model designed for volcanic swarms.

It can place events near:

- the vent
- the magma chamber
- the volcanic edifice
- a fault system

#### Weight parameters

- `vent_weight`
- `chamber_weight`
- `edifice_weight`
- `fault_weight`

#### Scale parameters

- `vent_scale`
- `chamber_scale`
- `edifice_scale`

---

# 3. `aftershock_model.py`

This file contains `AftershockModel`, which generates aftershock sequences for a parent earthquake.

It handles:

- productivity law for aftershock counts
- Omori-style decay for aftershock timing
- Gutenberg–Richter sampling for aftershock magnitudes
- Båth-style magnitude cap
- parent-centred aftershock locations

## Key parameters

### `productivity`
Baseline number of aftershocks.

### `alpha`
Controls how strongly larger mainshocks produce more aftershocks.

### `reference_magnitude`
Reference magnitude used by the productivity law.

### `p`
Omori decay exponent.

### `c_days`
Omori offset parameter.

### `duration_days`
Length of the aftershock sequence.

### `bath_offset`
Typical difference between the mainshock and the largest aftershock.

### `bath_offset_std`
Random scatter applied to the Båth offset.

### `radius_scale`
Base scale of the aftershock cloud around the parent rupture.

### `radius_exponent`
Controls how aftershock spread grows with mainshock magnitude.

## Main method

### `generate(...)`
Given a mainshock event and the simulator, generate a list of aftershock events.

Aftershocks are:

- time clustered around the mainshock using Omori's law
- magnitude-limited using Båth's law
- spatially clustered around the parent event

---

# 4. `volcano_monitor.py`

This file detects volcanic unrest from earthquake activity.

It does **not** generate earthquakes.

Instead it analyses recent earthquakes and determines whether eruption conditions are met.

## Concept

The monitor compares:

- short-term seismicity
- long-term seismicity

using sliding time windows.

## Key parameters

### `short_window_days`
Recent seismicity window.

### `long_window_days`
Background seismicity window.

### `rate_ratio_threshold`
Required increase in seismicity before eruption can occur.

### `min_short_count`
Minimum recent earthquake count.

### `ash_mag_threshold`
Magnitude threshold required for ash-producing eruptions.

### `pdc_mag_threshold`
Magnitude threshold required for ash + PDC eruptions.

### `eruption_cooldown_days`
Minimum time between eruptions.

## Main methods

### `status(events, current_time_years)`
Returns:

- short-term event count
- long-term event count
- rate ratio
- recent maximum magnitude
- cooldown state

### `check_for_eruption(events, current_time_years)`
Returns `None` or a dictionary describing the eruption if eruption conditions are met.

---

# 5. `analysis.py`

This file contains helper functions for analysing the generated earthquake catalogue.

## `filter_events(...)`
Filter events by type.

## `monthly_counts(...)`
Count events in each month, optionally filtering by event type.

## `expected_monthly_counts(...)`
Compute expected monthly counts from:

```math
\lambda(t)=\lambda_0 e^{kt}
```

## `cumulative_magnitude_frequency(...)`
Compute cumulative counts:

```math
N(M\ge m)
```

for a set of magnitude thresholds, optionally filtering by event type.

## `fit_gr_line(...)`
Fit a Gutenberg–Richter relationship:

```math
\log_{10}N = a - bM
```

Returns estimated `a` and `b` values.

## `theoretical_gr_line(...)`
Generate a theoretical Gutenberg–Richter curve using a specified `b` value.

## `fitted_gr_line(...)`
Generate a Gutenberg–Richter curve using fitted `a` and `b` values.

---

# 6. `example_usage.py`

This file demonstrates how to use the simulator, aftershock model, volcano monitor, and analysis helpers together.

## What it does

- creates several location models
- runs the earthquake simulator for each one
- generates a background earthquake catalogue
- generates aftershocks for the first background event
- checks eruption state from earthquake activity
- plots the locations and summary relationships

## Plots produced

### Left panel
Earthquake locations for each location model.

Colour indicates location model.
Marker type indicates background versus aftershock.

### Middle panel
Cumulative magnitude-frequency relationship.

It shows:

- background observed points
- aftershock observed points
- theoretical background Gutenberg–Richter line from the simulator `b` value
- fitted background Gutenberg–Richter line from the catalogue

This keeps the background and aftershock populations visually separate.

### Right panel
Monthly earthquake frequency.

It shows:

- background monthly counts as bars
- aftershock monthly counts stacked on top
- expected background monthly counts from the NHPP as a dotted line

This makes it easy to compare the observed catalogue against the expected background rate.

---

# How the pieces fit together

A typical workflow is:

1. Create a location model.
2. Pass it into `EarthquakeSimulator`.
3. Generate background earthquakes with `step()` or `generate_year()`.
4. Generate aftershocks for selected mainshocks with `AftershockModel`.
5. Pass the catalogue to `VolcanoMonitor`.
6. Use `analysis.py` helpers for fitting and plotting.

Example:

```python
from simulator import EarthquakeSimulator
from aftershock_model import AftershockModel
from volcano_monitor import VolcanoMonitor
from location_models import VentCentredLocationModel

bounds = (0.0, 100.0, 0.0, 100.0)
loc_model = VentCentredLocationModel(bounds, vent_x=50.0, vent_y=50.0, radial_scale=6.0)

sim = EarthquakeSimulator(lambda0=2.0, k=2.0, location_model=loc_model, seed=123)
aftershock_model = AftershockModel()
monitor = VolcanoMonitor()

background = sim.generate_year()
```

---

# Parameter tuning guide

## Increase background earthquake frequency

Increase:

- `lambda0`
- `k`

## Decrease background earthquake frequency

Decrease:

- `lambda0`
- `k`

## Increase proportion of small earthquakes

Increase:

- `b`

## Tighten vent clustering

Decrease:

- `radial_scale`

## Broaden fault zones

Increase:

- `perpendicular_sigma`

## Make aftershock sequences more productive

Increase:

- `productivity`
- `alpha`

## Make aftershocks decay more slowly

Decrease:

- `p`

## Make aftershock clouds larger

Increase:

- `radius_scale`
- `radius_exponent`

## Make eruptions easier to trigger

Decrease:

- `rate_ratio_threshold`
- `min_short_count`
- `ash_mag_threshold`
- `pdc_mag_threshold`

## Make eruptions harder to trigger

Increase:

- `rate_ratio_threshold`
- `min_short_count`
- `ash_mag_threshold`
- `pdc_mag_threshold`
- `eruption_cooldown_days`

---

# Notes

This project is a simplified synthetic earthquake generator.

It does **not** include:

- real tectonic stress transfer
- rupture physics
- realistic fault growth
- spatially varying geology
- full aftershock sequence modelling beyond the simplified empirical model
- full eruption physics

It is intended as a clean, controllable starting point for simulation or game use.
