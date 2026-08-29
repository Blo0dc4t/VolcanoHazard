WORLD_WIDTH = 1000

WORLD_HEIGHT = 1000

SIDEBAR_FRACTION = 0.2


#
# Simulation timing
#

SIMULATION_SPEED = 1


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

