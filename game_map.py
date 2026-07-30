import random
import pygame
import noise

import constants

from tile import Tile



class GameMap:


    def __init__(self):


        self.tiles = []


        self.map_modes = [

            "terrain",

            "elevation",

            "earthquake",

            "lava",

            "ash"

        ]


        self.view_index = 0



        #
        # Generate terrain
        #

        for y in range(constants.ROWS):


            row = []


            for x in range(constants.COLS):


                tile = Tile()



                value = noise.pnoise2(

                    x / constants.NOISE_SCALE,

                    y / constants.NOISE_SCALE,

                    octaves=constants.NOISE_OCTAVES,

                    persistence=constants.NOISE_PERSISTENCE,

                    lacunarity=constants.NOISE_LACUNARITY

                )



                tile.elevation = (

                    value + 1

                ) / 2



                tile.set_terrain()



                row.append(tile)



            self.tiles.append(row)



        #
        # Place hidden caldera
        #

        self.caldera = self.generate_caldera()



    # =====================================================
    # MAP VIEW CONTROL
    # =====================================================


    def current_view(self):

        return self.map_modes[self.view_index]



    def change_view(self, direction):


        self.view_index += direction



        if self.view_index < 0:

            self.view_index = len(self.map_modes)-1



        if self.view_index >= len(self.map_modes):

            self.view_index = 0



    # =====================================================
    # CALDERA
    # =====================================================


    def generate_caldera(self):


        possible = []


        for y,row in enumerate(self.tiles):


            for x,tile in enumerate(row):


                if tile.terrain in [

                    "land",

                    "mountain"

                ]:


                    possible.append(

                        (x,y)

                    )



        return random.choice(possible)



    # =====================================================
    # STRUCTURES
    # =====================================================


    def add_structure(

        self,

        x,

        y,

        structure_type

    ):


        if not (

            0 <= x < constants.COLS

            and

            0 <= y < constants.ROWS

        ):

            return



        if structure_type not in constants.INFRASTRUCTURE:

            return



        data = constants.INFRASTRUCTURE[structure_type]



        self.tiles[y][x].infrastructure.append(

            {

                "type": structure_type,

                "health": data["max_health"],

                "vulnerability": data["vulnerability"]

            }

        )



    # =====================================================
    # DAMAGE
    # =====================================================


    def apply_damage(self):


        for row in self.tiles:


            for tile in row:


                total_damage = (

                    tile.hazards["earthquake"]

                    +

                    tile.hazards["lava"]

                    +

                    tile.hazards["ash"]

                )



                if total_damage <= 0:

                    continue



                destroyed = []



                for item in tile.infrastructure:


                    damage = (

                        total_damage

                        *

                        item["vulnerability"]

                    )



                    item["health"] -= damage



                    if item["health"] <= 0:

                        destroyed.append(item)



                for item in destroyed:

                    tile.infrastructure.remove(item)



    # =====================================================
    # TILE COLOUR
    # =====================================================


    def get_tile_colour(self,tile):


        mode = self.current_view()



        if mode == "terrain":


            if tile.terrain == "water":

                return constants.WATER



            if tile.terrain == "land":

                return constants.LAND



            if tile.terrain == "mountain":

                return (

                    120,

                    120,

                    120

                )



        elif mode == "elevation":


            value = int(

                tile.elevation * 255

            )


            return (

                value,

                value,

                value

            )



        elif mode == "earthquake":


            value = min(

                255,

                int(tile.hazards["earthquake"] * 20)

            )


            return (

                value,

                0,

                0

            )



        elif mode == "lava":


            value = min(

                255,

                int(tile.hazards["lava"] * 2)

            )


            return (

                value,

                40,

                0

            )



        elif mode == "ash":


            value = min(

                255,

                int(tile.hazards["ash"] * 2)

            )


            return (

                value,

                value,

                value

            )


        return constants.BLACK



    # =====================================================
    # LEGEND
    # =====================================================


    def get_legend(self):


        mode = self.current_view()



        if mode == "terrain":

            return [

                "Blue = Water",

                "Green = Land",

                "Grey = Mountain"

            ]



        if mode == "elevation":

            return [

                "Dark = Low",

                "Light = High"

            ]



        if mode == "earthquake":

            return [

                "Dark = Weak",

                "Red = Strong"

            ]



        if mode == "lava":

            return [

                "Dark = None",

                "Orange = Lava"

            ]



        if mode == "ash":

            return [

                "Dark = None",

                "White = Ash"

            ]



    # =====================================================
    # PANEL
    # =====================================================


    def draw_panel(

    self,

    screen,

    day,

    volcano,

    events

):

        width, height = screen.get_size()

        panel_x = width - constants.PANEL_WIDTH

        pygame.draw.rect(

            screen,

            (30,30,30),

            (

                panel_x,

                0,

                constants.PANEL_WIDTH,

                height

            )

        )

        title_font = pygame.font.SysFont(None,30,bold=True)
        font = pygame.font.SysFont(None,24)

        y = 20

        # ---------------------------------------
        # Simulation
        # ---------------------------------------

        title = title_font.render(

            "Simulation",

            True,

            constants.WHITE

        )

        screen.blit(title,(panel_x+20,y))

        y += 40

        screen.blit(

            font.render(

                f"Day: {day}",

                True,

                constants.WHITE

            ),

            (panel_x+20,y)

        )

        y += 30

        screen.blit(

            font.render(

                f"Pressure: {volcano.pressure:.1f}",

                True,

                constants.WHITE

            ),

            (panel_x+20,y)

        )

        y += 30

        #
        # Pressure bar
        #

        pygame.draw.rect(

            screen,

            (60,60,60),

            (

                panel_x+20,

                y,

                constants.PANEL_WIDTH-40,

                18

            )

        )

        fraction = volcano.pressure/constants.PRESSURE_MAX

        fraction = max(0,min(1,fraction))

        if fraction < 0.5:

            colour = (0,200,0)

        elif fraction < 0.8:

            colour = (255,180,0)

        else:

            colour = (220,40,40)

        pygame.draw.rect(

            screen,

            colour,

            (

                panel_x+20,

                y,

                (constants.PANEL_WIDTH-40)*fraction,

                18

            )

        )

        y += 35

        #
        # Volcano status
        #

        if volcano.erupted:

            status = "ERUPTING"

            colour = constants.RED

        elif volcano.pressure > 80:

            status = "HIGH UNREST"

            colour = constants.ORANGE

        elif volcano.pressure > 50:

            status = "UNREST"

            colour = constants.YELLOW

        else:

            status = "DORMANT"

            colour = constants.WHITE

        screen.blit(

            font.render(

                status,

                True,

                colour

            ),

            (panel_x+20,y)

        )

        y += 50

        # ---------------------------------------
        # Events
        # ---------------------------------------

        title = title_font.render(

            "Events",

            True,

            constants.WHITE

        )

        screen.blit(title,(panel_x+20,y))

        y += 35

        if len(events) == 0:

            screen.blit(

                font.render(

                    "None",

                    True,

                    constants.WHITE

                ),

                (panel_x+20,y)

            )

            y += 25

        else:

            for event in events[-8:]:

                screen.blit(

                    font.render(

                        event,

                        True,

                        constants.WHITE

                    ),

                    (panel_x+20,y)

                )

                y += 22

        y += 20

        # ---------------------------------------
        # Current map
        # ---------------------------------------

        title = title_font.render(

            "Current Map",

            True,

            constants.WHITE

        )

        screen.blit(title,(panel_x+20,y))

        y += 35

        screen.blit(

            font.render(

                self.current_view().title(),

                True,

                constants.WHITE

            ),

            (panel_x+20,y)

        )

        y += 40

        # ---------------------------------------
        # Legend
        # ---------------------------------------

        title = title_font.render(

            "Legend",

            True,

            constants.WHITE

        )

        screen.blit(title,(panel_x+20,y))

        y += 35

        for item in self.get_legend():

            screen.blit(

                font.render(

                    item,

                    True,

                    constants.WHITE

                ),

                (panel_x+20,y)

            )

            y += 22


    # =====================================================
    # DRAW EVERYTHING
    # =====================================================


    def draw(

        self,

        screen,

        earthquakes,

        tile_width,

        tile_height,

        day,

        volcano,

        events,

        show_caldera=False

    ):



        #
        # Map tiles
        #

        for y,row in enumerate(self.tiles):


            for x,tile in enumerate(row):


                pygame.draw.rect(

                    screen,

                    self.get_tile_colour(tile),

                    (

                        x*tile_width,

                        y*tile_height,

                        tile_width,

                        tile_height

                    )

                )



                pygame.draw.rect(

                    screen,

                    constants.GRID,

                    (

                        x*tile_width,

                        y*tile_height,

                        tile_width,

                        tile_height

                    ),

                    1

                )



        #
        # Infrastructure
        #

        for y,row in enumerate(self.tiles):


            for x,tile in enumerate(row):


                for structure in tile.infrastructure:


                    pygame.draw.rect(

                        screen,

                        constants.WHITE,

                        (

                            x*tile_width + tile_width*0.25,

                            y*tile_height + tile_height*0.25,

                            tile_width*0.5,

                            tile_height*0.5

                        )

                    )



        #
        # Earthquakes
        #

        for quake in earthquakes:


            pygame.draw.rect(

                screen,

                constants.RED,

                (

                    quake.x*tile_width,

                    quake.y*tile_height,

                    tile_width,

                    tile_height

                )

            )



        #
        # Caldera debug
        #

        if show_caldera:


            x,y = self.caldera


            pygame.draw.rect(

                screen,

                constants.CALDERA,

                (

                    x*tile_width,

                    y*tile_height,

                    tile_width,

                    tile_height

                )

            )



        #
        # Side panel
        #

        self.draw_panel(

            screen,

            day,

            volcano,

            events

        )