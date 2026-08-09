import random
import math

from volcano import Volcano
from terrain import Terrain, TERRAIN_TYPES
from infrastructure import Infrastructure, INFRASTRUCTURE_TYPES
from player import Player
from constants import GAME_STATES


class World:

    def __init__(self, width=1000, height=1000):

        #
        # World dimensions
        #

        self.width = width
        self.height = height

        #
        # Terrain
        #

        print("creating terrain...")

        self.terrain = Terrain(
            width,
            height,
            cell_size=25,
            caldera_num=2
        )

        self.grid_width = self.terrain.grid_width
        self.grid_height = self.terrain.grid_height

        #
        # World grid
        #

        self.grid = [

            [
                {
                    "structure": None,
                    "lava": 0.0,
                    "ash": 0.0
                }

                for x in range(self.grid_width)
            ]

            for y in range(self.grid_height)
        ]

        #
        # Infrastructure
        #

        self.infrastructure = []
        self.selected_structure = None

        #
        # Building system
        #

        self.build_structure_type = None

        #
        # Multiplayer
        #

        self.players = []
        self.current_player_index = 0

        #
        # Create players
        #

        self.add_player(
            Player(
                "Player 1",
                (255, 0, 0)
            )
        )

        self.add_player(
            Player(
                "Player 2",
                (0, 255, 0)
            )
        )

        #
        # Initial game state
        #

        self.game_state = GAME_STATES[
            "CITY_SELECTION"
        ]

        #
        # Generate settlements
        #

        self.generate_infrastructure()

        #
        # Create volcanoes
        #

        print("creating volcanoes...")

        self.volcanoes = []

        for position in self.terrain.caldera_positions:

            volcano = Volcano(

                caldera_position=position,

                recharge_min=random.uniform(
                    0.003,
                    0.008
                ),

                recharge_max=random.uniform(
                    0.008,
                    0.015
                ),

                pressure_loss_max=random.uniform(
                    0.005,
                    0.015
                ),

                earthquake_multiplier=random.uniform(
                    30,
                    50
                ),

                earthquake_distance_scale=random.uniform(
                    150,
                    250
                ),

                fracture_damage_min=random.uniform(
                    0.005,
                    0.015
                ),

                fracture_damage_max=random.uniform(
                    0.04,
                    0.08
                ),

                fracture_healing=random.uniform(
                    0.92,
                    0.99
                )
            )

            self.volcanoes.append(volcano)

        #
        # Wind
        #

        self.wind_direction = random.uniform(
            0,
            2 * math.pi
        )

        self.wind_speed = random.uniform(
            0.5,
            2.0
        )

        self.wind_change_rate = 0.05
        self.wind_speed_change_rate = 0.05

        #
        # Hazard behaviour
        #

        self.lava_cooling_rate = 0.9
        self.lava_damage_factor = 100

        #
        # Lava behaviour
        #

        self.lava_length_factor = 0.15
        self.lava_spread_factor = 0.05
        self.lava_max_spread_chance = 0.4
        self.lava_momentum = 0.15
        self.lava_randomness_factor = 0.15
        self.lava_side_flow_strength = 0.2

        #
        # Ash behaviour
        #

        self.ash_settling_rate = 0.9
        self.ash_damage_factor = 5
        self.ash_length_factor = 0.25
        self.ash_spread_factor = 0.15

        #
        # Earthquake damage
        #

        self.earthquake_damage_distance_scale = 5
        self.earthquake_damage_factor = 0.01

        #
        # Active hazards
        #

        self.lava_cells = {}
        self.ash_cells = {}

        #
        # Event storage
        #

        self.earthquakes = []
        self.recent_earthquakes = []

        self.eruptions = []
        self.recent_eruptions = []

        #
        # History
        #

        self.pressure_history = []
        self.fracture_history = []

        #
        # Day counter
        #

        self.day = 0

    # =================================================
    # PLAYER
    # =================================================

    def add_player(self, player):

        self.players.append(player)

    def get_current_player(self):

        if (
            self.current_player_index < 0
            or
            self.current_player_index >= len(self.players)
        ):
            return None

        return self.players[
            self.current_player_index
        ]

    def select_player_from_structure(self, structure):

        if structure is None:
            return False

        if structure.owner is None:
            return False

        if structure.owner not in self.players:
            return False

        self.current_player_index = (
            self.players.index(structure.owner)
        )

        self.selected_structure = structure

        return True

    # =================================================
    # TERRAIN
    # =================================================

    def get_terrain_type(self, gx, gy):

        if not (
            0 <= gx < self.grid_width
            and
            0 <= gy < self.grid_height
        ):
            return None

        height = self.terrain.height_map[
            gy,
            gx
        ]

        if height < self.terrain.water_level:
            return "water"

        if height > self.terrain.mountain_level:
            return "mountains"

        if height < TERRAIN_TYPES[
            "plains"
        ]["level"]:
            return "plains"

        return "hills"

    # =================================================
    # BUILDING VALIDATION
    # =================================================

    def can_build(
        self,
        structure_type,
        x,
        y
    ):

        data = INFRASTRUCTURE_TYPES.get(
            structure_type
        )

        if data is None:
            return False

        #
        # Make sure coordinates are integers
        #

        try:
            x = int(x)
            y = int(y)
        except (TypeError, ValueError):
            return False

        width, height = data["size"]

        #
        # Map boundaries
        #

        if (
            x < 0
            or
            y < 0
            or
            x + width > self.grid_width
            or
            y + height > self.grid_height
        ):
            return False

        #
        # Terrain restrictions
        #

        allowed_terrain = data.get(
            "allowed_terrain",
            []
        )

        blocked_terrain = data.get(
            "blocked_terrain",
            []
        )

        #
        # Every cell in footprint must be valid
        #

        for gx in range(
            x,
            x + width
        ):

            for gy in range(
                y,
                y + height
            ):

                terrain_type = self.get_terrain_type(
                    gx,
                    gy
                )

                if terrain_type in blocked_terrain:
                    return False

                if (
                    allowed_terrain
                    and
                    terrain_type not in allowed_terrain
                ):
                    return False

                #
                # Existing infrastructure
                #

                if self.grid[gy][gx][
                    "structure"
                ] is not None:

                    return False

        return True

    # =================================================
    # PLACE INFRASTRUCTURE
    # =================================================

    def place_infrastructure(
        self,
        structure,
        x,
        y
    ):

        if not self.can_build(
            structure.type,
            x,
            y
        ):
            return False

        structure.position = (
            x,
            y
        )

        self.infrastructure.append(
            structure
        )

        width, height = structure.size

        for gx in range(
            x,
            x + width
        ):

            for gy in range(
                y,
                y + height
            ):

                self.grid[gy][gx][
                    "structure"
                ] = structure

        return True

    # =================================================
    # FIND RANDOM VALID LOCATION
    # =================================================

    def find_settlement_location(self, size):

        width, height = size

        max_attempts = 5000

        if (
            width > self.grid_width
            or
            height > self.grid_height
        ):
            return None

        for attempt in range(max_attempts):

            x = random.randint(
                0,
                self.grid_width - width
            )

            y = random.randint(
                0,
                self.grid_height - height
            )

            if self.can_build(
                "city",
                x,
                y
            ):
                return (
                    x,
                    y
                )

        print(
            "WARNING: Could not find valid settlement location"
        )

        return None

    # =================================================
    # GENERATE INITIAL INFRASTRUCTURE
    # =================================================

    def generate_infrastructure(self):

        cities = []

        print(
            "players",
            self.players
        )

        #
        # One extra city gives players a choice
        #

        for i in range(
            len(self.players) + 1
        ):

            cities.append(
                f"City {i + 1}"
            )

        print(
            "Generating cities:",
            cities
        )

        for name in cities:

            print(
                "Placing city:",
                name
            )

            data = INFRASTRUCTURE_TYPES[
                "city"
            ]

            location = self.find_settlement_location(
                data["size"]
            )

            if location is None:

                print(
                    "WARNING: Could not place city:",
                    name
                )

                continue

            x, y = location

            city = Infrastructure(

                name=name,

                structure_type="city",

                health=data["health"],

                colour=data["colour"],

                size=data["size"]

            )

            if not self.place_infrastructure(
                city,
                x,
                y
            ):

                print(
                    "WARNING: Failed to place city:",
                    name
                )

    # =================================================
    # CLAIM CITY
    # =================================================

    def claim_city(

        self,

        structure

    ):

        player = self.get_current_player()


        if player is None:

            return False


        if structure.owner:

            return False


        structure.assign_owner(

            player

        )


        player.city = structure

        player.start_location = structure.position


        #
        # Add income
        #

        player.income += INFRASTRUCTURE_TYPES[
            structure.type
        ]["income"]


        #
        # Move to next player
        #

        self.current_player_index += 1


        #
        # All players have selected
        #

        if self.current_player_index >= len(self.players):

            self.current_player_index = 0

            self.game_state = GAME_STATES[
                "PLAYING"
            ]

            print(
                "Starting game"
            )


        return True

    # =================================================
    # BUILD STRUCTURE
    # =================================================

    def build_structure(
        self,
        structure_type,
        x,
        y
    ):

        player = self.get_current_player()

        if player is None:
            return False

        data = INFRASTRUCTURE_TYPES.get(
            structure_type
        )

        if data is None:
            return False

        #
        # Building location
        #

        if not self.can_build(
            structure_type,
            x,
            y
        ):
            return False

        #
        # Cost
        #

        cost = data.get(
            "build_cost",
            0
        )

        if player.money < cost:
            return False

        #
        # Create structure
        #

        structure = Infrastructure(

            name=structure_type,

            structure_type=structure_type,

            health=data["health"],

            colour=data["colour"],

            size=data["size"]

        )

        #
        # Assign owner
        #

        structure.assign_owner(
            player
        )

        #
        # Place structure
        #

        if not self.place_infrastructure(
            structure,
            x,
            y
        ):
            return False

        #
        # Pay
        #

        player.money -= cost

        #
        # Add income
        #

        player.income += data.get(
            "income",
            0
        )

        return True

    # =================================================
    # WORLD STATE
    # =================================================

    def get_world_state_name(self):

        for name, value in GAME_STATES.items():

            if value == self.game_state:
                return name

        return None

    # =================================================
    # SIMULATION UPDATE
    # =================================================

    def update(self):

        self.day += 1

        self.update_wind()

        self.recent_earthquakes = []
        self.recent_eruptions = []

        eruption_occurred = False

        for volcano in self.volcanoes:

            volcano.update_pressure()

            earthquakes = (
                volcano.generate_earthquakes()
            )

            volcano.update_fracture(
                earthquakes
            )

            self.recent_earthquakes.extend(
                earthquakes
            )

            eruption = volcano.check_eruption()

            if eruption:

                eruption_occurred = True

                eruption_event = {

                    "day":
                    self.day,

                    "type":
                    volcano.eruption_type,

                    "location":
                    volcano.eruption_location,

                    "lava_intensity":
                    volcano.lava_intensity,

                    "ash_intensity":
                    volcano.ash_intensity

                }

                self.recent_eruptions.append(
                    eruption_event
                )

                self.generate_ash_plume(
                    eruption_event
                )

                self.generate_lava_flow(
                    eruption_event
                )

                volcano.release_pressure()

                print(
                    eruption_event["type"]
                )

        self.eruptions.extend(
            self.recent_eruptions
        )

        self.earthquakes.extend(
            self.recent_earthquakes
        )

        self.pressure_history.append(
            [
                volcano.pressure
                for volcano in self.volcanoes
            ]
        )

        self.fracture_history.append(
            [
                volcano.fracture
                for volcano in self.volcanoes
            ]
        )

        self.update_infrastructure_damage()

        self.update_economy()

        self.update_hazards()

        return {

            "earthquakes":
            self.recent_earthquakes,

            "eruption":
            eruption_occurred

        }

    # =================================================
    # EARTHQUAKE SENSING
    # =================================================

    def get_nearby_earthquakes(
        self,
        structure
    ):

        radius = INFRASTRUCTURE_TYPES[
            structure.type
        ].get(
            "earthquake_detection_radius",
            0
        )

        sx, sy = structure.position

        nearby = []

        for earthquake in self.recent_earthquakes:

            ex, ey = earthquake[
                "location"
            ]

            ex = int(
                ex /
                self.terrain.cell_size
            )

            ey = int(
                ey /
                self.terrain.cell_size
            )

            distance = self.distance(
                (sx, sy),
                (ex, ey)
            )

            if distance <= radius:

                nearby.append({

                    "magnitude":
                    earthquake["magnitude"],

                    "location":
                    earthquake["location"],

                    "distance":
                    distance

                })

        return nearby

    def get_player_earthquakes(
        self,
        players
    ):

        detected = []

        for player in players:

            for structure in self.infrastructure:

                if structure.owner != player:
                    continue

                if structure.destroyed:
                    continue

                earthquakes = (
                    self.get_nearby_earthquakes(
                        structure
                    )
                )

                for earthquake in earthquakes:

                    if earthquake not in detected:

                        detected.append(
                            earthquake
                        )

        return detected

    # =================================================
    # LAVA FLOW
    # =================================================

    def generate_lava_flow(
        self,
        eruption
    ):

        x, y = eruption[
            "location"
        ]

        gx = int(
            x /
            self.terrain.cell_size
        )

        gy = int(
            y /
            self.terrain.cell_size
        )

        start = (
            gx,
            gy
        )

        intensity = eruption[
            "lava_intensity"
        ]

        length = int(
            intensity *
            self.lava_length_factor
        )

        spread_chance = min(

            self.lava_max_spread_chance,

            intensity *
            self.lava_spread_factor /
            100

        )

        randomness = min(

            self.lava_randomness_factor,

            intensity / 100

        )

        current = start
        previous_direction = None

        for i in range(length):

            x, y = current

            if not (
                0 <= x < self.grid_width
                and
                0 <= y < self.grid_height
            ):
                break

            lava_strength = max(

                0,

                1 -
                (
                    i /
                    max(length, 1)
                )

            )

            self.lava_cells[
                (x, y)
            ] = lava_strength

            self.grid[y][x][
                "lava"
            ] = lava_strength

            neighbours = [

                (x + 1, y),
                (x - 1, y),
                (x, y + 1),
                (x, y - 1)

            ]

            neighbours = [

                p
                for p in neighbours
                if (
                    0 <= p[0] < self.grid_width
                    and
                    0 <= p[1] < self.grid_height
                )

            ]

            if not neighbours:
                break

            #
            # Side spreading
            #

            if random.random() < spread_chance:

                side = random.choice(
                    neighbours
                )

                sx, sy = side

                if self.grid[sy][sx][
                    "lava"
                ] < lava_strength:

                    side_strength = (
                        lava_strength *
                        self.lava_side_flow_strength
                    )

                    self.lava_cells[
                        side
                    ] = side_strength

                    self.grid[sy][sx][
                        "lava"
                    ] = side_strength

            #
            # Direction scoring
            #

            def flow_score(p):

                px, py = p

                score = self.terrain.height_map[
                    py,
                    px
                ]

                if previous_direction:

                    dx = px - x
                    dy = py - y

                    if (
                        dx,
                        dy
                    ) == previous_direction:

                        score -= self.lava_momentum

                score += random.uniform(
                    0,
                    randomness
                )

                return score

            #
            # Occasionally ignore terrain
            #

            if random.random() < randomness:

                next_cell = random.choice(
                    neighbours
                )

            else:

                next_cell = min(
                    neighbours,
                    key=flow_score
                )

            previous_direction = (

                next_cell[0] - x,
                next_cell[1] - y

            )

            current = next_cell

    # =================================================
    # ASH PLUME
    # =================================================

    def generate_ash_plume(
        self,
        eruption
    ):

        x, y = eruption[
            "location"
        ]

        gx = int(
            x /
            self.terrain.cell_size
        )

        gy = int(
            y /
            self.terrain.cell_size
        )

        length = int(

            eruption["ash_intensity"] *
            self.wind_speed *
            self.ash_length_factor

        )

        dx = math.cos(
            self.wind_direction
        )

        dy = math.sin(
            self.wind_direction
        )

        for i in range(length):

            px = gx + dx * i
            py = gy - dy * i

            spread = int(
                i *
                self.ash_spread_factor
            )

            for sx in range(
                -spread,
                spread + 1
            ):

                for sy in range(
                    -spread,
                    spread + 1
                ):

                    cx = int(
                        px + sx
                    )

                    cy = int(
                        py + sy
                    )

                    if not (
                        0 <= cx < self.grid_width
                        and
                        0 <= cy < self.grid_height
                    ):
                        continue

                    distance = math.sqrt(
                        sx * sx +
                        sy * sy
                    )

                    if distance > spread + 1:
                        continue

                    strength = (

                        1 -
                        i /
                        max(length, 1)

                    )

                    strength *= (

                        1 -
                        distance /
                        max(spread + 1, 1)

                    )

                    if strength <= 0:
                        continue

                    self.ash_cells[
                        (cx, cy)
                    ] = (

                        self.ash_cells.get(
                            (cx, cy),
                            0
                        )

                        +

                        strength

                    )

                    self.grid[cy][cx][
                        "ash"
                    ] = self.ash_cells[
                        (cx, cy)
                    ]

    # =================================================
    # HAZARD UPDATE
    # =================================================

    def update_hazards(self):

        #
        # Lava
        #

        for position in list(
            self.lava_cells.keys()
        ):

            intensity = self.lava_cells[
                position
            ]

            intensity *= (
                self.lava_cooling_rate
            )

            x, y = position

            if intensity < 0.01:

                del self.lava_cells[
                    position
                ]

                self.grid[y][x][
                    "lava"
                ] = 0

            else:

                self.lava_cells[
                    position
                ] = intensity

                self.grid[y][x][
                    "lava"
                ] = intensity

        #
        # Ash
        #

        for position in list(
            self.ash_cells.keys()
        ):

            intensity = self.ash_cells[
                position
            ]

            intensity *= (
                self.ash_settling_rate
            )

            x, y = position

            if intensity < 0.01:

                del self.ash_cells[
                    position
                ]

                self.grid[y][x][
                    "ash"
                ] = 0

            else:

                self.ash_cells[
                    position
                ] = intensity

                self.grid[y][x][
                    "ash"
                ] = intensity

    # =================================================
    # WIND
    # =================================================

    def update_wind(self):

        self.wind_direction += random.uniform(

            -self.wind_change_rate,
            self.wind_change_rate

        )

        self.wind_speed += random.uniform(

            -self.wind_speed_change_rate,
            self.wind_speed_change_rate

        )

        self.wind_speed = max(

            0.1,

            min(
                self.wind_speed,
                3.0
            )

        )

    # =================================================
    # INFRASTRUCTURE DAMAGE
    # =================================================

    def update_infrastructure_damage(self):

        for structure in self.infrastructure:

            if structure.destroyed:
                continue

            damage = 0

            x, y = structure.position

            width, height = structure.size

            for gx in range(
                x,
                x + width
            ):

                for gy in range(
                    y,
                    y + height
                ):

                    if not (
                        0 <= gx < self.grid_width
                        and
                        0 <= gy < self.grid_height
                    ):
                        continue

                    damage += self.get_lava_damage(
                        (gx, gy)
                    )

                    damage += self.get_ash_damage(
                        (gx, gy)
                    )

                    damage += self.get_earthquake_damage(
                        (gx, gy)
                    )

            if damage > 0:

                structure.apply_damage(
                    damage
                )

    # =================================================
    # LAVA DAMAGE
    # =================================================

    def get_lava_damage(
        self,
        position
    ):

        gx, gy = position

        if not (
            0 <= gx < self.grid_width
            and
            0 <= gy < self.grid_height
        ):
            return 0

        return (
            self.grid[gy][gx]["lava"]
            *
            self.lava_damage_factor
        )

    # =================================================
    # ASH DAMAGE
    # =================================================

    def get_ash_damage(
        self,
        position
    ):

        gx, gy = position

        if not (
            0 <= gx < self.grid_width
            and
            0 <= gy < self.grid_height
        ):
            return 0

        return (
            self.grid[gy][gx]["ash"]
            *
            self.ash_damage_factor
        )

    # =================================================
    # EARTHQUAKE DAMAGE
    # =================================================

    def get_earthquake_damage(
        self,
        position
    ):

        gx, gy = position

        if not (
            0 <= gx < self.grid_width
            and
            0 <= gy < self.grid_height
        ):
            return 0

        damage = 0

        for earthquake in self.recent_earthquakes:

            ex, ey = earthquake[
                "location"
            ]

            ex = int(
                ex /
                self.terrain.cell_size
            )

            ey = int(
                ey /
                self.terrain.cell_size
            )

            distance = self.distance(

                (gx, gy),

                (ex, ey)

            )

            magnitude = earthquake[
                "magnitude"
            ]

            damage += (

                magnitude ** 2

                *

                math.exp(

                    -distance /
                    self.earthquake_damage_distance_scale

                )

                *

                self.earthquake_damage_factor

            )

        return damage

    # =================================================
    # ECONOMY
    # =================================================

    def update_economy(self):

        for player in self.players:

            player.money += player.income

    # =================================================
    # DISTANCE
    # =================================================

    def distance(
        self,
        point1,
        point2
    ):

        x1, y1 = point1
        x2, y2 = point2

        return math.sqrt(

            (x2 - x1) ** 2

            +

            (y2 - y1) ** 2

        )

    # =================================================
    # VECTOR TO COMPASS
    # =================================================

    def vector_to_compass(
        self,
        angle
    ):

        angle = math.degrees(
            angle
        )

        angle %= 360

        directions = [

            "E",
            "NE",
            "N",
            "NW",
            "W",
            "SW",
            "S",
            "SE"

        ]

        index = round(
            angle / 45
        ) % 8

        return directions[
            index
        ]