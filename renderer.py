import pygame

from terrain import TERRAIN_TYPES
from infrastructure import INFRASTRUCTURE_TYPES
from constants import GAME_STATES, VOLCANO_DEFAULTS


class OptionTextField:
    def __init__(self, label, value, x, y, width=220, height=32, default=None):
        self.label = label
        self.value = str(value)
        self.default = default
        self.rect = pygame.Rect(x, y, width, height)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if not self.active:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_TAB, pygame.K_ESCAPE):
                self.active = False
            elif event.unicode and event.unicode.isprintable():
                self.value += event.unicode

    def draw(self, screen, font):
        label = font.render(self.label, True, (255, 255, 255))
        screen.blit(label, (self.rect.x - 180, self.rect.y + 6))
        colour = (80, 100, 130)
        if self.active:
            colour = (110, 140, 170)
        pygame.draw.rect(screen, colour, self.rect, 2)
        text = font.render(self.value, True, (255, 255, 255))
        screen.blit(text, (self.rect.x + 8, self.rect.y + 6))

    def parse_value(self):
        if self.default is None:
            return self.value
        if isinstance(self.default, tuple):
            raw = self.value.strip()
            parts = [part.strip() for part in raw.split(",") if part.strip()]
            if len(parts) == 2:
                try:
                    return (int(parts[0]), int(parts[1]))
                except ValueError:
                    pass
            return self.default
        if isinstance(self.default, int):
            try:
                return int(self.value)
            except ValueError:
                return self.default
        if isinstance(self.default, float):
            try:
                return float(self.value)
            except ValueError:
                return self.default
        return self.value


class MenuRenderer:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.option_tabs = list(VOLCANO_DEFAULTS.keys())
        self.option_tab_index = 0
        self.option_fields = self.build_option_fields()

    def build_option_fields(self):
        fields = {}
        for tab_name in self.option_tabs:
            group = VOLCANO_DEFAULTS[tab_name]
            fields[tab_name] = []
            for index, (name, value) in enumerate(group.items()):
                fields[tab_name].append(
                    OptionTextField(name, value, 260, 120 + index * 52, default=value)
                )
        return fields

    def get_current_option_values(self):
        values = {}
        for tab_name in self.option_tabs:
            values[tab_name] = {}
            for field in self.option_fields[tab_name]:
                values[tab_name][field.label] = field.parse_value()
        return values

    def draw_home_screen(self, screen, home_buttons):
        surface = pygame.Surface((self.screen_width, self.screen_height))
        for y in range(0, self.screen_height, 4):
            for x in range(0, self.screen_width, 4):
                value = (x * 0.15 + y * 0.10) % 1.0
                if value < 0.35:
                    colour = (25, 40, 50)
                elif value < 0.6:
                    colour = (40, 65, 45)
                else:
                    colour = (55, 80, 70)
                pygame.draw.rect(surface, colour, (x, y, 4, 4))

        screen.blit(surface, (0, 0))

        title = pygame.font.SysFont(None, 72).render("Volcano Hazard", True, (255, 255, 255))
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 80))

        for label, rect in home_buttons.items():
            pygame.draw.rect(screen, (80, 120, 180), rect, border_radius=12)
            text = pygame.font.SysFont(None, 34).render(label, True, (255, 255, 255))
            screen.blit(text, (rect.x + rect.width // 2 - text.get_width() // 2, rect.y + 18))

    def draw_options_screen(self, screen):
        screen.fill((15, 20, 25))

        for index, tab_name in enumerate(self.option_tabs):
            rect = pygame.Rect(50 + index * 190, 30, 180, 42)
            colour = (110, 140, 180) if index == self.option_tab_index else (70, 90, 120)
            pygame.draw.rect(screen, colour, rect, border_radius=8)
            text = pygame.font.SysFont(None, 22).render(tab_name, True, (255, 255, 255))
            screen.blit(text, (rect.x + 12, rect.y + 10))

        active_tab = self.option_tabs[self.option_tab_index]
        for field in self.option_fields[active_tab]:
            field.draw(screen, pygame.font.SysFont(None, 24))

        save_text = pygame.font.SysFont(None, 28).render(
            "Press Enter to apply and return",
            True,
            (200, 200, 200),
        )
        screen.blit(save_text, (50, self.screen_height - 50))


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
            self.screen_width -
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
                int(
                    self.screen_height *
                    0.035
                )
            )
        )

        self.small_font = pygame.font.SysFont(
            None,
            max(
                16,
                int(
                    self.screen_height *
                    0.022
                )
            )
        )

        #
        # Terrain
        #

        self.terrain_surface = (
            self.create_terrain_surface()
        )

    # =================================================
    # BUILDING TYPES
    # =================================================

    def get_buildable_types(self):

        return list(
            INFRASTRUCTURE_TYPES.keys()
        )

    # =================================================
    # SCREEN -> GRID
    # =================================================

    def screen_to_grid(
        self,
        mouse_x,
        mouse_y
    ):

        if mouse_x < 0:
            return -1, -1

        if mouse_x >= self.map_width:
            return -1, -1

        if mouse_y < 0:
            return -1, -1

        if mouse_y >= self.screen_height:
            return -1, -1

        world_x = (
            mouse_x /
            self.scale_x
        )

        world_y = (
            mouse_y /
            self.scale_y
        )

        cell_size = (
            self.world.terrain.cell_size
        )

        grid_x = int(
            world_x /
            cell_size
        )

        grid_y = int(
            world_y /
            cell_size
        )

        return grid_x, grid_y

    # =================================================
    # GRID -> SCREEN RECT
    # =================================================

    def grid_to_screen_rect(
        self,
        x,
        y,
        width,
        height
    ):

        cell = (
            self.world.terrain.cell_size
        )

        return pygame.Rect(

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
                    width *
                    cell *
                    self.scale_x
                )
            ),

            max(
                1,
                int(
                    height *
                    cell *
                    self.scale_y
                )
            )
        )

    # =================================================
    # CLICKED STRUCTURE
    # =================================================

    def get_clicked_structure(
        self,
        mouse_position
    ):

        mx, my = mouse_position

        #
        # Ignore sidebar
        #

        if mx >= self.map_width:
            return None

        for structure in self.world.infrastructure:

            if structure.destroyed:
                continue

            x, y = structure.position
            w, h = structure.size

            rect = self.grid_to_screen_rect(
                x,
                y,
                w,
                h
            )

            if rect.collidepoint(
                mx,
                my
            ):
                return structure

        return None

    # =================================================
    # TERRAIN
    # =================================================

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

                h = terrain.height_map[
                    y,
                    x
                ]

                colour = None

                for (
                    terrain_type,
                    data
                ) in sorted(
                    TERRAIN_TYPES.items(),
                    key=lambda item:
                    item[1]["level"]
                ):

                    if h < data["level"]:

                        colour = data[
                            "colour"
                        ]

                        break

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
                        x *
                        terrain.cell_size,

                        y *
                        terrain.cell_size,

                        terrain.cell_size,

                        terrain.cell_size
                    )
                )

        return surface

    # =================================================
    # DRAW EVERYTHING
    # =================================================

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

        self.draw_build_preview(screen)

        self.draw_sidebar(screen)

    # =================================================
    # TERRAIN
    # =================================================

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
            (0, 0)
        )

    # =================================================
    # VOLCANO
    # =================================================

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
                    int(
                        x *
                        self.scale_x
                    ),

                    int(
                        y *
                        self.scale_y
                    )
                ),

                6
            )

    # =================================================
    # LAVA
    # =================================================

    def draw_lava(
        self,
        screen
    ):

        cell = (
            self.world.terrain.cell_size
        )

        for y in range(
            self.world.grid_height
        ):

            for x in range(
                self.world.grid_width
            ):

                lava = (
                    self.world.grid[y][x]["lava"]
                )

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

    # =================================================
    # ASH
    # =================================================

    def draw_ash(
        self,
        screen
    ):

        cell = (
            self.world.terrain.cell_size
        )

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

                ash = (
                    self.world.grid[y][x]["ash"]
                )

                if ash <= 0:
                    continue

                alpha = max(
                    20,
                    min(
                        180,
                        int(
                            ash *
                            180
                        )
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
            (0, 0)
        )

    # =================================================
    # INFRASTRUCTURE
    # =================================================

    def draw_structures(
        self,
        screen
    ):

        drawn = set()

        for y in range(
            self.world.grid_height
        ):

            for x in range(
                self.world.grid_width
            ):

                structure = (
                    self.world.grid[y][x][
                        "structure"
                    ]
                )

                if structure is None:
                    continue

                if structure.destroyed:
                    continue

                if structure in drawn:
                    continue

                drawn.add(structure)

                colour = structure.colour

                if structure.owner:

                    colour = (
                        structure.owner.colour
                    )

                sx, sy = structure.position

                w, h = structure.size

                rect = self.grid_to_screen_rect(
                    sx,
                    sy,
                    w,
                    h
                )

                pygame.draw.rect(
                    screen,
                    colour,
                    rect,
                    3
                )

                #
                # Health
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

                        self.draw_health_text(
                            screen,
                            structure,
                            rect
                        )

                #
                # City selection
                #

                if (
                    self.world.game_state ==
                    GAME_STATES[
                        "CITY_SELECTION"
                    ]

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

    # =================================================
    # BUILD PREVIEW
    # =================================================

    def draw_build_preview(
        self,
        screen
    ):

        if (
            self.world.game_state !=
            GAME_STATES[
                "BUILDING_PLACEMENT"
            ]
        ):
            return

        structure_type = (
            self.world.build_structure_type
        )

        if structure_type is None:
            return

        mouse_x, mouse_y = (
            pygame.mouse.get_pos()
        )

        if mouse_x >= self.map_width:
            return

        grid_x, grid_y = (
            self.screen_to_grid(
                mouse_x,
                mouse_y
            )
        )

        data = INFRASTRUCTURE_TYPES[
            structure_type
        ]

        width, height = data[
            "size"
        ]

        valid = self.world.can_build(
            structure_type,
            grid_x,
            grid_y
        )

        #
        # Grey regardless of validity.
        # Valid = lighter, invalid = darker.
        #

        if valid:

            fill_colour = (
                180,
                180,
                180,
                70
            )

            outline_colour = (
                200,
                200,
                200,
                220
            )

        else:

            fill_colour = (
                80,
                80,
                80,
                70
            )

            outline_colour = (
                100,
                100,
                100,
                220
            )

        rect = self.grid_to_screen_rect(

            grid_x,
            grid_y,
            width,
            height

        )

        preview_surface = pygame.Surface(
            screen.get_size(),
            pygame.SRCALPHA
        )

        pygame.draw.rect(

            preview_surface,

            fill_colour,

            rect
        )

        pygame.draw.rect(

            preview_surface,

            outline_colour,

            rect,

            2
        )

        screen.blit(
            preview_surface,
            (0, 0)
        )

    # =================================================
    # HEALTH BAR
    # =================================================

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

    # =================================================
    # HEALTH TEXT
    # =================================================

    def draw_health_text(
        self,
        screen,
        structure,
        rect
    ):

        text = self.small_font.render(

            f"{int(structure.health)}/"
            f"{int(structure.max_health)}",

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

    # =================================================
    # EARTHQUAKES
    # =================================================

    def draw_earthquakes(
        self,
        screen
    ):

        earthquakes = (
            self.world.get_player_earthquakes(
                self.world.players
            )
        )

        for earthquake in earthquakes:

            x, y = earthquake[
                "location"
            ]

            pygame.draw.circle(

                screen,

                (
                    0,
                    0,
                    0
                ),

                (
                    int(
                        x *
                        self.scale_x
                    ),

                    int(
                        y *
                        self.scale_y
                    )
                ),

                max(
                    5,
                    int(
                        earthquake[
                            "magnitude"
                        ]
                    )
                )
            )

    # =================================================
    # SIDEBAR
    # =================================================

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

        if (
            self.world.game_state ==
            GAME_STATES[
                "BUILDING_PLACEMENT"
            ]
        ):

            self.draw_build_menu(
                screen
            )

        else:

            self.draw_normal_sidebar(
                screen
            )

    # =================================================
    # NORMAL SIDEBAR
    # =================================================

    def draw_normal_sidebar(
        self,
        screen
    ):

        x = self.map_width

        title = self.font.render(

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
                x + 20,
                25
            )
        )

        y = 75

        #
        # Current player
        #

        current_player = (
            self.world.get_current_player()
        )

        if current_player:

            text = self.small_font.render(

                f"Current: "
                f"{current_player.name}",

                True,

                current_player.colour
            )

            screen.blit(

                text,

                (
                    x + 20,
                    y
                )
            )

            y += 30

            text = self.small_font.render(

                f"Money: "
                f"${int(current_player.money)}",

                True,

                (
                    255,
                    215,
                    0
                )
            )

            screen.blit(

                text,

                (
                    x + 20,
                    y
                )
            )

            y += 30

            text = self.small_font.render(

                f"Income: "
                f"${int(current_player.income)}/day",

                True,

                (
                    0,
                    255,
                    0
                )
            )

            screen.blit(

                text,

                (
                    x + 20,
                    y
                )
            )

            y += 45

        #
        # Players
        #

        text = self.small_font.render(

            "Players",

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
                x + 20,
                y
            )
        )

        y += 30

        for player in self.world.players:

            if player is current_player:

                prefix = "> "

            else:

                prefix = ""

            text = self.small_font.render(

                f"{prefix}"
                f"{player.name}   "
                f"${int(player.money)}   "
                f"+${int(player.income)}/day",

                True,

                player.colour
            )

            screen.blit(

                text,

                (
                    x + 20,
                    y
                )
            )

            y += 30

        #
        # State
        #

        y += 15

        text = self.small_font.render(

            f"State: "
            f"{self.world.get_world_state_name()}",

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
                x + 20,
                y
            )
        )

        y += 30

        #
        # Day
        #

        text = self.small_font.render(

            f"Day: {self.world.day}",

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
                x + 20,
                y
            )
        )

        y += 30

        #
        # Volcanoes
        #

        text = self.small_font.render(

            f"Volcanoes: "
            f"{len(self.world.volcanoes)}",

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
                x + 20,
                y
            )
        )

        y += 35

        #
        # Today's events
        #

        text = self.small_font.render(

            "Today:",

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
                x + 20,
                y
            )
        )

        y += 30

        events = [

            f"Earthquakes: "
            f"{len(self.world.recent_earthquakes)}",

            f"Eruptions: "
            f"{len(self.world.recent_eruptions)}"

        ]

        for line in events:

            text = self.small_font.render(

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
                    x + 20,
                    y
                )
            )

            y += 30

        #
        # Wind
        #

        y += 10

        #
        # Wind information
        #

        wind_direction = self.world.vector_to_compass(
            self.world.wind_direction
        )

        wind_text = self.small_font.render(

            f"Wind: {wind_direction} "
            f"at {self.world.wind_speed:.1f} m/s",

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
                x + 20,
                y
            )

        )

        y += 40

    # =================================================
    # BUILD MENU
    # =================================================

    def draw_build_menu(
        self,
        screen
    ):

        x = self.map_width

        #
        # Title
        #

        title = self.font.render(

            "Build",

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
                x + 20,
                25
            )
        )

        y = 75

        #
        # Current player
        #

        player = (
            self.world.get_current_player()
        )

        if player:

            text = self.small_font.render(

                f"Player: "
                f"{player.name}",

                True,

                player.colour
            )

            screen.blit(

                text,

                (
                    x + 20,
                    y
                )
            )

            y += 30

            text = self.small_font.render(

                f"Money: "
                f"${int(player.money)}",

                True,

                (
                    255,
                    215,
                    0
                )
            )

            screen.blit(

                text,

                (
                    x + 20,
                    y
                )
            )

            y += 40

        #
        # Instructions
        #

        text = self.small_font.render(

            "Select a building:",

            True,

            (
                200,
                200,
                200
            )
        )

        screen.blit(

            text,

            (
                x + 20,
                y
            )
        )

        y += 35

        #
        # Infrastructure dictionary order
        #

        buildable_types = (
            self.get_buildable_types()
        )

        for number, structure_type in enumerate(

            buildable_types,

            start=1

        ):

            data = INFRASTRUCTURE_TYPES[
                structure_type
            ]

            selected = (
                structure_type ==
                self.world.build_structure_type
            )

            if selected:

                text_colour = (
                    255,
                    255,
                    255
                )

            else:

                text_colour = (
                    200,
                    200,
                    200
                )

            cost = data.get(
                "build_cost",
                0
            )

            text = self.small_font.render(

                f"{number}. "
                f"{structure_type} "
                f"${cost}",

                True,

                text_colour
            )

            screen.blit(

                text,

                (
                    x + 20,
                    y
                )
            )

            y += 32

        #
        # Selected building
        #

        if self.world.build_structure_type:

            y += 20

            text = self.small_font.render(

                f"Selected: "
                f"{self.world.build_structure_type}",

                True,

                (
                    180,
                    180,
                    180
                )
            )

            screen.blit(

                text,

                (
                    x + 20,
                    y
                )
            )

        #
        # Controls
        #

        controls_y = (
            self.screen_height - 70
        )

        text = self.small_font.render(

            "B: Exit build mode",

            True,

            (
                180,
                180,
                180
            )
        )

        screen.blit(

            text,

            (
                x + 20,
                controls_y
            )
        )