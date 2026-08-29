import pygame

from world import World
from renderer import Renderer, MenuRenderer
from constants import (
    GAME_STATES,
    WORLD_WIDTH,
    WORLD_HEIGHT,
    SIDEBAR_FRACTION,
    SIMULATION_SPEED,
)


pygame.init()

info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Volcano Simulation")
clock = pygame.time.Clock()

# Game state
menu_state = "HOME"
world = None
renderer = None
menu_renderer = MenuRenderer(SCREEN_WIDTH, SCREEN_HEIGHT)
custom_volcano_settings = None

# Home screen buttons
home_buttons = {
    "Play": pygame.Rect(SCREEN_WIDTH // 2 - 110, 220, 220, 60),
    "Options": pygame.Rect(SCREEN_WIDTH // 2 - 110, 310, 220, 60),
    "Quit": pygame.Rect(SCREEN_WIDTH // 2 - 110, 400, 220, 60),
}

# Tab rectangles for click detection
def get_tab_rects():
    rects = {}
    for index, tab_name in enumerate(menu_renderer.option_tabs):
        rects[index] = pygame.Rect(50 + index * 190, 30, 180, 42)
    return rects


def create_world(custom_settings=None):
    global world, renderer, menu_state
    world = World(WORLD_WIDTH, WORLD_HEIGHT)
    if custom_settings is not None:
        world.apply_volcano_settings(custom_settings)
    world.game_state = GAME_STATES["CITY_SELECTION"]
    renderer = Renderer(world, SIDEBAR_FRACTION)
    menu_state = "PLAYING"


# Main loop
day_timer = 0
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            continue

        if menu_state == "HOME":
            if event.type == pygame.MOUSEBUTTONDOWN:
                for label, rect in home_buttons.items():
                    if rect.collidepoint(event.pos):
                        if label == "Play":
                            create_world(custom_volcano_settings)
                        elif label == "Options":
                            menu_state = "OPTIONS"
                        elif label == "Quit":
                            running = False
            continue

        if menu_state == "OPTIONS":
            active_tab = menu_renderer.option_tabs[menu_renderer.option_tab_index]
            for field in menu_renderer.option_fields[active_tab]:
                field.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                tab_rects = get_tab_rects()
                for index, rect in tab_rects.items():
                    if rect.collidepoint(event.pos):
                        menu_renderer.option_tab_index = index

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    menu_renderer.option_tab_index = (menu_renderer.option_tab_index + 1) % len(menu_renderer.option_tabs)
                elif event.key == pygame.K_LEFT:
                    menu_renderer.option_tab_index = (menu_renderer.option_tab_index - 1) % len(menu_renderer.option_tabs)
                elif event.key == pygame.K_ESCAPE:
                    menu_state = "HOME"
                elif event.key == pygame.K_RETURN:
                    custom_volcano_settings = menu_renderer.get_current_option_values()
                    menu_state = "HOME"
            continue

        if world is None:
            continue

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_r:
                if world.selected_structure:
                    repaired = world.selected_structure.repair()
                    print(f"Repaired {world.selected_structure.name} for {repaired} HP")

            if event.key == pygame.K_LEFT:
                world.current_player_index = (world.current_player_index - 1) % len(world.players)
                print("Current player:", world.get_current_player().name)

            if event.key == pygame.K_RIGHT:
                world.current_player_index = (world.current_player_index + 1) % len(world.players)
                print("Current player:", world.get_current_player().name)

            if event.key == pygame.K_RETURN:
                if world.game_state in [GAME_STATES["PAUSED"], GAME_STATES["BUILDING_PLACEMENT"]]:
                    world.game_state = GAME_STATES["PLAYING"]
                    print("Simulation resumed")
                elif world.game_state == GAME_STATES["PLAYING"]:
                    world.game_state = GAME_STATES["PAUSED"]
                    print("Simulation paused")

            if event.key == pygame.K_b:
                if world.game_state in (GAME_STATES["PLAYING"], GAME_STATES["PAUSED"]):
                    world.game_state = GAME_STATES["BUILDING_PLACEMENT"]
                    world.build_structure_type = None
                    print("Building mode")
                elif world.game_state == GAME_STATES["BUILDING_PLACEMENT"]:
                    world.game_state = GAME_STATES["PLAYING"]
                    world.build_structure_type = None
                    print("Building mode cancelled")

            if event.key >= pygame.K_1 and event.key <= pygame.K_9 and world.game_state == GAME_STATES["BUILDING_PLACEMENT"]:
                buildable_types = renderer.get_buildable_types()
                number = event.key - pygame.K_1
                if number < len(buildable_types):
                    world.build_structure_type = buildable_types[number]
                    print("Selected building:", world.build_structure_type)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1:
                continue

            if world.game_state == GAME_STATES["BUILDING_PLACEMENT"]:
                if world.build_structure_type is None:
                    continue
                grid_x, grid_y = renderer.screen_to_grid(*event.pos)
                placed = world.build_structure(world.build_structure_type, grid_x, grid_y)
                if placed:
                    print(f"Placed {world.build_structure_type} at ({grid_x}, {grid_y})")
                else:
                    print("Cannot build there")
                continue

            structure = renderer.get_clicked_structure(event.pos)
            if structure is None:
                continue

            if world.game_state == GAME_STATES["CITY_SELECTION"]:
                claimed = world.claim_city(structure)
                if claimed:
                    print(structure.owner.name, "selected", structure.name)

            if world.game_state in (GAME_STATES["PLAYING"], GAME_STATES["PAUSED"]):
                world.selected_structure = structure
                switched = world.select_player_from_structure(structure)
                if switched:
                    print("Current player:", world.get_current_player().name)

    if world is not None and world.game_state == GAME_STATES["PLAYING"]:
        day_timer += 1
        if day_timer >= 10:
            for _ in range(SIMULATION_SPEED):
                world.update()
            day_timer = 0

    if menu_state == "HOME":
        menu_renderer.draw_home_screen(screen, home_buttons)
    elif menu_state == "OPTIONS":
        menu_renderer.draw_options_screen(screen)
    elif renderer is not None:
        renderer.draw(screen)

    pygame.display.flip()
    clock.tick(60)


pygame.quit()
