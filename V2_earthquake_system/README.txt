# Earthquake Simulation Package

This project generates synthetic earthquake catalogues for games, simulations, or visualisation. It is split into three files:

* `simulator.py` — handles when earthquakes happen, how large they are, seismic moment conversion, eruption detection, and aftershock generation.
* `location_models.py` — handles where earthquakes occur on the map.
* `example_usage.py` — shows how to combine the simulator and location models and plot the results.

---

## 1. `simulator.py`

This file contains the `EarthquakeSimulator` class.

It models the **timing**, **size**, and **eruption state** of earthquakes.

### What it does

The simulator uses a **non-homogeneous Poisson process** for background earthquakes. That means the earthquake rate changes over time instead of staying constant.

The background rate is:

```math
\lambda(t) = \lambda_0 e^{kt}
```

where `t` is time in years from the start of the simulation.

It also keeps a catalogue of events so you can look for recent clusters and trigger a volcanic eruption state when seismicity becomes intense enough.

### Main features

* generates background earthquakes over time
* samples magnitudes using a truncated Gutenberg–Richter distribution
* converts moment magnitude to seismic moment
* can generate aftershocks with an Omori-like decay law
* can detect eruption conditions from recent earthquake frequency and magnitude
* can step through time in small increments
* can save and restore state

### Key parameters

#### `lambda0`

Starting earthquake rate at `t = 0`.

* larger values mean more earthquakes overall
* smaller values mean fewer earthquakes overall

#### `k`

Exponential growth rate of earthquake frequency.

* `k > 0` makes earthquakes become more frequent over time
* larger `k` means a stronger increase through the year
* `k = 0` gives a constant rate

#### `m_min`

Minimum magnitude for the Gutenberg–Richter magnitude sampling.

#### `m_max`

Maximum magnitude for the magnitude sampling.

#### `b`

Controls the shape of the magnitude distribution.

* larger `b` gives more small earthquakes and fewer large ones
* smaller `b` gives relatively more large events

#### `duration_years`

How long the simulation runs for.

#### `seed`

Random seed for reproducible results.

### Eruption-detection parameters

These values control whether the simulator decides that a volcanic eruption should be triggered.

#### `short_window_days`

How far back to look for recent seismicity.

* smaller values make the detector more sensitive to sudden swarms
* larger values smooth out short-term noise

#### `long_window_days`

Baseline window used for comparison.

* often larger than `short_window_days`
* used to estimate the background recent rate

#### `rate_ratio_threshold`

How much larger the short-window rate must be than the long-window rate before the volcano is considered active enough to erupt.

#### `min_short_count`

Minimum number of earthquakes in the short window before an eruption can be considered.

This prevents tiny clusters from triggering an eruption too easily.

#### `ash_mag_threshold`

If the recent earthquakes are frequent enough and the largest recent magnitude is above this value, the simulator can classify the eruption as ash-producing.

#### `pdc_mag_threshold`

If the recent earthquakes are frequent enough and the largest recent magnitude is above this value, the simulator can classify the eruption as producing ash plus pyroclastic density currents.

#### `eruption_cooldown_days`

How long to wait after an eruption before another one can be triggered.

This stops the same swarm from repeatedly triggering eruptions every step.

### Important methods

#### `rate(t)`

Returns the instantaneous background earthquake rate at time `t`.

#### `cumulative_intensity(t)`

Returns the integrated rate from the start of the simulation to time `t`.

#### `step(dt)`

Advances the simulation by `dt` years and returns any background earthquakes that occurred in that interval.

#### `generate_until(t_end)`

Generates earthquakes from the current time up to `t_end`.

#### `generate_year()`

Convenience method that generates a full year of background earthquakes.

#### `generate_aftershocks(...)`

Generates aftershocks after a main earthquake using a simplified Omori-style decay.

Key aftershock parameters:

* `duration_days` — how long the aftershock sequence lasts
* `c_days` — controls how strongly aftershocks cluster immediately after the mainshock
* `p` — decay exponent for the aftershock rate
* `productivity` — baseline number of aftershocks
* `alpha` — how strongly larger mainshocks produce more aftershocks

#### `volcano_status()`

Summarises recent seismicity using the short and long time windows.

It returns values such as:

* short-window event count
* long-window event count
* short-window rate
* long-window rate
* rate ratio
* maximum recent magnitude

#### `check_for_eruption()`

Checks whether the recent earthquake activity is strong enough to trigger an eruption.

It can return:

* `None` — no eruption
* `ash` — eruption with ash output
* `ash_and_pdc` — eruption with ash and pyroclastic density currents

#### `get_current_rate()`

Returns the current background rate at the simulator’s internal time.

#### `get_next_event_time()`

Peeks at the next background earthquake time without changing the simulator state.

#### `get_statistics()`

Returns a summary of the generated catalogue, including event counts, mean magnitude, and the last eruption state.

#### `serialize_state()` / `load_state()`

Used to save and restore the simulator state.

### Event structure

Each generated earthquake is stored as a dictionary containing fields such as:

* `type` — `background` or `aftershock`
* `time_years` — time of the event in years
* `month` — month number derived from the event time
* `magnitude` — moment magnitude
* `seismic_moment_Nm` — seismic moment in N·m
* `x`, `y` — location, if a location model is attached

---

## 2. `location_models.py`

This file contains the models that control **where** earthquakes occur on the map.

The location models do not change the timing, magnitude distribution, or eruption logic. They only decide the spatial coordinates of each event.

All location models inherit from the base `LocationModel` class.

### Shared behaviour

Every location model is given map bounds:

```python
(x_min, x_max, y_min, y_max)
```

The public `sample_location()` method uses rejection sampling to ensure the returned point stays inside the map bounds.

### Classes

#### `RandomLocationModel`

Samples locations uniformly across the map.

Use this if you want earthquakes to be spatially random.

#### `VentCentredLocationModel`

Samples locations clustered around a vent or anchor point.

Useful for volcanic systems where earthquakes cluster around a conduit or vent.

Key parameter:

* `radial_scale` — how quickly locations spread away from the vent

Smaller values keep events closer to the vent.

#### `FaultLocationModel`

Samples earthquakes along one or more fault segments.

Each fault segment is specified as:

```python
(x1, y1, x2, y2, weight)
```

where `weight` controls how likely that segment is chosen.

Key parameter:

* `perpendicular_sigma` — how far events are allowed to deviate sideways from the fault line

#### `VolcanicSwarmLocationModel`

A mixture model designed for volcanic swarms.

It can place events near:

* the vent
* the magma chamber
* the volcanic edifice
* a fault system

Key parameters:

* `vent_weight`
* `chamber_weight`
* `edifice_weight`
* `fault_weight`

These determine how often each source is chosen.

Additional scale parameters:

* `vent_scale`
* `chamber_scale`
* `edifice_scale`

These control how widely events spread around each source.

If `fault_segments` is provided, the model can also place events along faults.

---

## 3. `example_usage.py`

This file demonstrates how to use the simulator and the location models together.

### What it does

* creates several location models
* runs the earthquake simulator for each one
* generates a background earthquake catalogue and aftershocks
* plots the locations and summary relationships

### Plots produced

The example script creates a figure with three panels:

1. **Left panel** — earthquake locations for each location model
2. **Middle panel** — cumulative magnitude-frequency relationship
3. **Right panel** — time-frequency relationship by month

### Why the example uses several models

The example compares how different location models change the spatial pattern of earthquakes while keeping the same general timing and magnitude logic.

This makes it easy to see the difference between:

* random spatial placement
* vent-centred clustering
* fault-aligned placement
* volcanic swarm mixtures

---

## How the pieces fit together

A typical workflow is:

1. Create a location model.
2. Pass it into `EarthquakeSimulator`.
3. Call `step()` or `generate_year()` to create earthquakes.
4. Optionally call `generate_aftershocks()` after a main event.
5. Use `volcano_status()` and `check_for_eruption()` to detect volcanic unrest.
6. Use the returned event dictionaries in gameplay or plotting.

Example:

```python
from simulator import EarthquakeSimulator
from location_models import VentCentredLocationModel

bounds = (0.0, 100.0, 0.0, 100.0)
loc_model = VentCentredLocationModel(bounds, vent_x=50.0, vent_y=50.0, radial_scale=6.0)

sim = EarthquakeSimulator(lambda0=2.0, k=2.0, location_model=loc_model, seed=123)
events = sim.generate_year()
status = sim.volcano_status()
eruption = sim.check_for_eruption()
```

---

## Parameter tuning guide

### To increase earthquake frequency

* increase `lambda0`
* increase `k`

### To decrease earthquake frequency

* decrease `lambda0`
* decrease `k`

### To make large earthquakes rarer

* increase `b`

### To make earthquakes cluster more tightly around a vent

* decrease `radial_scale`

### To make faults more diffuse

* increase `perpendicular_sigma`

### To make one volcanic source dominate over the others

* increase its weight in `VolcanicSwarmLocationModel`

### To make eruptions easier to trigger

* decrease `short_window_days`
* decrease `rate_ratio_threshold`
* decrease `min_short_count`
* decrease `ash_mag_threshold`
* decrease `pdc_mag_threshold`

### To make eruptions harder to trigger

* increase `short_window_days`
* increase `rate_ratio_threshold`
* increase `min_short_count`
* increase `ash_mag_threshold`
* increase `pdc_mag_threshold`
* increase `eruption_cooldown_days`

---

## Notes

This project is a simplified synthetic earthquake generator.

It does **not** include:

* real tectonic stress transfer
* rupture physics
* realistic fault growth
* spatially varying geology
* full aftershock sequence modelling
* full eruption physics

It is intended as a clean, controllable starting point for simulation or game use.
