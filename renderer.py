import pygame


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



        self.statistics = {

            "daily_earthquakes":0,

            "daily_eruptions":0,

            "accumulated_earthquakes":0,

            "accumulated_eruptions":0

        }



        self.terrain_surface = self.create_terrain_surface()



    # =====================================================
    # STATISTICS
    # =====================================================

    def update_statistics(

        self,

        statistics

    ):

        self.statistics = statistics



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



                if h < terrain.water_level:


                    colour = (

                        40,

                        80,

                        180

                    )


                elif h < 0.55:


                    colour = (

                        60,

                        170,

                        60

                    )


                elif h < terrain.mountain_level:


                    colour = (

                        130,

                        100,

                        60

                    )


                else:


                    colour = (

                        180,

                        180,

                        180

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


        x,y = self.world.volcano.caldera_position



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

    def draw_structures(

        self,

        screen

    ):


        cell = self.world.terrain.cell_size


        drawn=set()



        for y in range(

            self.world.grid_height

        ):


            for x in range(

                self.world.grid_width

            ):



                structure = self.world.grid[y][x]["structure"]



                if structure is None or structure.destroyed:

                    continue



                if structure in drawn:

                    continue



                drawn.add(structure)



                colour = structure.colour



                sx,sy = structure.position



                w,h = structure.size



                pygame.draw.rect(

                    screen,

                    colour,

                    (

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

                    ),

                    2

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

            "",

            "Today:",

            f"Earthquakes: {self.statistics['daily_earthquakes']}",

            f"Eruptions: {self.statistics['daily_eruptions']}",

            "",

            "Total:",

            f"Earthquakes: {self.statistics['accumulated_earthquakes']}",

            f"Eruptions: {self.statistics['accumulated_eruptions']}"

        ]


        y=120
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