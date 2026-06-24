# Earthquake Simulation Package

This project generates synthetic earthquake catalogues for games, simulations, or visualisation. The package separates earthquake generation, spatial location modelling, eruption detection, and catalogue analysis into independent modules.

## Files

* `simulator.py` — handles earthquake occurrence, magnitudes, seismic moments, and aftershock generation.
* `location_models.py` — handles where earthquakes occur on the map.
* `volcano_monitor.py` — detects volcanic unrest and eruption conditions from earthquake activity.
* `analysis.py` — helper functions for magnitude-frequency analysis, Gutenberg–Richter fitting, expected occurrence rates, and plotting support.
* `example_usage.py` — demonstrates how all components work together.

---

# 1. `simulator.py`

This file contains the `EarthquakeSimulator` class.

It models:

* earthquake occurrence time
* earthquake magnitude
* seismic moment
* aftershock generation

It does **not** determine eruption state.

That responsibility belongs to `volcano_monitor.py`.

---

## Earthquake occurrence model

Background earthquakes are generated using a non-homogeneous Poisson process (NHPP).

The earthquake occurrence rate is:

```math
\lambda(t)=\lambda_0 e^{kt}
```

where:

* (t) is time in years
* (\lambda_0) is the initial earthquake rate
* (k) controls how quickly the rate increases

The expected number of earthquakes over a time interval is:

```math
\Lambda(t)
=
\int \lambda(t)\,dt
```

For the exponential model:

```math
\Lambda(t)
=
\frac{\lambda_0}{k}
\left(
e^{kt}-1
\right)
```

---

## Magnitude model

Magnitudes are sampled using a truncated Gutenberg–Richter distribution.

```math
\log_{10}N(M\ge m)=a-bm
```

where:

* (N(M\ge m)) is the cumulative number of earthquakes larger than magnitude (m)
* (a) controls the overall seismicity level
* (b) controls the ratio of small to large earthquakes

The simulator samples magnitudes directly from this distribution.

---

## Seismic moment

Moment magnitude is converted into seismic moment using:

```math
M_0 = 10^{1.5M_w + 9.1}
```

where:

* (M_w) = moment magnitude
* (M_0) = seismic moment in N·m

---

## Main features

* generates background earthquakes
* generates aftershocks
* converts magnitude to seismic moment
* supports save/load of simulation state
* supports stepping through time

---

## Key parameters

### `lambda0`

Initial earthquake rate.

Higher values generate more earthquakes overall.

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

---

## Main methods

### `step(dt)`

Advance the simulation by `dt` years and generate any earthquakes occurring in that interval.

### `generate_until(t_end)`

Generate earthquakes up to a specific time.

### `generate_year()`

Generate earthquakes for the entire simulation period.

### `generate_aftershocks(...)`

Generate an Omori-style aftershock sequence.

### `get_current_rate()`

Return:

```math
\lambda(t)
```

at the current simulation time.

### `get_next_event_time()`

Peek at the next event time without modifying simulator state.

### `get_statistics()`

Return summary statistics of the generated catalogue.

### `serialize_state()` / `load_state()`

Save and restore simulator state.

---

## Event structure

Each event contains:

```python
{
    "type": "background" or "aftershock",
    "time_years": float,
    "month": int,
    "magnitude": float,
    "seismic_moment_Nm": float,
    "x": float,
    "y": float,
}
```

if a location model is attached.

---

# 2. `location_models.py`

This file controls earthquake spatial distribution.

The location models affect:

* where earthquakes occur

They do **not** affect:

* earthquake frequency
* magnitude distribution
* eruption state

---

## Shared behaviour

All models are constrained by map bounds:

```python
(x_min, x_max, y_min, y_max)
```

Locations are generated using rejection sampling to ensure all earthquakes remain inside the map.

---

## `RandomLocationModel`

Uniform random spatial distribution.

Useful for testing.

---

## `VentCentredLocationModel`

Clusters earthquakes around a volcanic vent.

### Parameters

#### `vent_x`

Vent x-coordinate.

#### `vent_y`

Vent y-coordinate.

#### `radial_scale`

Controls how quickly event density decreases away from the vent.

Smaller values produce tighter clustering.

---

## `FaultLocationModel`

Generates earthquakes along fault traces.

Each fault segment is defined by:

```python
(x1, y1, x2, y2, weight)
```

### Parameters

#### `perpendicular_sigma`

Controls how far events may deviate from the fault trace.

---

## `VolcanicSwarmLocationModel`

Mixture model designed for volcanic unrest.

Can generate earthquakes near:

* vent
* magma chamber
* volcanic edifice
* regional faults

### Weight parameters

* `vent_weight`
* `chamber_weight`
* `edifice_weight`
* `fault_weight`

These determine how often each source is selected.

### Scale parameters

* `vent_scale`
* `chamber_scale`
* `edifice_scale`

These control the spatial spread around each source.

---

# 3. `volcano_monitor.py`

This file detects volcanic unrest from earthquake activity.

It does **not** generate earthquakes.

Instead it analyses recent earthquakes and determines whether eruption conditions are met.

---

## Concept

The monitor compares:

* short-term seismicity
* long-term seismicity

using sliding time windows.

The short-term earthquake rate is:

```math
R_s
=
\frac{N_s}{T_s}
```

The long-term earthquake rate is:

```math
R_l
=
\frac{N_l}{T_l}
```

The monitor then evaluates:

```math
\frac{R_s}{R_l}
```

to determine whether activity is increasing unusually quickly.

---

## Eruption types

### `"ash"`

Ash-producing eruption.

### `"ash_and_pdc"`

Ash eruption with pyroclastic density currents.

---

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

---

## Main methods

### `volcano_status(...)`

Returns:

* short-term event count
* long-term event count
* rate ratio
* recent maximum magnitude

### `check_for_eruption(...)`

Returns:

```python
None
```

or:

```python
{
    "eruption_type": ...
}
```

if eruption conditions are met.

---

# 4. `analysis.py`

This file contains helper functions for analysing the generated catalogue.

---

## `cumulative_magnitude_frequency(...)`

Computes:

```math
N(M\ge m)
```

for a series of magnitude thresholds.

---

## `fit_gr_line(...)`

Fits:

```math
\log_{10}N = a - bM
```

to the generated catalogue.

Returns:

* `a_est`
* `b_est`

---

## `theoretical_gr_line(...)`

Constructs a Gutenberg–Richter relationship using a specified b-value.

Useful for comparing:

* simulated catalogue
* expected catalogue

---

## `fitted_gr_line(...)`

Constructs a Gutenberg–Richter curve using fitted values of:

* `a`
* `b`

---

## `expected_monthly_counts(...)`

Computes expected monthly earthquake counts from:

```math
\lambda(t)=\lambda_0 e^{kt}
```

This allows comparison between:

* observed monthly counts
* expected monthly counts

---

## `monthly_counts(...)`

Computes observed monthly earthquake counts.

---

# 5. `example_usage.py`

Demonstrates how all modules work together.

---

## Workflow

1. Create location model.
2. Create simulator.
3. Create volcano monitor.
4. Generate earthquakes.
5. Detect eruptions.
6. Analyse catalogue.
7. Plot results.

---

## Produced plots

### Left panel

Earthquake locations.

Colour indicates:

* Random model
* Vent-centred model
* Fault model
* Volcanic swarm model

Marker type indicates:

* background earthquake
* aftershock

---

### Middle panel

Cumulative magnitude-frequency relationship.

Displays:

* observed catalogue as black points
* theoretical Gutenberg–Richter relationship using simulator b-value as a red dashed line
* fitted Gutenberg–Richter relationship using estimated b-value as a blue dashed line

This allows direct comparison between:

* expected seismicity
* generated seismicity

---

### Right panel

Monthly earthquake frequency.

Displays:

* observed monthly counts as bars
* expected monthly counts from the NHPP model as a dotted line

This allows direct comparison between:

* generated earthquake counts
* theoretical occurrence-rate model

---

# Parameter Tuning Guide

## Increase earthquake frequency

Increase:

* `lambda0`
* `k`

---

## Decrease earthquake frequency

Decrease:

* `lambda0`
* `k`

---

## Increase proportion of small earthquakes

Increase:

* `b`

---

## Increase proportion of large earthquakes

Decrease:

* `b`

---

## Tighten vent clustering

Decrease:

* `radial_scale`

---

## Broaden fault zones

Increase:

* `perpendicular_sigma`

---

## Make eruptions easier to trigger

Decrease:

* `rate_ratio_threshold`
* `min_short_count`
* `ash_mag_threshold`
* `pdc_mag_threshold`

---

## Make eruptions harder to trigger

Increase:

* `rate_ratio_threshold`
* `min_short_count`
* `ash_mag_threshold`
* `pdc_mag_threshold`
* `eruption_cooldown_days`

---

# Notes

This package is intended as a synthetic earthquake and volcanic unrest simulator.

It does **not** currently model:

* realistic stress transfer
* rupture mechanics
* magma transport physics
* gas emissions
* ground deformation
* full eruption dynamics

It is designed to provide a controllable framework for games, simulations, and experimentation.
