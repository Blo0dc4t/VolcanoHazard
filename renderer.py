import pygame
from terrain import TERRAIN_TYPES
from constants import GAME_STATES


class Renderer:


    def __init__(

        self,

        world,

        sidebar_fraction=0.2

    ):


        self.world = world


        surface = pygame.display.get_surface()


        self.screen_width = surface.get_width()

        self.screen_height = surface.get_height()



        #
        # Sidebar
        #

        self.sidebar_width = int(

            self.screen_width *

            sidebar_fraction

        )


        self.map_width = (

            self.screen_width

            -

            self.sidebar_width

        )



        #
        # World scaling
        #

        self.scale_x = (

            self.map_width /

            self.world.width

        )


        self.scale_y = (

            self.screen_height /

            self.world.height

        )



        #
        # Fonts
        #

        self.font = pygame.font.SysFont(

            None,

            max(

                24,

                int(self.screen_height*0.035)

            )

        )


        self.small_font = pygame.font.SysFont(

            None,

            max(

                16,

                int(self.screen_height*0.022)

            )

        )

        #
        # Multiplayer selection
        #

        self.current_player_index = 0



        self.terrain_surface = self.create_terrain_surface()


    def get_clicked_structure(

        self,

        mouse_position

    ):


        mx,my = mouse_position



        for structure in self.world.infrastructure:


            if structure.destroyed:

                continue



            x,y = structure.position

            w,h = structure.size



            rect = pygame.Rect(

                int(
                    x *
                    self.world.terrain.cell_size *
                    self.scale_x
                ),


                int(
                    y *
                    self.world.terrain.cell_size *
                    self.scale_y
                ),


                int(
                    w *
                    self.world.terrain.cell_size *
                    self.scale_x
                ),


                int(
                    h *
                    self.world.terrain.cell_size *
                    self.scale_y
                )

            )



            if rect.collidepoint(
                mx,
                my
            ):

                return structure



        return None


    # =====================================================
    # TERRAIN
    # =====================================================

    def create_terrain_surface(self):


        terrain = self.world.terrain


        surface = pygame.Surface(

            (

                terrain.width,

                terrain.height

            )

        )


        for y in range(

            terrain.grid_height

        ):


            for x in range(

                terrain.grid_width

            ):


                h = terrain.height_map[y,x]



                colour = None


                for terrain_type, data in sorted(
                    
                    TERRAIN_TYPES.items(),

                    key=lambda item: item[1]["level"]

                ):


                    if h < data["level"]:

                        colour = data["colour"]

                        break



                #
                # Safety fallback
                #

                if colour is None:

                    colour = (

                        255,

                        255,

                        255

                    )



                pygame.draw.rect(

                    surface,

                    colour,

                    (

                        x*terrain.cell_size,

                        y*terrain.cell_size,

                        terrain.cell_size,

                        terrain.cell_size

                    )

                )


        return surface



    # =====================================================
    # DRAW EVERYTHING
    # =====================================================

    def draw(

        self,

        screen

    ):


        self.draw_terrain(screen)

        self.draw_structures(screen)

        self.draw_lava(screen)

        self.draw_ash(screen)

        self.draw_volcano(screen)

        self.draw_earthquakes(screen)

        self.draw_sidebar(screen)



    # =====================================================
    # TERRAIN
    # =====================================================

    def draw_terrain(

        self,

        screen

    ):


        scaled_surface = pygame.transform.scale(

            self.terrain_surface,

            (

                self.map_width,

                self.screen_height

            )

        )


        screen.blit(

            scaled_surface,

            (

                0,

                0

            )

        )


    # =====================================================
    # VOLCANO
    # =====================================================

    def draw_volcano(

        self,

        screen

    ):


        for volcano in self.world.volcanoes:


            x, y = volcano.caldera_position



            pygame.draw.circle(

                screen,

                (
                    255,
                    0,
                    0
                ),

                (
                    int(x*self.scale_x),

                    int(y*self.scale_y)

                ),

                6

            )


    # =====================================================
    # LAVA CELLS
    # =====================================================

    def draw_lava(

        self,

        screen

    ):


        cell = self.world.terrain.cell_size



        for y in range(

            self.world.grid_height

        ):


            for x in range(

                self.world.grid_width

            ):



                lava = self.world.grid[y][x]["lava"]



                if lava <= 0:

                    continue



                pygame.draw.rect(

                    screen,

                    (

                        255,

                        80,

                        0

                    ),

                    (

                        int(

                            x *

                            cell *

                            self.scale_x

                        ),


                        int(

                            y *

                            cell *

                            self.scale_y

                        ),


                        max(

                            1,

                            int(

                                cell *

                                self.scale_x

                            )

                        ),


                        max(

                            1,

                            int(

                                cell *

                                self.scale_y

                            )

                        )

                    )

                )



    # =====================================================
    # ASH CELLS
    # =====================================================

    def draw_ash(

        self,

        screen

    ):


        cell = self.world.terrain.cell_size



        ash_surface = pygame.Surface(

            screen.get_size(),

            pygame.SRCALPHA

        )



        for y in range(

            self.world.grid_height

        ):


            for x in range(

                self.world.grid_width

            ):



                ash = self.world.grid[y][x]["ash"]



                if ash <= 0:

                    continue



                alpha = max(

                    20,

                    min(

                        180,

                        int(ash*180)

                    )

                )



                pygame.draw.rect(

                    ash_surface,

                    (

                        120,

                        120,

                        120,

                        alpha

                    ),

                    (

                        int(

                            x *

                            cell *

                            self.scale_x

                        ),


                        int(

                            y *

                            cell *

                            self.scale_y

                        ),


                        max(

                            1,

                            int(

                                cell *

                                self.scale_x

                            )

                        ),


                        max(

                            1,

                            int(

                                cell *

                                self.scale_y

                            )

                        )

                    )

                )



        screen.blit(

            ash_surface,

            (

                0,

                0

            )

        )



    # =====================================================
    # INFRASTRUCTURE
    # =====================================================


        # =====================================================
    # HEALTH BAR
    # =====================================================

    def draw_health_bar(

        self,

        screen,

        structure,

        rect

    ):


        if structure.max_health <= 0:

            return



        health_fraction = (

            structure.health /

            structure.max_health

        )


        health_fraction = max(

            0,

            min(

                1,

                health_fraction

            )

        )



        bar_width = rect[2]

        bar_height = 6



        bar_x = rect[0]

        bar_y = rect[1] - 10



        #
        # Background
        #

        pygame.draw.rect(

            screen,

            (

                80,

                80,

                80

            ),

            (

                bar_x,

                bar_y,

                bar_width,

                bar_height

            )

        )



        #
        # Health colour
        #

        if health_fraction > 0.6:


            colour = (

                0,

                200,

                0

            )


        elif health_fraction > 0.3:


            colour = (

                220,

                200,

                0

            )


        else:


            colour = (

                220,

                0,

                0

            )



        pygame.draw.rect(

            screen,

            colour,

            (

                bar_x,

                bar_y,

                int(

                    bar_width *

                    health_fraction

                ),

                bar_height

            )

        )





    # =====================================================
    # HEALTH TEXT
    # =====================================================

    def draw_health_text(

        self,

        screen,

        structure,

        rect

    ):


        text = self.small_font.render(

            f"{int(structure.health)}/{int(structure.max_health)}",

            True,

            (

                255,

                255,

                255

            )

        )



        screen.blit(

            text,

            (

                rect[0],

                rect[1] - 30

            )

        )


    def draw_structures(

        self,

        screen

    ):


        cell = self.world.terrain.cell_size



        drawn = set()



        for y in range(

            self.world.grid_height

        ):


            for x in range(

                self.world.grid_width

            ):



                structure = self.world.grid[y][x]["structure"]



                if structure is None:

                    continue



                if structure.destroyed:

                    continue



                if structure in drawn:

                    continue



                drawn.add(structure)



                #
                # Structure colour
                #

                colour = structure.colour



                #
                # Player ownership colour
                #

                if structure.owner:

                    colour = structure.owner.colour



                sx, sy = structure.position

                w, h = structure.size



                rect = (

                    int(

                        sx *

                        cell *

                        self.scale_x

                    ),


                    int(

                        sy *

                        cell *

                        self.scale_y

                    ),


                    int(

                        w *

                        cell *

                        self.scale_x

                    ),


                    int(

                        h *

                        cell *

                        self.scale_y

                    )

                )



                #
                # Draw structure outline
                #

                pygame.draw.rect(

                    screen,

                    colour,

                    rect,

                    3

                )



                #
                # Health display
                #

                if structure.owner:


                    if structure.type in (

                        "city",

                        "town"

                    ):


                        self.draw_health_bar(

                            screen,

                            structure,

                            rect

                        )



                    if structure.type == "city":


                        self.draw_health_text(

                            screen,

                            structure,

                            rect

                        )



                #
                # Starting selection highlight
                #

                if (

                    self.world.game_state == GAME_STATES["CITY_SELECTION"]

                    and

                    structure.owner is None

                ):


                    pygame.draw.rect(

                        screen,

                        (

                            255,

                            255,

                            255

                        ),

                        rect,

                        1

                    )

    # =====================================================
    # EARTHQUAKES
    # =====================================================

    def draw_earthquakes(

        self,

        screen

    ):


        for earthquake in self.world.recent_earthquakes:


            x,y = earthquake["location"]



            pygame.draw.circle(

                screen,

                (

                    0,

                    0,

                    0

                ),

                (

                    int(

                        x*self.scale_x

                    ),

                    int(

                        y*self.scale_y

                    )

                ),

                max(

                    5,

                    int(

                        earthquake["magnitude"]

                    )

                )

            )



    # =====================================================
    # SIDEBAR
    # =====================================================

    def draw_sidebar(

        self,

        screen

    ):


        x = self.map_width



        pygame.draw.rect(

            screen,

            (

                30,

                30,

                30

            ),

            (

                x,

                0,

                self.sidebar_width,

                self.screen_height

            )

        )



        title=self.font.render(

            "Simulation",

            True,

            (

                255,

                255,

                255

            )

        )


        screen.blit(

            title,

            (

                x+20,

                40

            )

        )


        lines = [

            f"Day: {self.world.day}",

            f"Volcanoes: {len(self.world.volcanoes)}",

            "",

            "Today:",

            f"Earthquakes: {len(self.world.recent_earthquakes)}",

            f"Eruptions: {len(self.world.recent_eruptions)}",

            "",

            "Total:",

            f"Earthquakes: {len(self.world.earthquakes)}",

            f"Eruptions: {len(self.world.eruptions)}"

        ]


        y=120

        #
        # Multiplayer information
        #

        if self.world.game_state == GAME_STATES["CITY_SELECTION"]:


            player = self.world.get_current_player()


            if player:


                text = self.small_font.render(

                    f"{player.name}: choose city",

                    True,

                    (
                        255,
                        255,
                        255
                    )

                )


                screen.blit(

                    text,

                    (
                        x+20,
                        y
                    )

                )


                y += 40



        else:


            for player in self.world.players:

                if player.city:

                    text = self.small_font.render(

                        f"{player.name}",

                        True,

                        player.colour

                    )

                    screen.blit(

                        text,

                        (x + 20, y)

                    )

                    y += 25

                    city_text = self.small_font.render(

                        f"City: {player.city.name}",

                        True,

                        (220, 220, 220)

                    )

                    screen.blit(

                        city_text,

                        (x + 20, y)

                    )

                    y += 25

                    repair_text = self.small_font.render(
                        
                        f"Repair Cost: ${player.city.get_repair_cost()}/HP",

                        True,

                        (220, 220, 220)

                    )

                    screen.blit(

                        repair_text,

                        (x + 20, y)

                    )

                    y += 25

                    money_text = self.small_font.render(

                        f"Money: ${player.money}",

                        True,

                        (255, 215, 0)

                    )

                    screen.blit(

                        money_text,

                        (x + 20, y)

                    )

                    y += 25

                    income_text = self.small_font.render(

                        f"Total Income: ${player.income}",

                        True,

                        (0, 255, 0)

                    )

                    screen.blit(

                        income_text,

                        (x + 20, y)

                    )

                    y += 40



        # draw the wind direction and current wind speed
        wind_text = self.small_font.render(
        
            f"Wind: {self.world.vector_to_compass(self.world.wind_direction)} at {round(self.world.wind_speed, 1)} m/s",

            True,

            (

                220,

                220,

                220

            )

        )


        screen.blit(

            wind_text,

            (

                x+20,

                y

            )

        )

        y += 40

        # draw volcano and earthquke stats


        for line in lines:


            text=self.small_font.render(

                line,

                True,

                (

                    220,

                    220,

                    220

                )

            )


            screen.blit(

                text,

                (

                    x+20,

                    y

                )

            )


            y+=40