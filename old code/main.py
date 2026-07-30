import pygame
import random
import math


# =====================================================
# SETTINGS
# =====================================================

WIDTH = 800
HEIGHT = 800

GRID_SIZE = 25

ROWS = HEIGHT // GRID_SIZE
COLS = WIDTH // GRID_SIZE

FPS = 10


# =====================================================
# COLOURS
# =====================================================

WATER = (40, 90, 170)
LAND = (80, 150, 80)

EARTHQUAKE_SMALL = (240, 220, 60)
EARTHQUAKE_LARGE = (220, 50, 40)

CALDERA_COLOUR = (130, 0, 130)

LAVA = (255, 80, 20)
ASH = (130, 130, 130)

GRID = (30, 30, 30)



# =====================================================
# TILE
# =====================================================

class Tile:

    def __init__(self):

        self.earthquake = 0

        self.lava = False

        self.ash = False

        self.damage = 0



# =====================================================
# VOLCANO
# =====================================================

class Volcano:

    def __init__(self):

        # Current pressure level

        self.pressure = random.randint(
            20,
            40
        )


        # Volcano personality

        self.explosivity = random.randint(
            0,
            100
        )


        # Effects of last eruption

        self.eruption_radius = 0

        self.ash_cloud = 0

        self.damage = 0


        self.erupted_this_turn = False



    def update(self):

        self.erupted_this_turn = False


        # magma recharge

        self.pressure += random.gauss(
            3,
            5
        )


        self.pressure = max(
            0,
            min(
                100,
                self.pressure
            )
        )


        # unrest dies away sometimes

        if random.random() < 0.03:

            release = random.randint(
                10,
                30
            )

            self.pressure -= release


            print(
                "Pressure released naturally:",
                release
            )


        # eruption check

        if self.pressure >= 90:

            self.erupt()



    def erupt(self):

        self.erupted_this_turn = True


        print("\n================")
        print(" ERUPTION ")
        print("================")


        # eruption strength

        power = (
            self.pressure +
            self.explosivity
        )


        # scale consequences

        self.eruption_radius = max(
            2,
            int(power / 30)
        )


        self.damage = int(
            power * 2
        )


        self.ash_cloud = max(
            5,
            int(power / 10)
        )


        # eruption type

        if power < 120:

            eruption_type = "Effusive lava flow"

            pressure_release = random.randint(
                40,
                60
            )


        elif power < 170:

            eruption_type = "Explosive eruption"

            pressure_release = random.randint(
                60,
                80
            )


        else:

            eruption_type = "Major explosive eruption"

            pressure_release = random.randint(
                80,
                95
            )


        print(
            "Style:",
            eruption_type
        )

        print(
            "Power:",
            round(power)
        )

        print(
            "Lava radius:",
            self.eruption_radius
        )

        print(
            "Ash radius:",
            self.ash_cloud
        )

        print(
            "Damage:",
            self.damage
        )


        # release pressure

        self.pressure -= pressure_release


        self.pressure = max(
            0,
            self.pressure
        )


        print(
            "New pressure:",
            round(self.pressure,1)
        )



# =====================================================
# MAP
# =====================================================

class GameMap:


    def __init__(self):

        self.tiles = [

            [
                Tile()
                for x in range(COLS)
            ]

            for y in range(ROWS)

        ]


        # hidden volcano location

        self.caldera = (

            random.randint(
                10,
                COLS-10
            ),

            random.randint(
                10,
                ROWS-10
            )

        )



    def distance_from_caldera(
            self,
            x,
            y
    ):

        cx, cy = self.caldera


        return math.sqrt(

            (x-cx)**2 +
            (y-cy)**2

        )



    def update_earthquakes(
            self,
            volcano
    ):


        for y in range(ROWS):

            for x in range(COLS):


                distance = self.distance_from_caldera(
                    x,
                    y
                )


                # exponential decay

                location_factor = math.exp(
                    -distance / 5
                )


                pressure_factor = (
                    volcano.pressure / 100
                )


                chance = (
                    location_factor *
                    pressure_factor
                )


                if random.random() < chance:


                    self.tiles[y][x].earthquake = random.randint(
                        20,
                        100
                    )


                else:

                    # earthquake fading

                    self.tiles[y][x].earthquake *= 0.8



    def create_lava(
            self,
            radius
    ):

        cx, cy = self.caldera


        for y in range(ROWS):

            for x in range(COLS):


                distance = math.sqrt(

                    (x-cx)**2 +
                    (y-cy)**2

                )


                if distance <= radius:

                    self.tiles[y][x].lava = True



    def create_ash(
            self,
            radius
    ):

        cx, cy = self.caldera


        for y in range(ROWS):

            for x in range(COLS):


                distance = math.sqrt(

                    (x-cx)**2 +
                    (y-cy)**2

                )


                if distance <= radius:

                    self.tiles[y][x].ash = True



    def clear_old_effects(self):

        for row in self.tiles:

            for tile in row:

                tile.lava = False

                tile.ash = False



    def draw(
            self,
            screen
    ):


        for y in range(ROWS):

            for x in range(COLS):


                tile = self.tiles[y][x]


                colour = LAND


                if tile.ash:

                    colour = ASH


                if tile.earthquake > 0:

                    if tile.earthquake < 60:

                        colour = EARTHQUAKE_SMALL

                    else:

                        colour = EARTHQUAKE_LARGE



                if tile.lava:

                    colour = LAVA



                # show caldera for testing

                if (x,y) == self.caldera:

                    colour = CALDERA_COLOUR



                pygame.draw.rect(

                    screen,

                    colour,

                    (
                        x*GRID_SIZE,
                        y*GRID_SIZE,
                        GRID_SIZE,
                        GRID_SIZE
                    )

                )


                pygame.draw.rect(

                    screen,

                    GRID,

                    (
                        x*GRID_SIZE,
                        y*GRID_SIZE,
                        GRID_SIZE,
                        GRID_SIZE
                    ),

                    1

                )



# =====================================================
# MAIN GAME LOOP
# =====================================================


pygame.init()


screen = pygame.display.set_mode(
    (
        WIDTH,
        HEIGHT
    )
)


pygame.display.set_caption(
    "Volcano Simulation"
)


clock = pygame.time.Clock()



game_map = GameMap()

volcano = Volcano()



running = True


while running:


    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False



    # remove previous eruption effects

    game_map.clear_old_effects()



    # update volcano

    volcano.update()



    # earthquakes

    game_map.update_earthquakes(
        volcano
    )



    # eruption effects

    if volcano.erupted_this_turn:


        game_map.create_lava(
            volcano.eruption_radius
        )


        game_map.create_ash(
            volcano.ash_cloud
        )



    # draw

    screen.fill(
        WATER
    )


    game_map.draw(
        screen
    )


    pygame.display.flip()


    clock.tick(FPS)



pygame.quit()