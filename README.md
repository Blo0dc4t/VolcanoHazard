# Volcano Hazard

Volcano Hazard is a Pygame simulation and strategy game. You manage settlements in a procedurally generated world while volcanoes produce earthquakes, lava, ash, and eruptions.

## Requirements

- Windows
- Python 3.12 or a compatible Python version
- Pygame
- `noise`
- NumPy

## Run From Source

Open a terminal in the project folder and install the dependencies:

```powershell
python -m pip install pygame noise numpy
```

Start the game with:

```powershell
python main.py
```

The game opens in fullscreen mode.

## Main Menu

- **Play**: Generate a world and begin the game.
- **Options**: Edit the world and volcano settings before starting.
- **Quit**: Close the game.

## Options

The options screen is divided into three top-level groups:

### General

- World width and height
- Sidebar fraction
- Simulation speed

### World defaults

- World generation
- Wind
- Hazard behaviour
- Lava behaviour
- Ash behaviour
- Earthquake damage

### Volcano defaults


- **Infrastructure types**
	- City
	- Town
	- Seismometer
	- Road
	- Health, size, colour, income, costs, detection radius, and terrain rules

- **Terrain types**
	- Water
	- Plains
	- Mountains
	- Terrain levels and colours



List-valued infrastructure fields such as colours, sizes, and terrain lists should be entered as JSON arrays, for example `[255, 255, 0]` or `["mountains", "water"]`.
Click a text box and type a new value. Use the mouse wheel to scroll through long sections. Click a tab or use the left and right arrow keys to change groups. Press **Enter** to apply the settings and return to the home screen. Click **Play** to start a game using the saved settings. Press **Escape** to leave the options screen without applying new changes.

## How to Play

When a world is generated, the game begins in city-selection mode. Click a city or settlement on the map to claim it for the current player. Once cities are selected, the simulation can be managed from the map and sidebar.

### Controls

| Key or action | Function |
|---|---|
| Left mouse button | Select a structure, claim a city, or place a building |
| `Enter` | Pause or resume the simulation |
| `B` | Enter or leave building mode |
| `1`-`9` | Select a building type while in building mode |
| `R` | Rotate the building in placement mode; repair the selected structure otherwise |
| Left arrow | Switch to the previous player |
| Right arrow | Switch to the next player |
| `Escape` | Return to the home menu |

### Building

1. Press `B` to enter building mode.
2. Press a number from `1` to `9` to select an available building type.
3. Click a valid location on the map.
4. Press `B` again to cancel building mode.

Buildings must satisfy the terrain and placement rules shown by the game. Construction uses the current player's available resources.

### Simulation

The simulation advances while the game is playing. Volcano pressure, fractures, earthquakes, lava, ash, wind, infrastructure damage, and repairs are updated over time. Press `Enter` to pause the simulation when you need time to inspect the map or plan construction.

### Road Connectivity

The first city claimed by each player becomes their capital. The capital is always active. Other buildings only contribute their income when they are connected to the capital by a continuous path of that player's roads. Roads do not provide income themselves; they activate connected cities, towns, and seismometers.

Destroyed buildings and roads do not count as connected until they are repaired.

## Project Structure

- `main.py`: Startup flow, menu state, input handling, and main loop
- `renderer.py`: Menu and gameplay rendering
- `world.py`: World creation, simulation updates, players, hazards, and buildings
- `terrain.py`: Procedural terrain generation
- `volcano.py`: Volcano behaviour and eruption logic
- `infrastructure.py`: Building types and structure behaviour
- `player.py`: Player state and resources
- `constants.py`: Loads settings and defines internal game states
- `settings.json`: Editable general, world, volcano, terrain, and infrastructure settings

## Editing Game Settings

The editable configuration is stored in `settings.json` in the project folder. It contains:

- `general`: World dimensions, sidebar fraction, and simulation speed
- `world`: Terrain generation, wind, lava, ash, and earthquake settings
- `volcano`: Volcano pressure, fracture, earthquake, and eruption settings
- `terrain_types`: Terrain levels and colours
- `infrastructure_types`: Building health, costs, sizes, income, colours, and terrain rules

The game loads this file when it starts, so these values can be changed without editing Python code. Keep the section and property names unchanged.

## Build a Windows Executable

Install PyInstaller in the same Python environment used to run the game:

```powershell
python -m pip install pyinstaller
```

Build a folder-based executable:

```powershell
python -m PyInstaller --clean --name VolcanoHazard --windowed --onedir --add-data "settings.json;." main.py
```

The executable will be located at:

```text
dist\VolcanoHazard\VolcanoHazard.exe
```

The `--add-data "settings.json;."` option automatically includes `settings.json` in the packaged folder. Depending on the PyInstaller version, it may appear beside the executable or inside `dist\VolcanoHazard\_internal`. The game supports both locations. An external copy beside the executable takes priority, allowing settings to be edited after packaging.

For a single executable, use the same approach if you do not need to edit the settings file after packaging:

```powershell
python -m PyInstaller --clean --name VolcanoHazard --windowed --onefile --add-data "settings.json;." main.py
```

The single-file executable will be located at:

```text
dist\VolcanoHazard.exe
```

With `--onefile`, the settings file is bundled into the executable and extracted to a temporary folder when the game runs. Use the `--onedir` build if players need to edit `settings.json` after packaging.

For troubleshooting, build without `--windowed` so Python errors remain visible in a console:

```powershell
python -m PyInstaller --name VolcanoHazard main.py
```

For a console-enabled build that also includes the settings file:

```powershell
python -m PyInstaller --clean --name VolcanoHazard --add-data "settings.json;." main.py
```
