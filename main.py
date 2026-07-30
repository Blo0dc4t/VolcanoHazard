import pygame

import constants

from game_map import GameMap
from volcano import Volcano
from earthquakes import EarthquakeGenerator


pygame.init()


# =====================================================
# FULLSCREEN DISPLAY
# =====================================================

screen = pygame.display.set_mode(

    (0, 0),

    pygame.FULLSCREEN

)

WIDTH, HEIGHT = screen.get_size()

pygame.display.set_caption(

    "Volcano Hazard Simulation"

)

clock = pygame.time.Clock()


# =====================================================
# DISPLAY SCALING
# =====================================================

# Width available for the map (excluding side panel)

MAP_WIDTH = WIDTH - constants.PANEL_WIDTH

tile_width = MAP_WIDTH / constants.COLS

tile_height = HEIGHT / constants.ROWS


# =====================================================
# CREATE GAME OBJECTS
# =====================================================

game_map = GameMap()

volcano = Volcano()

earthquakes = EarthquakeGenerator()


# =====================================================
# GAME STATE
# =====================================================

running = True

day = 0

events = []


# =====================================================
# MAIN LOOP
# =====================================================

while running:


    for event in pygame.event.get():


        if event.type == pygame.QUIT:

            running = False


        elif event.type == pygame.KEYDOWN:


            # -----------------------------------------
            # Exit
            # -----------------------------------------

            if event.key == pygame.K_ESCAPE:

                running = False


            # -----------------------------------------
            # Change map view
            # -----------------------------------------

            elif event.key == pygame.K_LEFT:

                game_map.change_view(-1)


            elif event.key == pygame.K_RIGHT:

                game_map.change_view(1)


            # -----------------------------------------
            # Advance one timestep
            # -----------------------------------------

            elif event.key == pygame.K_RETURN:


                day += 1

                events = []


                #
                # Volcano update
                #

                volcano.update()


                if volcano.erupted:

                    events.append("Volcanic eruption")


                #
                # Earthquakes
                #

                before = len(

                    earthquakes.events

                )


                earthquakes.generate(

                    volcano.pressure,

                    game_map.caldera

                )


                after = len(

                    earthquakes.events

                )


                if after > before:


                    quake = earthquakes.events[-1]


                    events.append(

                        f"M{quake.magnitude:.1f} earthquake"

                    )


                #
                # Update earthquake catalogue
                #

                earthquakes.update()


                #
                # Apply hazard damage
                #

                game_map.apply_damage()


                print(

                    f"DAY {day}"

                )


    # =================================================
    # DRAW
    # =================================================

    screen.fill(

        constants.BLACK

    )


    game_map.draw(

        screen,

        earthquakes.events,

        tile_width,

        tile_height,

        day,

        volcano,

        events,

        show_caldera=True

    )


    pygame.display.flip()


    clock.tick(

        constants.FPS

    )


pygame.quit()