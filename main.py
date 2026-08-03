import pygame

from world import World
from renderer import Renderer



pygame.init()



#
# Get monitor resolution
#

info = pygame.display.Info()


SCREEN_WIDTH = info.current_w

SCREEN_HEIGHT = info.current_h



#
# Simulation resolution
# (never changes)
#

WORLD_WIDTH = 1000

WORLD_HEIGHT = 1000



SIDEBAR_FRACTION = 0.2



#
# Fullscreen window
#

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



running=True

SIMULATION_SPEED=10

day_timer=0


daily_events = {
    "earthquakes": 0,
    "eruptions": 0
}


accumulated_events = {
    "earthquakes": 0,
    "eruptions": 0
}


while running:


    for event in pygame.event.get():


        if event.type == pygame.QUIT:

            running=False


        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                running=False



    #
    # Simulation update
    #

    day_timer += 1


    if day_timer >= 10:

        earthquakes_today = 0
        eruptions_today = 0

        for _ in range(SIMULATION_SPEED):

            result = world.update()

            earthquakes_today += len(
                result["earthquakes"]
            )

            if result["eruption"]:
                eruptions_today += 1

        day_timer = 0

        #
        # Store today's events
        #

        daily_events["earthquakes"] = earthquakes_today
        daily_events["eruptions"] = eruptions_today

        #
        # Update totals
        #

        accumulated_events["earthquakes"] += earthquakes_today
        accumulated_events["eruptions"] += eruptions_today

        #
        # Send both to renderer
        #

        renderer.update_statistics({

            "daily_earthquakes": daily_events["earthquakes"],
            "daily_eruptions": daily_events["eruptions"],

            "accumulated_earthquakes": accumulated_events["earthquakes"],
            "accumulated_eruptions": accumulated_events["eruptions"]

        })



    #
    # Draw
    #
    renderer.draw(

        screen

    )


    pygame.display.flip()


    clock.tick(60)



pygame.quit()