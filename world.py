import random
import math

from volcano import Volcano
from terrain import Terrain
from infrastructure import Infrastructure, INFRASTRUCTURE_TYPES



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

        #
        # Example infrastructure
        #

        city = Infrastructure(

            name="Mount Valley City",

            structure_type="city",

            health=INFRASTRUCTURE_TYPES["city"]["health"],

            colour=INFRASTRUCTURE_TYPES["city"]["colour"],

            size=INFRASTRUCTURE_TYPES["city"]["size"]

        )


        self.place_infrastructure(

            city,

            20,

            20

        )


        #
        # Create volcano
        #

        print("creating volcano...")


        self.volcano = Volcano(

            caldera_position=self.terrain.caldera_position,

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



        self.ash_settling_rate = 0.98

        self.ash_length_factor = 0.25

        self.ash_spread_factor = 0.15

        



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
    # SIMULATION UPDATE
    # =================================================

    def update(self):


        self.day += 1


        # 
        # Update wind
        #
        self.update_wind()


        #
        # Volcano evolution
        #

        self.volcano.update_pressure()



        earthquakes = self.volcano.generate_earthquakes()



        self.volcano.update_fracture(

            earthquakes

        )



        #
        # Store earthquakes
        #

        self.earthquakes.extend(

            earthquakes

        )


        self.recent_earthquakes = earthquakes



        #
        # Store history
        #

        self.pressure_history.append(

            self.volcano.pressure

        )


        self.fracture_history.append(

            self.volcano.fracture

        )



        #
        # Check eruption
        #

        eruption = self.volcano.check_eruption()



        if eruption:


            eruption_event = {


                "day":

                self.day,


                "type":

                self.volcano.eruption_type,


                "location":

                self.volcano.eruption_location,


                "lava_intensity":

                self.volcano.lava_intensity,


                "ash_intensity":

                self.volcano.ash_intensity

            }



            self.eruptions.append(

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
            # Reset volcano
            #

            self.volcano.release_pressure()



            print(

                eruption_event["type"]

            )



        #
        # Apply hazards
        #

        self.update_infrastructure_damage()



        #
        # Reduce old hazards
        #

        self.update_hazards()



        return {


            "earthquakes":

            earthquakes,


            "eruption":

            eruption

        }

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



            x,y = structure.position


            width,height = structure.size



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



                    tile = self.grid[gy][gx]



                    #
                    # Lava is much more damaging
                    #

                    damage += (

                        tile["lava"]

                        *

                        100

                    )



                    #
                    # Ash damages more slowly
                    #

                    damage += (

                        tile["ash"]

                        *

                        5

                    )



            if damage > 0:


                structure.apply_damage(

                    damage

                )




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


    # =================================================
    # HAZARD QUERY FUNCTIONS
    # =================================================

    def get_lava_damage(

        self,

        position

    ):


        x,y = position



        gx = int(

            x /

            self.terrain.cell_size

        )


        gy = int(

            y /

            self.terrain.cell_size

        )



        if not (

            0 <= gx < self.grid_width

            and

            0 <= gy < self.grid_height

        ):

            return 0



        return (

            self.grid[gy][gx]["lava"]

            *

            100

        )




    def get_ash_damage(

        self,

        position

    ):


        x,y = position



        gx = int(

            x /

            self.terrain.cell_size

        )


        gy = int(

            y /

            self.terrain.cell_size

        )



        if not (

            0 <= gx < self.grid_width

            and

            0 <= gy < self.grid_height

        ):

            return 0



        return (

            self.grid[gy][gx]["ash"]

            *

            5

        )