# Earthquake Simulation Package

This project generates synthetic earthquake catalogues for games, simulations, and visualisation. The package keeps the main pieces separate:

- `simulator.py` — background earthquake generation and catalogue state.
- `volcano_state.py` — exponentially growing volcanic pressure with pressure release after eruptions.
- `volcano_monitor.py` — probabilistic eruption detection from pressure and recent seismicity.
- `aftershock_model.py` — aftershock sequences using productivity law, Omori timing, Gutenberg-Richter magnitudes, and Båth-style magnitude limits.
- `location_models.py` — spatial placement of earthquakes.
- `analysis.py` — catalogue analysis and plotting helpers.
- `example_usage.py` — shows how everything fits together.

---

## 1. `volcano_state.py`

This file contains the `VolcanoState` class.

It models a dimensionless pressure variable that grows exponentially over time and drops after an eruption.

The pressure evolves as

```math
P(t + \Delta t) = P(t) e^{g \Delta t}
```

where:

- `P(t)` is the current pressure multiplier,
- `g` is `pressure_growth_rate`,
- `\Delta t` is time in years.

The background earthquake rate is derived from that pressure:

```math
\lambda(t) = \lambda_0 P(t)
```

### Main parameters

- `initial_pressure` — starting pressure multiplier.
- `pressure_growth_rate` — exponential pressure recharge rate.
- `ash_release_fraction` — fraction of pressure retained after an ash eruption.
- `pdc_release_fraction` — fraction of pressure retained after an ash + PDC eruption.
- `min_pressure` — lower bound on pressure.
- `max_pressure` — optional upper bound on pressure.

### Main methods

- `current_pressure(t)` — pressure multiplier at time `t`.
- `rate_parameters(base_lambda0)` — returns the coefficient and growth rate for `lambda(t)=a e^{gt}`.
- `cumulative_intensity(base_lambda0, t0, t1)` — integrated background intensity over a time window.
- `release(current_time, eruption_type)` — applies a pressure drop after an eruption and logs it.

---

## 2. `simulator.py`

This file contains the `EarthquakeSimulator` class.

It generates background earthquakes, samples magnitudes, converts moment magnitude to seismic moment, and manages simulation time.

It does **not** decide when eruptions happen. That is the job of `volcano_monitor.py`.

### Background occurrence model

With an attached `VolcanoState`, the background rate is pressure-driven:

```math
\lambda(t) = \lambda_0 P(t)
```

and because pressure grows exponentially between eruptions, the rate is also exponential in time within each pressure regime.

The expected number of background earthquakes over a time window is the integral of that rate.

### Magnitude model

Magnitudes are sampled from a truncated Gutenberg-Richter distribution:

```math
\log_{10} N(M \ge m) = a - b m
```

where:

- `a` controls overall seismicity level,
- `b` controls the relative abundance of small versus large earthquakes.

### Seismic moment

Moment magnitude is converted to seismic moment using:

```math
M_0 = 10^{1.5 M_w + 9.1}
```

### Key parameters

- `lambda0` — base earthquake rate when pressure equals 1.
- `m_min` — minimum sampled magnitude.
- `m_max` — maximum sampled magnitude.
- `b` — Gutenberg-Richter b-value.
- `duration_years` — simulation length.
- `seed` — random seed.

### Main methods

- `step(dt)` — advance by `dt` years and generate background earthquakes.
- `generate_until(t_end)` — generate earthquakes up to a specific time.
- `generate_year()` — generate a full simulation year.
- `get_current_rate()` — current pressure-adjusted background rate.
- `get_next_event_time()` — peek at the next event time.
- `get_statistics()` — summary of the generated catalogue.
- `serialize_state()` / `load_state()` — save and restore simulator state.

### Event structure

Each generated background earthquake is stored as a dictionary containing:

- `type` — `background`
- `time_years` — time in years
- `month` — month number derived from the event time
- `magnitude` — moment magnitude
- `seismic_moment_Nm` — seismic moment in N·m
- `x`, `y` — location, if a location model is attached

---

## 3. `volcano_monitor.py`

This file contains the `VolcanoMonitor` class.

It watches recent background seismicity and volcanic pressure, then decides probabilistically whether an eruption should happen.

### Concept

The monitor uses two linked ideas:

- **Seismicity** controls whether an eruption is triggered.
- **Pressure** controls whether the eruption is ash or ash + PDC.

The eruption trigger is probabilistic, not a hard cutoff. Recent seismicity raises the probability of eruption, and pressure raises it further.

A simple representation is:

```math
p_{eruption} = \sigma(eta_0 + eta_P(P - P_0) + eta_R(R - 1) + eta_N(N_s - N_0))
```

where:

- `P` is pressure,
- `R` is the short/long seismicity rate ratio,
- `N_s` is the short-window event count,
- `\sigma` is the logistic sigmoid.

If an eruption occurs, the type is chosen probabilistically using a second pressure-based logistic model.

### Eruption types

- `ash` — ash-producing eruption.
- `ash_and_pdc` — ash eruption with pyroclastic density currents.

### Main parameters

- `short_window_days` — recent seismicity window.
- `long_window_days` — background seismicity window.
- `eruption_bias` — baseline eruption logit.
- `eruption_pressure_midpoint` — pressure level around which eruption likelihood rises strongly.
- `eruption_pressure_weight` — how strongly pressure affects eruption probability.
- `eruption_rate_ratio_weight` — how strongly the short/long seismicity ratio affects eruption probability.
- `eruption_count_weight` — how strongly the short-window event count affects eruption probability.
- `min_short_count` — reference count used in the soft count term.
- `pdc_bias` — baseline logit for the ash+PDC choice.
- `pdc_pressure_midpoint` — pressure level where ash+PDC becomes likely.
- `pdc_pressure_weight` — how strongly pressure affects ash+PDC probability.
- `pdc_rate_ratio_weight` — how strongly the rate ratio affects ash+PDC probability.
- `eruption_cooldown_days` — minimum time between eruptions.

### Main methods

- `status(events, volcano_state, current_time_years)` — returns the recent seismicity and pressure state.
- `check_for_eruption(events, volcano_state, current_time_years, rng)` — returns an eruption record if an eruption is triggered, otherwise `None`.

When an eruption occurs, the pressure is reduced through `VolcanoState.release(...)` and the pressure drop is recorded.

---

## 4. `aftershock_model.py`

This file contains the `AftershockModel` class.

It generates aftershock sequences for qualifying background earthquakes.

### Main features

- productivity law for the number of aftershocks,
- Omori’s law for the timing,
- Gutenberg-Richter sampling for the magnitudes,
- Båth’s law as an upper magnitude guide,
- parent-centred spatial clustering.

### Triggering

A background earthquake must exceed `trigger_magnitude` before it can generate aftershocks.

### Productivity law

The expected number of aftershocks is:

```math
E[N_{after}] = K 10^{lpha(M - M_{ref})}
```

where:

- `K` is the productivity constant,
- `alpha` controls how strongly larger mainshocks generate aftershocks,
- `M` is the mainshock magnitude,
- `M_ref` is the reference magnitude.

### Omori’s law

Aftershock times follow a truncated Omori decay:

```math
n(t) = rac{K}{(c + t)^p}
```

where:

- `c` is the near-time offset,
- `p` is the decay exponent,
- `t` is time since the mainshock.

### Båth’s law

The largest aftershock is limited by a typical offset from the mainshock magnitude:

```math
M_{max, after} pprox M_{mainshock} - 1.2
```

This is implemented as a tunable magnitude cap.

### Spatial clustering

Aftershocks are sampled around the parent event location, with the radius scaling with the mainshock magnitude.

---

## 5. `location_models.py`

This file contains the models that control **where** earthquakes occur on the map.

The location models do not change the timing, magnitude distribution, pressure evolution, or eruption logic. They only decide the spatial coordinates of each background event.

All location models inherit from the base `LocationModel` class.

### Shared behaviour

Every location model is given map bounds:

```python
(x_min, x_max, y_min, y_max)
```

The public `sample_location()` method uses rejection sampling to ensure the returned point stays inside the map bounds.

### Classes

- `RandomLocationModel` — uniform random locations across the map.
- `VentCentredLocationModel` — locations clustered around a vent or anchor point.
- `FaultLocationModel` — earthquakes along one or more fault segments.
- `VolcanicSwarmLocationModel` — mixture model for volcanic swarms.

### Key parameters

- `radial_scale` — how quickly vent-centred locations spread away from the vent.
- `perpendicular_sigma` — sideways scatter away from fault traces.
- `vent_weight`, `chamber_weight`, `edifice_weight`, `fault_weight` — mixture weights in the volcanic swarm model.
- `vent_scale`, `chamber_scale`, `edifice_scale` — spatial spread around each volcanic source.

---

## 6. `analysis.py`

This file contains helper functions for analysing the generated earthquake catalogue.

### `cumulative_magnitude_frequency(...)`

Computes:

```math
N(M \ge m)
```

for a series of magnitude thresholds.

### `fit_gr_line(...)`

Fits:

```math
\log_{10} N = a - bM
```

to the generated catalogue.

Returns:

- `a_est`
- `b_est`

### `theoretical_gr_line(...)`

Constructs a Gutenberg-Richter relationship using a specified b-value.

### `fitted_gr_line(...)`

Constructs a Gutenberg-Richter curve using fitted values of `a` and `b`.

### `expected_monthly_counts(...)`

Computes expected monthly background earthquake counts from the pressure-driven model:

```math
\lambda(t) = \lambda_0 P(t)
```

using the pressure at the start of each month and the exponential pressure growth rate.

### `monthly_counts(...)`

Computes observed monthly earthquake counts, optionally filtered by event type.

---

## 7. `example_usage.py`

This file demonstrates how all modules work together.

### Workflow

1. Create a volcano state.
2. Create a location model.
3. Create a simulator.
4. Create a volcano monitor.
5. Create an aftershock model.
6. Generate background earthquakes.
7. Generate aftershocks for every qualifying background event.
8. Detect eruptions from pressure and recent seismicity.
9. Plot the results.

### Produced plots

#### Left panel

Earthquake locations.

Colour indicates the location model.

Marker type indicates:

- background earthquake
- aftershock

#### Top-right panel

Cumulative magnitude-frequency relationship.

Displays:

- observed background catalogue as black points,
- theoretical Gutenberg-Richter relationship using the simulator b-value as a red dashed line,
- fitted Gutenberg-Richter relationship using the estimated b-value as a blue dashed line,
- aftershock catalogue as grey crosses.

#### Bottom-left panel

Monthly earthquake frequency.

Displays:

- background counts as black bars,
- aftershock counts stacked on top in grey,
- expected background monthly counts from the pressure-driven NHPP as a dotted red line,
- eruption times as vertical red lines.

#### Bottom-right panel

Volcanic pressure through time.

This panel shows the hidden pressure variable that drives the background rate and drops after eruptions.

Eruption times are marked by vertical lines, and each drop is shown explicitly.

---

## Parameter tuning guide

### Increase earthquake frequency

Increase:

- `lambda0`
- `pressure_growth_rate`

### Decrease earthquake frequency

Decrease:

- `lambda0`
- `pressure_growth_rate`

### Make large earthquakes rarer

Increase `b`.

### Make eruptions easier to trigger

Decrease:

- `eruption_bias`
- `eruption_pressure_midpoint`
- `eruption_pressure_weight`
- `eruption_rate_ratio_weight`
- `eruption_count_weight`
- `eruption_cooldown_days`

### Make eruptions harder to trigger

Increase:

- `eruption_bias`
- `eruption_pressure_midpoint`
- `eruption_pressure_weight`
- `eruption_rate_ratio_weight`
- `eruption_count_weight`
- `eruption_cooldown_days`

### Make ash + PDC eruptions more likely

Increase:

- `pdc_bias`
- `pdc_pressure_midpoint`
- `pdc_pressure_weight`
- `pdc_rate_ratio_weight`

### Make aftershock sequences more productive

Increase:

- `productivity`
- `alpha`

### Make aftershocks more short-lived

Increase:

- `p`
- `c_days`

### Make aftershocks cluster more tightly around the mainshock

Decrease:

- `radius_scale`

---

## Notes

This project is a simplified synthetic earthquake and volcanic unrest simulator.

It does **not** currently model:

- real tectonic stress transfer,
- rupture mechanics,
- magma transport physics,
- gas emissions,
- ground deformation,
- full eruption dynamics.

It is designed to provide a controllable framework for games, simulations, and experimentation.
