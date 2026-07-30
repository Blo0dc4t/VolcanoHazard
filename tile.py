class Tile:


    def __init__(self):


        #
        # Terrain properties
        #

        self.elevation = 0

        self.terrain = None



        #
        # Hazard intensity fields
        #

        self.hazards = {

            "earthquake": 0,

            "lava": 0,

            "ash": 0

        }



        #
        # Objects placed on tile
        #

        self.infrastructure = []



    # =====================================================
    # Terrain classification
    # =====================================================

    def set_terrain(self):


        from constants import (

            WATER_LEVEL,

            COAST_LEVEL,

            MOUNTAIN_LEVEL

        )



        if self.elevation < WATER_LEVEL:


            self.terrain = "water"



        elif self.elevation < COAST_LEVEL:


            self.terrain = "coast"



        elif self.elevation < MOUNTAIN_LEVEL:


            self.terrain = "land"



        else:


            self.terrain = "mountain"