import pygame

from world import World
from renderer import Renderer
from constants import GAME_STATES



pygame.init()



#
# Screen
#

info = pygame.display.Info()


SCREEN_WIDTH = info.current_w

SCREEN_HEIGHT = info.current_h



WORLD_WIDTH = 1000

WORLD_HEIGHT = 1000



SIDEBAR_FRACTION = 0.2



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
# Create world
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
# Simulation timing
#

SIMULATION_SPEED = 10

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


        if event.type == pygame.QUIT:

            running = False



        if event.type == pygame.KEYDOWN:


            if event.key == pygame.K_ESCAPE:

                running = False



            #
            # Repair selected structure
            #

            if event.key == pygame.K_r:


                if world.selected_structure:


                    repaired = world.selected_structure.repair()


                    print(

                        f"Repaired {world.selected_structure.name} for {repaired} HP"

                    )



        #
        # Structure selection
        #

        if event.type == pygame.MOUSEBUTTONDOWN:


            structure = renderer.get_clicked_structure(

                event.pos

            )


            if structure:


                print(

                    "Clicked on structure:",

                    structure.name

                )


                #
                # Always select structure
                #

                world.selected_structure = structure



                #
                # City selection:
                # clicking also claims the city
                #

                if world.game_state == GAME_STATES["CITY_SELECTION"]:


                    claimed = world.claim_city(

                        structure

                    )


                    if claimed:


                        player = world.players[
                            world.current_player_index - 1
                        ]


                        print(

                            player.name,

                            "selected",

                            structure.name

                        )



                        #
                        # All players selected
                        #

                        if world.current_player_index >= len(world.players):


                            world.game_state = GAME_STATES["PLAYING"]


                            print(

                                "Simulation started"

                            )




    #
    # SIMULATION UPDATE
    #

    if world.game_state == GAME_STATES["PLAYING"]:


        day_timer += 1



        if day_timer >= 10:


            for _ in range(SIMULATION_SPEED):


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