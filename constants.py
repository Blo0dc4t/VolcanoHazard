import math


GENERAL_DEFAULTS = {

    "General": {

        "world_width": 1000,
        "world_height": 1000,
        "sidebar_fraction": 0.2,
        "simulation_speed": 1,

    },

}


WORLD_DEFAULTS = {

    "World generation": {

        "cell_size": 25,
        "noise_scale": 50,
        "noise_octaves": 4,
        "noise_persistence": 0.5,
        "noise_lacunarity": 2.0,
        "caldera_num": 2,
        "caldera_min_distance": 10,

    },

    "Wind": {

        "wind_direction_min": 0.0,
        "wind_direction_max": 2 * math.pi,
        "wind_speed_min": 0.5,
        "wind_speed_max": 2.0,
        "wind_change_rate": 0.05,
        "wind_speed_change_rate": 0.05,

    },

    "Hazard behaviour": {

        "lava_cooling_rate": 0.9,
        "lava_damage_factor": 100,

    },

    "Lava behaviour": {

        "lava_length_factor": 0.15,
        "lava_spread_factor": 0.05,
        "lava_max_spread_chance": 0.4,
        "lava_momentum": 0.15,
        "lava_randomness_factor": 0.15,
        "lava_side_flow_strength": 0.2,

    },

    "Ash behaviour": {

        "ash_settling_rate": 0.9,
        "ash_damage_factor": 5,
        "ash_length_factor": 0.25,
        "ash_spread_factor": 0.15,

    },

    "Earthquake damage": {

        "earthquake_damage_distance_scale": 5,
        "earthquake_damage_factor": 0.01,

    },

}


VOLCANO_DEFAULTS = {

    "Initial state": {

        "caldera_position": (500, 500),
        "initial_pressure": 0.25,
        "initial_fracture": 0.0,

    },

    "Pressure parameters": {

        "recharge_min": 0.005,
        "recharge_max": 0.01,
        "pressure_loss_max": 0.01,

    },

    "Earthquake parameters": {

        "earthquake_multiplier": 40,
        "earthquake_distance_scale": 200,

    },

    "Fracture parameters": {

        "fracture_damage_min": 0.01,
        "fracture_damage_max": 0.06,
        "fracture_healing": 0.96,

    },

    "Eruption parameters": {

        "eruption_pressure_threshold": 0.8,
        "fracture_pressure_effect": 0.3,
        "minimum_pressure": 0.35,

    }

}


# Game states

GAME_STATES = {

    "HOME": -1,

    "CITY_SELECTION": 0,

    "PLAYING": 1,

    "PAUSED": 2,

    "BUILDING_PLACEMENT": 3,

    "OPTIONS": 4,

}

