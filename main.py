import pygame

from world import World
from renderer import Renderer
from constants import (
    GAME_STATES,
    WORLD_WIDTH,
    WORLD_HEIGHT,
    SIDEBAR_FRACTION,
    SIMULATION_SPEED
)


pygame.init()


#
# Screen
#

info = pygame.display.Info()

SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

screen = pygame.display.set_mode(

    (
        SCREEN_WIDTH,
        SCREEN_HEIGHT
    ),

    pygame.FULLSCREEN
)

pygame.display.set_caption(
    "Volcano Simulation"
)

clock = pygame.time.Clock()


#
# World
#

world = World(
    WORLD_WIDTH,
    WORLD_HEIGHT
)


#
# Renderer
#

renderer = Renderer(
    world,
    SIDEBAR_FRACTION
)


#
# Simulation timer
#

day_timer = 0

running = True


# =====================================================
# MAIN LOOP
# =====================================================

while running:

    #
    # EVENTS
    #

    for event in pygame.event.get():

        #
        # Quit
        #

        if event.type == pygame.QUIT:

            running = False

        #
        # Keyboard
        #

        if event.type == pygame.KEYDOWN:

            #
            # Escape
            #

            if event.key == pygame.K_ESCAPE:

                running = False

            #
            # Repair selected structure
            #

            if event.key == pygame.K_r:

                if world.selected_structure:

                    repaired = (
                        world.selected_structure.repair()
                    )

                    print(

                        f"Repaired "
                        f"{world.selected_structure.name} "
                        f"for "
                        f"{repaired} HP"

                    )

            #
            # Pause / resume
            #

            if event.key == pygame.K_RETURN:

                if (
                    world.game_state ==
                    GAME_STATES["PAUSED"]
                ):

                    world.game_state = (
                        GAME_STATES["PLAYING"]
                    )

                    print(
                        "Simulation resumed"
                    )

                elif (
                    world.game_state ==
                    GAME_STATES["PLAYING"]
                ):

                    world.game_state = (
                        GAME_STATES["PAUSED"]
                    )

                    print(
                        "Simulation paused"
                    )

            #
            # Building mode
            #

            if event.key == pygame.K_b:

                if world.game_state in (

                    GAME_STATES["PLAYING"],
                    GAME_STATES["PAUSED"]

                ):

                    world.game_state = (
                        GAME_STATES[
                            "BUILDING_PLACEMENT"
                        ]
                    )

                    world.build_structure_type = None

                    print(
                        "Building mode"
                    )

                elif (
                    world.game_state ==
                    GAME_STATES[
                        "BUILDING_PLACEMENT"
                    ]
                ):

                    world.game_state = (
                        GAME_STATES["PLAYING"]
                    )

                    world.build_structure_type = None

                    print(
                        "Building mode cancelled"
                    )

            #
            # Building number selection
            #

            if (
                event.key >= pygame.K_1
                and
                event.key <= pygame.K_9
                and
                world.game_state ==
                GAME_STATES[
                    "BUILDING_PLACEMENT"
                ]
            ):

                buildable_types = (
                    renderer.get_buildable_types()
                )

                number = (
                    event.key -
                    pygame.K_1
                )

                if number < len(
                    buildable_types
                ):

                    world.build_structure_type = (
                        buildable_types[number]
                    )

                    print(

                        "Selected building:",

                        world.build_structure_type

                    )

        #
        # Mouse
        #

        if event.type == pygame.MOUSEBUTTONDOWN:

            #
            # Left button
            #

            if event.button != 1:
                continue

            #
            # BUILDING MODE
            #

            if (
                world.game_state ==
                GAME_STATES[
                    "BUILDING_PLACEMENT"
                ]
            ):

                #
                # Must have selected a type
                #

                if (
                    world.build_structure_type
                    is None
                ):
                    continue

                #
                # Convert mouse position
                # to grid position
                #

                grid_x, grid_y = (
                    renderer.screen_to_grid(
                        *event.pos
                    )
                )

                #
                # Attempt construction
                #

                placed = world.build_structure(

                    world.build_structure_type,

                    grid_x,

                    grid_y

                )

                if placed:

                    print(

                        f"Placed "
                        f"{world.build_structure_type} "
                        f"at "
                        f"({grid_x}, {grid_y})"

                    )

                else:

                    print(
                        "Cannot build there"
                    )

                #
                # Do not also select
                # a structure underneath
                # the mouse.
                #

                continue

            #
            # Get clicked structure
            #

            structure = (
                renderer.get_clicked_structure(
                    event.pos
                )
            )

            #
            # Nothing clicked
            #

            if structure is None:
                continue

            #
            # CITY SELECTION
            #

            if (
                world.game_state ==
                GAME_STATES[
                    "CITY_SELECTION"
                ]
            ):

                claimed = world.claim_city(structure)

                if claimed:

                    print(
                        structure.owner.name,
                        "selected",
                        structure.name
                    )

            #
            # NORMAL PLAY OR PAUSED
            #

            if (
                world.game_state in (
                    GAME_STATES["PLAYING"], GAME_STATES["PAUSED"]
                )
            ):

                #
                # Select structure
                #

                world.selected_structure = (
                    structure
                )

                #
                # If it belongs to a player,
                # switch to that player.
                #

                switched = (
                    world.select_player_from_structure(
                        structure
                    )
                )

                if switched:

                    print(

                        "Current player:",

                        world.get_current_player().name

                    )

    #
    # SIMULATION UPDATE
    #

    if (
        world.game_state ==
        GAME_STATES["PLAYING"]
    ):

        day_timer += 1

        if day_timer >= 10:

            for _ in range(
                SIMULATION_SPEED
            ):

                world.update()

            day_timer = 0

    #
    # DRAW
    #

    renderer.draw(
        screen
    )

    pygame.display.flip()

    clock.tick(60)


pygame.quit()