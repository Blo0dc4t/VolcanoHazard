import random
import noise
import numpy as np
from constants import TERRAIN_TYPES


class Terrain:


    def __init__(

        self,

        width,

        height,

        cell_size=4,

        scale=50,

        octaves=4,

        persistence=0.5,

        lacunarity=2.0,

        seed=None,

        caldera_num=1,

        caldera_min_distance=10

    ):


        self.width = width
        self.height = height

        self.cell_size = cell_size


        #
        # Grid dimensions
        #

        self.grid_width = width // cell_size
        self.grid_height = height // cell_size


        self.scale = scale

        self.octaves = octaves

        self.persistence = persistence

        self.lacunarity = lacunarity

        self.caldera_num = caldera_num

        self.caldera_min_distance = caldera_min_distance


        self.water_level = TERRAIN_TYPES["water"]["level"]

        self.mountain_level = TERRAIN_TYPES["mountains"]["level"]


        if seed is None:

            seed = random.randint(
                0,
                255
            )


        self.seed = seed



        self.height_map = np.zeros(

            (

                self.grid_height,

                self.grid_width

            )

        )


        self.generate()


        self.highest_point = self.find_highest_point()

        self.caldera_positions = []

        self.caldera_positions = []

        for _ in range(caldera_num):

            position = self.choose_caldera_position()

            if position is not None:

                self.caldera_positions.append(
                    position
                )


    # =================================================
    # GENERATE TERRAIN
    # =================================================

    def generate(self):


        minimum = 999

        maximum = -999



        for y in range(self.grid_height):

            for x in range(self.grid_width):


                value = noise.pnoise2(

                    (x + self.seed) / self.scale,

                    (y + self.seed) / self.scale,

                    octaves=self.octaves,

                    persistence=self.persistence,

                    lacunarity=self.lacunarity

                )


                self.height_map[y,x] = value


                minimum = min(
                    minimum,
                    value
                )


                maximum = max(
                    maximum,
                    value
                )



        self.height_map = (

            self.height_map - minimum

        ) / (

            maximum - minimum

        )


    def is_water(self, position):
        x,y = position


        gx = int(

            x / self.cell_size

        )

        gy = int(

            y / self.cell_size

        )


        gx = max(
            0,
            min(
                self.grid_width-1,
                gx
            )
        )

        gy = max(
            0,
            min(
                self.grid_height-1,
                gy
            )
        )


        return self.height_map[gy,gx] < self.water_level

    def is_mountain(self, position):
        x,y = position


        gx = int(

            x / self.cell_size

        )

        gy = int(

            y / self.cell_size

        )


        gx = max(
            0,
            min(
                self.grid_width-1,
                gx
            )
        )

        gy = max(
            0,
            min(
                self.grid_height-1,
                gy
            )
        )


        return self.height_map[gy,gx] > self.mountain_level



    # =================================================
    # HIGHEST POINT
    # =================================================

    def find_highest_point(self):


        y,x = np.unravel_index(

            np.argmax(self.height_map),

            self.height_map.shape

        )


        return (

            x,
            y

        )



    # =================================================
    # CALDERA
    # =================================================

    def choose_caldera_position(self, centre_position=None):


        if centre_position is None:

            centre_x = self.grid_width // 2
            centre_y = self.grid_height // 2

        else:

            centre_x, centre_y = centre_position



        #
        # Search radius around centre
        #

        max_distance = min(
            self.grid_width,
            self.grid_height
        ) * 0.5



        candidates = []
        fallback_candidates = []



        for y in range(1, self.grid_height - 1):

            for x in range(1, self.grid_width - 1):


                #
                # Distance from preferred centre
                #

                distance = (
                    (x - centre_x) ** 2
                    +
                    (y - centre_y) ** 2
                ) ** 0.5


                if distance > max_distance:

                    continue



                #
                # Ignore water
                #

                if self.is_water(
                    (
                        x * self.cell_size,
                        y * self.cell_size
                    )
                ):

                    continue



                height = self.height_map[y][x]



                #
                # Check local maximum
                #

                neighbours = [

                    self.height_map[y-1][x],
                    self.height_map[y+1][x],
                    self.height_map[y][x-1],
                    self.height_map[y][x+1]

                ]


                is_local_maximum = all(
                    height > neighbour
                    for neighbour in neighbours
                )



                #
                # Check distance from
                # existing calderas
                #

                too_close = False


                for existing in self.caldera_positions:


                    existing_x = (

                        existing[0] /

                        self.cell_size

                    )


                    existing_y = (

                        existing[1] /

                        self.cell_size

                    )


                    caldera_distance = (

                        (
                            x - existing_x
                        ) ** 2

                        +

                        (
                            y - existing_y
                        ) ** 2

                    ) ** 0.5


                    if (

                        caldera_distance

                        <

                        self.caldera_min_distance

                    ):

                        too_close = True

                        break



                if too_close:

                    continue



                fallback_candidates.append(
                    (
                        height,
                        x,
                        y
                    )
                )

                if is_local_maximum:
                    candidates.append(
                        (
                            height,
                            x,
                            y
                        )
                    )



        #
        # No suitable local maximum
        #

        if not candidates:
            candidates = fallback_candidates

        if not candidates:

            print(
                "No suitable caldera location found"
            )

            return None



        candidates.sort(
            reverse=True
        )

        _, x, y = candidates[0]


        return (

            x * self.cell_size,

            y * self.cell_size

        )

    # =================================================
    # HEIGHT QUERY
    # =================================================

    def get_height(self, position):


        x,y = position


        gx = int(

            x / self.cell_size

        )

        gy = int(

            y / self.cell_size

        )


        gx = max(
            0,
            min(
                self.grid_width-1,
                gx
            )
        )

        gy = max(
            0,
            min(
                self.grid_height-1,
                gy
            )
        )


        return self.height_map[gy,gx]