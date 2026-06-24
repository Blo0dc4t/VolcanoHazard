# Earthquake Simulation Package

This project generates synthetic earthquake catalogues for games, simulations, or visualisation.

## Files

- `simulator.py` — handles earthquake occurrence, magnitudes, seismic moments, and aftershocks.
- `location_models.py` — handles earthquake spatial distributions.
- `example_usage.py` — demonstrates usage and plotting.

---

## simulator.py

This file contains the `EarthquakeSimulator` class.

### Earthquake Rate

Background earthquakes are generated using a non-homogeneous Poisson process:

```math
\lambda(t) = \lambda_0 e^{kt}
```

where:

- `lambda0` is the starting earthquake rate
- `k` controls how rapidly earthquake frequency increases
- `t` is time in years

### Parameters

| Parameter | Description |
|------------|------------|
| `lambda0` | Initial earthquake rate |
| `k` | Exponential growth rate |
| `m_min` | Minimum magnitude |
| `m_max` | Maximum magnitude |
| `b` | Gutenberg–Richter b-value |
| `duration_years` | Simulation length |
| `seed` | Random seed |

### Example

```python
sim = EarthquakeSimulator(
    lambda0=2.0,
    k=2.0,
    seed=123,
)
```

---

## Magnitude Distribution

Magnitudes follow a truncated Gutenberg–Richter distribution.

The Gutenberg–Richter relationship is:

```math
\log_{10}N(M \ge m) = a - bm
```

where:

- `N(M ≥ m)` is the cumulative number of earthquakes larger than magnitude `m`
- `b` controls the relative proportion of large and small earthquakes

Larger values of `b` produce relatively more small earthquakes.

---

## Seismic Moment

Moment magnitude is converted to seismic moment using:

```math
M_0 = 10^{1.5M_w + 9.1}
```

where:

- `M_w` is moment magnitude
- `M_0` is seismic moment in N·m

---

## Aftershocks

Aftershocks are generated using an Omori-style decay law.

Key parameters:

| Parameter | Description |
|------------|------------|
| `duration_days` | Length of aftershock sequence |
| `c_days` | Near-time clustering parameter |
| `p` | Decay exponent |
| `productivity` | Expected aftershock productivity |
| `alpha` | Magnitude dependence |

---

## location_models.py

This file controls where earthquakes occur.

### RandomLocationModel

Uniform random spatial distribution.

```python
model = RandomLocationModel(bounds)
```

### VentCentredLocationModel

Clusters earthquakes around a volcanic vent.

```python
model = VentCentredLocationModel(
    bounds,
    vent_x=50,
    vent_y=50,
    radial_scale=6,
)
```

### FaultLocationModel

Places earthquakes along fault segments.

```python
model = FaultLocationModel(
    bounds,
    segments=[
        (10, 20, 85, 25, 1.0),
    ],
)
```

### VolcanicSwarmLocationModel

Mixture of:

- vent events
- chamber events
- edifice events
- fault events

Useful for volcanic unrest simulations.

---

## example_usage.py

Produces three plots:

### Earthquake Location Map

Shows:

- location model by colour
- background earthquakes as circles
- aftershocks as crosses

### Magnitude–Frequency Relationship

Plots:

```math
N(M \ge m)
```

for integer magnitude thresholds.

### Time–Frequency Relationship

Shows the number of earthquakes occurring in each month.

---

## Increasing Earthquake Frequency

Increase:

```python
lambda0
```

to increase overall earthquake frequency.

Increase:

```python
k
```

to make earthquake frequency rise more rapidly through the simulation.

Example:

```python
sim = EarthquakeSimulator(
    lambda0=5.0,
    k=4.0,
)
```

This will produce significantly more earthquakes than:

```python
sim = EarthquakeSimulator(
    lambda0=1.0,
    k=1.0,
)
```