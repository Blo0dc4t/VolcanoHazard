import json

import pygame

from terrain import TERRAIN_TYPES
from infrastructure import INFRASTRUCTURE_TYPES
from constants import (
    GAME_STATES,
    GENERAL_DEFAULTS,
    INFRASTRUCTURE_TYPES,
    TERRAIN_TYPES,
    VOLCANO_DEFAULTS,
    WORLD_DEFAULTS,
)


class OptionTextField:
    def __init__(self, label, value, x, y, width=220, height=32, default=None):
        self.label = label
        if isinstance(value, list):
            self.value = json.dumps(value)
        else:
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
        screen.blit(label, (self.rect.x - 350, self.rect.y + 6))
        colour = (80, 100, 130)
        if self.active:
            colour = (110, 140, 170)
        pygame.draw.rect(screen, colour, self.rect, 2)
        text = font.render(self.value, True, (255, 255, 255))
        screen.blit(text, (self.rect.x + 8, self.rect.y + 6))

    def parse_value(self):
        if self.default is None:
            return self.value
        if isinstance(self.default, list):
            try:
                parsed = json.loads(self.value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            return self.default
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
        self.option_groups = {
            "General": {
                "General": GENERAL_DEFAULTS["General"],
            },
            "World defaults": WORLD_DEFAULTS,
            "Volcano defaults": VOLCANO_DEFAULTS,
            "Infrastructure types": INFRASTRUCTURE_TYPES,
            "Terrain types": TERRAIN_TYPES,
        }
        self.option_tabs = list(self.option_groups.keys())
        self.option_tab_index = 0
        self.option_scroll_offset = 0
        self.option_fields = self.build_option_fields()
        self.option_section_rects = {}

    def build_option_fields(self):
        fields = {}
        for tab_name, sections in self.option_groups.items():
            fields[tab_name] = {}
            for section_name, group in sections.items():
                fields[tab_name][section_name] = []
                for name, value in group.items():
                    fields[tab_name][section_name].append(
                        OptionTextField(name, value, 500, 0, default=value)
                    )
        return fields

    def get_current_option_values(self):
        values = {}
        for tab_name in self.option_tabs:
            values[tab_name] = {}
            for section_name, fields in self.option_fields[tab_name].items():
                values[tab_name][section_name] = {}
                for field in fields:
                    values[tab_name][section_name][field.label] = field.parse_value()
        return values

    def get_tab_rects(self):
        return {
            index: pygame.Rect(50 + index * 190, 30, 180, 42)
            for index in range(len(self.option_tabs))
        }

    def handle_option_event(self, event):
        active_tab = self.option_tabs[self.option_tab_index]

        if event.type == pygame.MOUSEBUTTONDOWN:
            for index, rect in self.get_tab_rects().items():
                if rect.collidepoint(event.pos):
                    self.option_tab_index = index
                    self.option_scroll_offset = 0
                    return

        if event.type == pygame.MOUSEWHEEL:
            self.option_scroll_offset -= event.y * 35
            self.option_scroll_offset = max(
                0,
                min(self.option_scroll_offset, self.get_max_scroll())
            )
            return

        for fields in self.option_fields[active_tab].values():
            for field in fields:
                field.handle_event(event)

    def get_max_scroll(self):
        active_tab = self.option_tabs[self.option_tab_index]
        content_height = 25

        for fields in self.option_fields[active_tab].values():
            content_height += 40 + len(fields) * 52 + 15

        visible_height = self.screen_height - 190
        return max(0, content_height - visible_height)

    def draw_option_fields(self, screen):
        active_tab = self.option_tabs[self.option_tab_index]
        y = 105 - self.option_scroll_offset
        self.option_section_rects = {}
        field_font = pygame.font.SysFont(None, 24)
        section_font = pygame.font.SysFont(None, 28)
        content_rect = pygame.Rect(
            0,
            82,
            self.screen_width,
            self.screen_height - 140
        )
        previous_clip = screen.get_clip()
        screen.set_clip(content_rect)

        for section_name, fields in self.option_fields[active_tab].items():
            section_text = section_font.render(section_name, True, (220, 180, 90))
            screen.blit(section_text, (70, y))
            y += 40
            self.option_section_rects[section_name] = pygame.Rect(70, y - 40, 300, 32)

            for field in fields:
                field.rect.y = y
                field.draw(screen, field_font)
                y += 52

            y += 15

        screen.set_clip(previous_clip)

        if self.get_max_scroll() > 0:
            scrollbar_height = max(
                30,
                int(content_rect.height * content_rect.height /
                    (content_rect.height + self.get_max_scroll()))
            )
            scrollbar_range = content_rect.height - scrollbar_height
            scrollbar_y = content_rect.y + int(
                scrollbar_range * self.option_scroll_offset / self.get_max_scroll()
            )
            pygame.draw.rect(
                screen,
                (110, 140, 180),
                (self.screen_width - 18, scrollbar_y, 8, scrollbar_height),
                border_radius=4
            )

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
            rect = self.get_tab_rects()[index]
            colour = (110, 140, 180) if index == self.option_tab_index else (70, 90, 120)
            pygame.draw.rect(screen, colour, rect, border_radius=8)
            text = pygame.font.SysFont(None, 22).render(tab_name, True, (255, 255, 255))
            screen.blit(text, (rect.x + 12, rect.y + 10))

        self.draw_option_fields(screen)

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
        sidebar_fraction=None
    ):

        self.world = world

        surface = pygame.display.get_surface()

        self.screen_width = surface.get_width()
        self.screen_height = surface.get_height()

        #
        # Sidebar
        #

        if sidebar_fraction is None:
            sidebar_fraction = GENERAL_DEFAULTS["General"]["sidebar_fraction"]

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

        for index, volcano in enumerate(self.world.volcanoes):

            x, y = volcano.caldera_position
            screen_position = (
                int(x * self.scale_x),
                int(y * self.scale_y)
            )

            pygame.draw.circle(

                screen,

                (255, 255, 255),
                screen_position,
                12
            )

            pygame.draw.circle(

                screen,

                (255, 0, 0),
                screen_position,
                8
            )

            label = self.small_font.render(
                f"V{index + 1}",
                True,
                (255, 255, 255)
            )

            screen.blit(
                label,
                (
                    screen_position[0] + 14,
                    screen_position[1] - label.get_height() // 2
                )
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

                if structure.owner:
                    border_colour = structure.owner.colour
                    connected = (
                        structure in structure.owner.connected_structures
                    )

                    if connected:
                        fill_colour = tuple(
                            min(255, channel + (255 - channel) // 3)
                            for channel in border_colour
                        )
                    else:
                        fill_colour = tuple(
                            max(35, channel // 3)
                            for channel in border_colour
                        )
                else:
                    border_colour = structure.colour
                    fill_colour = structure.colour

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
                    fill_colour,
                    rect
                )

                pygame.draw.rect(
                    screen,
                    border_colour,
                    rect,
                    3
                )

                if structure.owner and structure.type in (
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

        if self.world.build_rotation % 2:
            width, height = height, width

        valid = self.world.can_build(
            structure_type,
            grid_x,
            grid_y,
            (width, height)
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

        health_text = (
            f"{int(structure.health)}/{int(structure.max_health)}"
        )
        font_size = min(18, max(8, rect.height - 4))
        font = pygame.font.Font(None, font_size)

        while (
            font_size > 8
            and (
                font.size(health_text)[0] > rect.width - 4
                or font.size(health_text)[1] > rect.height - 4
            )
        ):
            font_size -= 1
            font = pygame.font.Font(None, font_size)

        text = font.render(
            health_text,
            True,
            (255, 255, 255)
        )

        text_rect = text.get_rect(center=rect.center)

        screen.blit(
            text,
            text_rect
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