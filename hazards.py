import math

import constants



class HazardManager:


    def __init__(self, game_map):


        self.game_map = game_map



    # =====================================================
    # Clear hazard layers
    # =====================================================

    def clear(self):


        for row in self.game_map.tiles:


            for tile in row:


                tile.hazards["earthquake"] = 0

                tile.hazards["lava"] = 0

                tile.hazards["ash"] = 0



    # =====================================================
    # Earthquake hazard
    # =====================================================

    def add_earthquake(self, quake):


        radius = int(

            quake.magnitude *

            constants.EARTHQUAKE_RADIUS_SCALE

        )



        for y in range(

            max(0, quake.y-radius),

            min(constants.ROWS, quake.y+radius+1)

        ):


            for x in range(

                max(0, quake.x-radius),

                min(constants.COLS, quake.x+radius+1)

            ):



                distance = math.sqrt(

                    (x-quake.x)**2 +

                    (y-quake.y)**2

                )



                if distance <= radius:


                    intensity = (

                        quake.magnitude *

                        (1-distance/radius)

                    )



                    self.game_map.tiles[y][x].hazards["earthquake"] += intensity



    # =====================================================
    # Lava flow
    # =====================================================

    def add_lava(

        self,

        x,

        y,

        intensity

    ):


        visited = set()



        distance = int(

            intensity /

            constants.LAVA_DISTANCE_SCALE

        )



        self.flow_lava(

            x,

            y,

            intensity,

            distance,

            visited

        )



    def flow_lava(

        self,

        x,

        y,

        intensity,

        remaining,

        visited

    ):



        #
        # Stop conditions
        #

        if remaining <= 0:

            return



        if (x,y) in visited:

            return



        if x < 0 or x >= constants.COLS:

            return


        if y < 0 or y >= constants.ROWS:

            return



        visited.add(

            (x,y)

        )



        tile = self.game_map.tiles[y][x]



        tile.hazards["lava"] = max(

            tile.hazards["lava"],

            intensity

        )



        current_height = tile.elevation



        neighbours = [

            (x+1,y),

            (x-1,y),

            (x,y+1),

            (x,y-1)

        ]



        for nx,ny in neighbours:



            if nx < 0 or nx >= constants.COLS:

                continue


            if ny < 0 or ny >= constants.ROWS:

                continue



            next_tile = self.game_map.tiles[ny][nx]



            #
            # Lava can only move:
            #
            # downhill
            # or almost flat
            #

            if next_tile.elevation <= current_height + 0.02:


                self.flow_lava(

                    nx,

                    ny,

                    intensity *

                    constants.LAVA_DECAY,

                    remaining-1,

                    visited

                )



    # =====================================================
    # Ash plume
    # =====================================================

    def add_ash(

        self,

        x,

        y,

        intensity

    ):


        angle = math.radians(

            constants.WIND_DIRECTION

        )



        dx = math.cos(angle)

        dy = -math.sin(angle)



        distance = int(

            intensity /

            constants.ASH_DISTANCE_SCALE

        )



        #
        # Create widening plume

        #

        for i in range(distance):


            cx = int(

                x + dx*i

            )


            cy = int(

                y + dy*i

            )



            if cx < 0 or cx >= constants.COLS:

                break


            if cy < 0 or cy >= constants.ROWS:

                break



            spread = int(

                i / 5

            )



            for sx in range(

                -spread,

                spread+1

            ):



                for sy in range(

                    -spread,

                    spread+1

                ):



                    nx = cx + sx

                    ny = cy + sy



                    if nx < 0 or nx >= constants.COLS:

                        continue



                    if ny < 0 or ny >= constants.ROWS:

                        continue



                    tile = self.game_map.tiles[ny][nx]



                    tile.hazards["ash"] = max(

                        tile.hazards["ash"],

                        intensity *

                        (

                            1 -

                            i/distance

                        )

                    )