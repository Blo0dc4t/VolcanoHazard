import json
import sys
from pathlib import Path


if getattr(sys, "frozen", False):
    SETTINGS_PATH = Path(sys.executable).resolve().parent / "settings.json"
else:
    SETTINGS_PATH = Path(__file__).resolve().parent / "settings.json"


with SETTINGS_PATH.open("r", encoding="utf-8") as settings_file:
    SETTINGS = json.load(settings_file)


GENERAL_DEFAULTS = {
    "General": SETTINGS["general"],
}

WORLD_DEFAULTS = SETTINGS["world"]
VOLCANO_DEFAULTS = SETTINGS["volcano"]
TERRAIN_TYPES = SETTINGS["terrain_types"]
INFRASTRUCTURE_TYPES = SETTINGS["infrastructure_types"]


# Game states

GAME_STATES = {

    "HOME": -1,

    "CITY_SELECTION": 0,

    "PLAYING": 1,

    "PAUSED": 2,

    "BUILDING_PLACEMENT": 3,

    "OPTIONS": 4,

}

