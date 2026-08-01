import pygame

from world import World
from renderer import Renderer


#
# Window size
#

WORLD_WIDTH = 1000
WORLD_HEIGHT = 1000

SIDEBAR_WIDTH = 250


pygame.init()


screen = pygame.display.set_mode(

    (

        WORLD_WIDTH + SIDEBAR_WIDTH,

        WORLD_HEIGHT

    )

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
# Create renderer
#

renderer = Renderer(

    world,

    SIDEBAR_WIDTH

)



running = True


day_timer = 0



#
# Store daily statistics
#

daily_events = {

    "earthquakes":0,

    "eruptions":0

}



while running:


    for event in pygame.event.get():


        if event.type == pygame.QUIT:

            running=False



    #
    # Update simulation
    #

    day_timer += 1


    if day_timer >= 10:


        result = world.update()


        day_timer=0



        #
        # Update sidebar statistics
        #

        daily_events["earthquakes"] = len(

            result["earthquakes"]

        )


        daily_events["eruptions"] = int(

            result["eruption"]

        )



        renderer.update_statistics(

            daily_events

        )



    #
    # Draw

    renderer.draw(

        screen

    )


    pygame.display.flip()


    clock.tick(60)



pygame.quit()