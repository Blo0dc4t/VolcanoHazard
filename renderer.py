import pygame


class Renderer:


    def __init__(

        self,

        world,

        sidebar_width

    ):

        self.world = world

        self.sidebar_width = sidebar_width


        self.font = pygame.font.SysFont(

            None,

            28

        )


        self.small_font = pygame.font.SysFont(

            None,

            22

        )


        self.statistics = {

            "earthquakes":0,

            "eruptions":0

        }


        self.terrain_surface = self.create_terrain_surface()


    # ====================================================
    # UPDATE STATISTICS
    # ====================================================

    def update_statistics(

        self,

        statistics

    ):

        self.statistics = statistics


    # =====================================================
    # CREATE TERRAIN SURFACE
    # =====================================================

    def create_terrain_surface(self):


        terrain=self.world.terrain


        surface=pygame.Surface(

            (

                terrain.width,

                terrain.height

            )

        )


        for y in range(terrain.grid_height):

            for x in range(terrain.grid_width):


                h=terrain.height_map[y,x]


                if h < terrain.water_level:

                    colour=(40,80,180)

                elif h < 0.55:

                    colour=(60,170,60)

                elif h < terrain.mountain_level:

                    colour=(130,100,60)

                else:

                    colour=(180,180,180)



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


        self.draw_terrain(

            screen

        )


        self.draw_volcano(

            screen

        )


        self.draw_earthquakes(

            screen

        )

        self.draw_lava(screen)

        self.draw_ash(screen)

        self.draw_sidebar(screen)


    # =====================================================
    # TERRAIN
    # =====================================================

    def draw_terrain(

        self,

        screen

    ):


        screen.blit(

            self.terrain_surface,

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

                x,

                y

            ),

            6

        )


    def draw_lava(self, screen):


        for flow in self.world.lava_flows:


            for point in flow:


                x,y = point


                if (
                    0 <= x < self.world.width
                    and
                    0 <= y < self.world.height
                ):


                    pygame.draw.rect(

                        screen,

                        (255,80,0),

                        (

                            x*self.world.terrain.cell_size,

                            y*self.world.terrain.cell_size,

                            self.world.terrain.cell_size,

                            self.world.terrain.cell_size

                        )

                    )


    def draw_ash(self, screen):


        for plume in self.world.ash_plumes:


            for point in plume:


                x,y = point


                if (
                    0 <= x < self.world.width
                    and
                    0 <= y < self.world.height
                ):


                    pygame.draw.circle(

                        screen,

                        (180,180,180),

                        point,

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

                    x,

                    y

                ),

                2

            )

    # =====================================================
    # SIDEBAR
    # =====================================================

    def draw_sidebar(self, screen):


        x = self.world.width


        pygame.draw.rect(

            screen,

            (30,30,30),

            (

                x,

                0,

                self.sidebar_width,

                self.world.height

            )

        )


        text = self.font.render(

            "Simulation",

            True,

            (255,255,255)

        )


        screen.blit(

            text,

            (

                x+20,

                30

            )

        )



        lines=[

            f"Day: {self.world.day}",

            "",

            "Events today:",

            f"Earthquakes: {self.statistics['earthquakes']}",

            f"Eruptions: {self.statistics['eruption'] if 'eruption' in self.statistics else self.statistics['eruptions']}"

        ]



        y=90


        for line in lines:


            text=self.small_font.render(

                line,

                True,

                (220,220,220)

            )


            screen.blit(

                text,

                (

                    x+20,

                    y

                )

            )


            y+=35
