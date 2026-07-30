# ===========================
# WINDOW SETTINGS
# ===========================

WIDTH = 1000
HEIGHT = 800

FPS = 30

PANEL_WIDTH = 250



# ===========================
# GRID
# ===========================

# Fixed simulation grid

COLS = 50
ROWS = 40

# Only used as a reference
# Actual drawing size is calculated
# from the fullscreen resolution

GRID_SIZE = 20



# ===========================
# VOLCANO
# ===========================

PRESSURE_MIN = 0

PRESSURE_MAX = 100

ERUPTION_THRESHOLD = 90



# ===========================
# EARTHQUAKES
# ===========================

MIN_MAGNITUDE = 0.5

MAX_MAGNITUDE = 6.5

EARTHQUAKE_LIFETIME = 40

SWARM_RADIUS = 4



# ===========================
# MAP GENERATION
# ===========================

NOISE_SCALE = 12

NOISE_OCTAVES = 4

NOISE_PERSISTENCE = 0.5

NOISE_LACUNARITY = 2.0



# ===========================
# TERRAIN
# ===========================

WATER_LEVEL = 0.35

COAST_LEVEL = 0.42

MOUNTAIN_LEVEL = 0.75



# ===========================
# INFRASTRUCTURE
# ===========================

INFRASTRUCTURE = {


    "house": {

        "max_health": 100,

        "vulnerability": 1.0

    },


    "bridge": {

        "max_health": 150,

        "vulnerability": 1.5

    },


    "road": {

        "max_health": 200,

        "vulnerability": 0.5

    }

}



# ===========================
# COLOURS
# ===========================

WATER = (40,90,170)

LAND = (85,150,85)

GRID = (40,40,40)

WHITE = (255,255,255)

BLACK = (0,0,0)


YELLOW = (240,220,70)

ORANGE = (255,140,0)

RED = (220,50,40)

ASH = (120,120,120)

LAVA = (255,80,20)

CALDERA = (140,0,140)