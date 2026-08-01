import random
import noise
import numpy as np


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

        water_level=0.35,

        mountain_level=0.75

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


        self.water_level = water_level

        self.mountain_level = mountain_level


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

        self.caldera_position = self.choose_caldera_position()



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

    def choose_caldera_position(self):


        x,y = self.highest_point


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