import random
import math

from volcano import Volcano
from terrain import Terrain
from infrastructure import Infrastructure, INFRASTRUCTURE_TYPES
from player import Player
from constants import GAME_STATES



class World:


    def __init__(

        self,

        width=1000,

        height=1000

    ):


        #
        # World dimensions
        #
        # Continuous coordinates
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

            cell_size=20

        )


        self.grid_width = self.terrain.grid_width

        self.grid_height = self.terrain.grid_height



        #
        # World grid
        #
        # Each cell stores:
        #
        # structure:
        #     infrastructure object
        #
        # lava:
        #     lava intensity
        #
        # ash:
        #     ash intensity
        #

        self.grid = [

            [

                {

                    "structure":None,

                    "lava":0.0,

                    "ash":0.0

                }

                for x in range(self.grid_width)

            ]

            for y in range(self.grid_height)

        ]


        #
        # Infrastructure objects
        #

        self.infrastructure = []

        self.selected_structure = None


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

                (255,0,0)

            )

        )



        self.add_player(

            Player(

                "Player 2",

                (0,255,0)

            )

        )


        #
        # Player selection state
        #

        self.game_state = GAME_STATES["CITY_SELECTION"]

        #
        # Generate settlements
        #

        self.generate_infrastructure()


        #
        # Create volcano
        #

        print("creating volcanoes...")

        self.volcanoes = []

        for position in self.terrain.caldera_positions:

            self.volcanoes.append(
                Volcano(
                    caldera_position=position,
                )
            )



        #
        # Wind
        #

        self.wind_direction = random.uniform(

            0,

            2*math.pi

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

        self.lava_cooling_rate = 0.98

        # Lava damage factor controls how much damage lava does to infrastructure

        self.lava_damage_factor = 100

        # Lava behaviour tuning

        self.lava_length_factor = 0.15

        # How much lava branches sideways
        self.lava_spread_factor = 0.05

        # Maximum sideways branch probability
        self.lava_max_spread_chance = 0.4

        # How much lava follows previous direction
        self.lava_momentum = 0.15

        # How unpredictable lava paths are
        self.lava_randomness_factor = 0.15

        # How much weaker side flows are
        self.lava_side_flow_strength = 0.2


        # Ash behaviour tuning

        self.ash_settling_rate = 0.98

        self.ash_damage_factor = 5

        self.ash_length_factor = 0.25

        self.ash_spread_factor = 0.15


        # earthquake behaviour tuning

        self.earthquake_damage_distance_scale = 5

        self.earthquake_damage_factor = 0.01



        #
        # Active hazard cells
        #
        # Dictionaries allow:
        #
        # position -> intensity
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


    def handle_structure_click(self, structure):


        if structure is None:

            return



        #
        # Always select structure
        #

        self.selected_structure = structure



        #
        # City selection phase
        #

        if self.game_state == GAME_STATES["CITY_SELECTION"]:


            self.claim_city(structure)



            #
            # Check if all players have chosen
            #

            if self.current_player_index >= len(self.players):

                self.game_state = GAME_STATES["PLAYING"]

                print(
                    "Starting game"
                )


    def get_current_player(self):


        if self.current_player_index >= len(self.players):

            return None


        return self.players[
            self.current_player_index
        ]


    # =================================================
    # SIMULATION UPDATE
    # =================================================

    def update(self):


        self.day += 1


        #
        # Update wind
        #

        self.update_wind()



        self.recent_earthquakes = []

        self.recent_eruptions = []

        eruption_occurred = False



        #
        # Update all volcanoes
        #

        for volcano in self.volcanoes:


            #
            # Volcano evolution
            #

            volcano.update_pressure()



            earthquakes = volcano.generate_earthquakes()



            volcano.update_fracture(

                earthquakes

            )


            #
            # Store earthquakes
            #

            self.recent_earthquakes.extend(

                earthquakes

            )



            #
            # Check eruption
            #

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



                #
                # Create hazards
                #

                self.generate_ash_plume(

                    eruption_event

                )


                self.generate_lava_flow(

                    eruption_event

                )



                #
                # Reset this volcano
                #

                volcano.release_pressure()



                print(

                    eruption_event["type"]

                )

        # 
        # Store eruptions
        # 

        self.eruptions.extend(
            self.recent_eruptions
        )


        #
        # Store earthquakes after all volcanoes update
        #

        self.earthquakes.extend(

            self.recent_earthquakes

        )


        #
        # Store history
        # 
        # (currently only tracks one volcano)
        #

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



        #
        # Apply hazards
        #

        self.update_infrastructure_damage()


        # 
        # Update economy
        # 

        self.update_economy()


        #
        # Reduce old hazards
        #

        self.update_hazards()
        

    # =================================================
    # PLACE INFRASTRUCTURE
    # =================================================

    def place_infrastructure(

        self,

        structure,

        x,

        y

    ):


        #
        # Store position
        #

        structure.position = (

            x,

            y

        )



        #
        # Add to world list
        #

        self.infrastructure.append(

            structure

        )



        #
        # Occupy grid cells
        #

        width,height = structure.size



        for gx in range(

            x,

            x + width

        ):


            for gy in range(

                y,

                y + height

            ):


                if (

                    0 <= gx < self.grid_width

                    and

                    0 <= gy < self.grid_height

                ):


                    self.grid[gy][gx]["structure"] = structure


    def generate_infrastructure(self):

        cities = []

        print("players", self.players)
        for i in range(len(self.players)+1):

            cities.append(
                f"City {i+1}"
            )
        print("Generating cities:", cities)

        for name in cities:

            print("Placing city: {}".format(name))
            x,y = self.find_settlement_location()
            print("Settlement location: ({},{})".format(x,y))



            city = Infrastructure(

                name=name,

                structure_type="city",

                health=INFRASTRUCTURE_TYPES["city"]["health"],

                colour=INFRASTRUCTURE_TYPES["city"]["colour"],

                size=INFRASTRUCTURE_TYPES["city"]["size"]

            )



            self.place_infrastructure(

                city,

                x,

                y

            )


    def add_player(self, player):

        self.players.append(player)



    def find_settlement_location(self):

        water_cells = 0
        mountain_cells = 0

        max_attempts = 5000


        for attempt in range(max_attempts):


            x = random.randint(
                0,
                self.grid_width - 1
            )


            y = random.randint(
                0,
                self.grid_height - 1
            )



            #
            # Check terrain
            #

            if self.terrain.is_water(
                (
                    x * self.terrain.cell_size,
                    y * self.terrain.cell_size
                )
            ):
                water_cells += 1
                continue


            if self.terrain.is_mountain(
                (
                    x * self.terrain.cell_size,
                    y * self.terrain.cell_size
                )
            ):
                mountain_cells += 1
                continue



            #
            # Check existing infrastructure
            #

            occupied = False


            for structure in self.infrastructure:


                sx, sy = structure.position


                if (
                    abs(x - sx) < structure.size[0]
                    and
                    abs(y - sy) < structure.size[1]
                ):

                    occupied = True

                    break



            if occupied:

                continue



            return x, y


        print("Water rejected:", water_cells)
        print("Mountain rejected:", mountain_cells)

        print(
            "WARNING: Could not find valid settlement location"
        )


        return (
            self.grid_width // 2,
            self.grid_height // 2
        )
    

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

        player.income += INFRASTRUCTURE_TYPES[
            structure.type
        ]["income"]



        #
        # Move to next player
        #

        self.current_player_index += 1



        return True


    # =================================================
    # GENERATE LAVA FLOW
    # =================================================

    def generate_lava_flow(

        self,

        eruption

    ):


        x, y = eruption["location"]


        #
        # Convert world position
        # to terrain grid
        #

        gx = int(

            x / self.terrain.cell_size

        )


        gy = int(

            y / self.terrain.cell_size

        )


        start = (

            gx,

            gy

        )


        #
        # Eruption controls
        #

        intensity = eruption["lava_intensity"]


        length = int(

            intensity *

            self.lava_length_factor

        )


        #
        # Stronger eruptions:
        # - wider
        # - more random
        #

        spread_chance = min(
            self.lava_max_spread_chance,
            intensity * self.lava_spread_factor / 100
        )


        randomness = min(
            self.lava_randomness_factor,
            intensity / 100
        )


        #
        # Current flow position
        #

        current = start


        #
        # Previous movement direction
        # gives lava momentum
        #

        previous_direction = None



        for i in range(length):


            x, y = current


            if not (

                0 <= x < self.grid_width

                and

                0 <= y < self.grid_height

            ):

                break



            #
            # Lava weakens with distance
            #

            lava_strength = max(

                0,

                1 -

                (

                    i / max(length, 1)

                )

            )



            #
            # Store lava
            #

            self.lava_cells[(x,y)] = lava_strength


            self.grid[y][x]["lava"] = lava_strength



            #
            # Get neighbouring cells
            #

            neighbours = [

                (x+1,y),

                (x-1,y),

                (x,y+1),

                (x,y-1)

            ]


            neighbours = [

                p for p in neighbours

                if

                0 <= p[0] < self.grid_width

                and

                0 <= p[1] < self.grid_height

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


                if self.grid[sy][sx]["lava"] < lava_strength:


                    self.lava_cells[side] = lava_strength * self.lava_side_flow_strength


                    self.grid[sy][sx]["lava"] = lava_strength * self.lava_side_flow_strength



            #
            # Choose next direction
            #

            def flow_score(p):


                px, py = p


                #
                # Lower terrain is preferred
                #

                score = self.terrain.height_map[

                    py,

                    px

                ]



                #
                # Momentum:
                # favour continuing direction
                #

                if previous_direction:


                    dx = px - x

                    dy = py - y


                    if (

                        dx,

                        dy

                    ) == previous_direction:


                        score -= self.lava_momentum



                #
                # Small randomness
                #

                score += random.uniform(

                    0,

                    randomness

                )


                return score



            #
            # Occasionally ignore terrain
            # completely
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



            #
            # Save movement direction
            #

            previous_direction = (

                next_cell[0] - x,

                next_cell[1] - y

            )


            current = next_cell

    # =================================================
    # GENERATE ASH PLUME
    # =================================================

    def generate_ash_plume(

        self,

        eruption

    ):


        x,y = eruption["location"]



        #
        # Convert to grid
        #

        gx = int(

            x / self.terrain.cell_size

        )


        gy = int(

            y / self.terrain.cell_size

        )



        #
        # Plume length controlled by ash strength
        #

        length = int(

            eruption["ash_intensity"]

            *

            self.wind_speed

            *

            self.ash_length_factor

        )



        #
        # Wind vector
        #

        dx = math.cos(

            self.wind_direction

        )


        dy = math.sin(

            self.wind_direction

        )



        for i in range(length):


            #
            # Position along wind direction
            #

            px = gx + dx*i

            py = gy - dy*i



            #
            # Plume widens with distance
            #

            spread = int(

                i * self.ash_spread_factor

            )



            for sx in range(

                -spread,

                spread+1

            ):


                for sy in range(

                    -spread,

                    spread+1

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

                        sx*sx +

                        sy*sy

                    )



                    if distance > spread+1:

                        continue



                    #
                    # Ash decreases with distance
                    #

                    strength = (

                        1 -

                        i / max(length,1)

                    )



                    strength *= (

                        1 -

                        distance /

                        max(spread+1,1)

                    )



                    if strength <= 0:

                        continue



                    #
                    # Add ash
                    #

                    self.ash_cells[(cx,cy)] = (

                        self.ash_cells.get(

                            (cx,cy),

                            0

                        )

                        +

                        strength

                    )



                    self.grid[cy][cx]["ash"] = (

                        self.ash_cells[(cx,cy)]

                    )

    # =================================================
    # UPDATE HAZARDS
    # =================================================

    def update_hazards(self):


        #
        # Lava cooling
        #

        for position in list(self.lava_cells.keys()):


            intensity = self.lava_cells[position]



            intensity *= self.lava_cooling_rate



            x,y = position



            if intensity < 0.01:


                del self.lava_cells[position]


                self.grid[y][x]["lava"] = 0



            else:


                self.lava_cells[position] = intensity


                self.grid[y][x]["lava"] = intensity



        #
        # Ash settling
        #

        for position in list(self.ash_cells.keys()):


            intensity = self.ash_cells[position]



            intensity *= self.ash_settling_rate



            x,y = position



            if intensity < 0.01:


                del self.ash_cells[position]


                self.grid[y][x]["ash"] = 0



            else:


                self.ash_cells[position] = intensity


                self.grid[y][x]["ash"] = intensity


    # ================================================
    # Wind Update
    # ================================================
    def update_wind(self):


        #
        # Slowly rotate wind direction
        #

        self.wind_direction += random.uniform(
            -self.wind_change_rate,
            self.wind_change_rate
        )


        #
        # Slowly vary wind speed
        #

        self.wind_speed += random.uniform(
            -self.wind_speed_change_rate,
            self.wind_speed_change_rate
        )


        #
        # Keep values sensible
        #

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


        #
        # Check every infrastructure object
        #

        for structure in self.infrastructure:


            damage = 0



            x, y = structure.position


            width, height = structure.size



            #
            # Sum hazards over occupied tiles
            #

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



                    #
                    # Add hazard damage
                    #

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
    # HAZARD QUERY FUNCTIONS
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


            ex, ey = earthquake["location"]


            #
            # Convert earthquake world coordinates
            # into grid coordinates
            #

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



            magnitude = earthquake["magnitude"]



            #
            # Magnitude squared gives stronger
            # effect from large earthquakes
            #

            damage += (

                magnitude ** 2

                *

                math.exp(

                    -distance / self.earthquake_damage_distance_scale

                )

                *

                self.earthquake_damage_factor

            )


        return damage


    def update_economy(self):

        for player in self.players:

            player.money += player.income


    # =================================================
    # DISTANCE FUNCTION
    # =================================================

    def distance(

        self,

        point1,

        point2

    ):


        x1,y1 = point1

        x2,y2 = point2



        return math.sqrt(

            (

                x2-x1

            )**2

            +

            (

                y2-y1

            )**2

        )

    # =================================================
    # VECTOR TO COMPASS DIRECTION
    # =================================================

    def vector_to_compass(self, angle):
        angle = math.degrees(angle)
        angle = angle % 360

        # Convert so:
        # 0° = East, 90° = North
        angle = (angle + 360) % 360

        directions = [
            "E", "NE", "N", "NW",
            "W", "SW", "S", "SE"
        ]

        index = round(angle / 45) % 8
        return directions[index]


    