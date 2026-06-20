from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pygame

try:
    from volcano_expansion import VolcanoExpansion
except Exception:
    VolcanoExpansion = None


WIDTH = 1280
HEIGHT = 820
BOARD = pygame.Rect(40, 120, 760, 580)
PANEL = pygame.Rect(840, 40, 400, 740)
COLS = 14
ROWS = 10
START_MONEY = 1000
MOVE_COST_PER_TILE = 18

ROOT = Path(__file__).resolve().parent
LEADERBOARD_FILE = ROOT / "leaderboard.json"
SETTINGS_FILE = ROOT / "settings.json"

BG = (18, 26, 34)
PANEL_BG = (27, 35, 46)
PANEL_ALT = (38, 47, 61)
TEXT = (240, 245, 250)
MUTED = (182, 192, 204)
ACCENT = (247, 184, 78)
GOOD = (108, 214, 137)
BAD = (240, 96, 82)
WATER = (30, 94, 145)
WATER_ALT = (24, 76, 121)
LAND = (87, 125, 72)
LAND_EDGE = (58, 94, 51)
GRID = (220, 228, 235)
HOUSE = (250, 220, 130)
HOUSE_EDGE = (32, 28, 16)


@dataclass
class Player:
    name: str
    money: int = START_MONEY
    house: tuple[int, int] | None = None
    alive: bool = True
    survived_rounds: int = 0
    eliminated_round: int | None = None
    color: tuple[int, int, int] = (255, 255, 255)
    levee_active: bool = False
    insured: bool = False


@dataclass(frozen=True)
class Hazard:
    name: str
    damage: int
    pattern: str
    spread: int
    description: str


# Hazards are loaded from `settings.json` at runtime and exposed on each Game
# instance via `self.hazards` and `self.hazard_by_name`.


def make_fonts() -> dict[str, pygame.font.Font]:
    return {
        "title": pygame.font.SysFont("dejavusans", 30, bold=True),
        "body": pygame.font.SysFont("dejavusans", 22),
        "small": pygame.font.SysFont("dejavusans", 18),
        "tiny": pygame.font.SysFont("dejavusans", 15),
    }


def load_leaderboard() -> list[dict]:
    if not LEADERBOARD_FILE.exists():
        return []
    try:
        with LEADERBOARD_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def save_leaderboard(records: list[dict]) -> None:
    with LEADERBOARD_FILE.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2)


def push_leaderboard(players: list[Player], rounds: int, winner: str | None) -> None:
    records = load_leaderboard()
    stamp = datetime.now().isoformat(timespec="seconds")
    for player in players:
        records.append(
            {
                "name": player.name,
                "survived_rounds": player.survived_rounds,
                "final_money": player.money,
                "result": "winner" if player.name == winner else "played",
                "rounds_played": rounds,
                "timestamp": stamp,
            }
        )
    save_leaderboard(records[-300:])


def center_point(col: int, row: int) -> tuple[float, float]:
    cell_w = BOARD.width / COLS
    cell_h = BOARD.height / ROWS
    return BOARD.x + col * cell_w + cell_w / 2, BOARD.y + row * cell_h + cell_h / 2


def cell_rect(col: int, row: int) -> pygame.Rect:
    cell_w = BOARD.width // COLS
    cell_h = BOARD.height // ROWS
    return pygame.Rect(BOARD.x + col * cell_w, BOARD.y + row * cell_h, cell_w, cell_h)


def point_in_poly(point: tuple[float, float], poly: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y):
            x_intersect = (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1
            if x < x_intersect:
                inside = not inside
    return inside


def generate_island() -> tuple[list[list[bool]], list[tuple[float, float]]]:
    for _ in range(80):
        center_x = BOARD.centerx + random.uniform(-16, 16)
        center_y = BOARD.centery + random.uniform(-16, 16)
        polygon: list[tuple[float, float]] = []
        vertices = random.randint(10, 14)
        radius_x = BOARD.width * random.uniform(0.33, 0.42)
        radius_y = BOARD.height * random.uniform(0.33, 0.42)
        offset = random.uniform(0, math.tau)
        for index in range(vertices):
            angle = offset + math.tau * index / vertices
            jitter = random.uniform(0.72, 1.16)
            polygon.append((center_x + math.cos(angle) * radius_x * jitter, center_y + math.sin(angle) * radius_y * jitter))

        land: list[list[bool]] = []
        for row in range(ROWS):
            row_cells = []
            for col in range(COLS):
                row_cells.append(point_in_poly(center_point(col, row), polygon))
            land.append(row_cells)

        if sum(1 for row in land for value in row if value) >= 26:
            return land, polygon

    raise RuntimeError("Failed to generate a playable island")


def hazard_cells(
    hazard: Hazard,
    origin: tuple[int, int],
    direction: tuple[int, int] | None = None,
) -> set[tuple[int, int]]:
    ox, oy = origin
    cells: set[tuple[int, int]] = set()
    if hazard.pattern == "square":
        for dy in range(-hazard.spread, hazard.spread + 1):
            for dx in range(-hazard.spread, hazard.spread + 1):
                cells.add((ox + dx, oy + dy))
    elif hazard.pattern == "diamond":
        for dy in range(-hazard.spread, hazard.spread + 1):
            for dx in range(-hazard.spread, hazard.spread + 1):
                if abs(dx) + abs(dy) <= hazard.spread:
                    cells.add((ox + dx, oy + dy))
    elif hazard.pattern == "cross":
        cells.add((ox, oy))
        for step in range(1, hazard.spread + 1):
            cells.update({(ox + step, oy), (ox - step, oy), (ox, oy + step), (ox, oy - step)})
    elif hazard.pattern == "line":
        direction = direction or (1, 0)
        for step in range(hazard.spread):
            cells.add((ox + direction[0] * step, oy + direction[1] * step))
    return {(x, y) for x, y in cells if 0 <= x < COLS and 0 <= y < ROWS}


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def pick_land_cell(pos: tuple[int, int], island: list[list[bool]]) -> tuple[int, int] | None:
    x, y = pos
    if not BOARD.collidepoint(x, y):
        return None
    col = int((x - BOARD.x) // (BOARD.width / COLS))
    row = int((y - BOARD.y) // (BOARD.height / ROWS))
    if 0 <= col < COLS and 0 <= row < ROWS and island[row][col]:
        return col, row
    return None


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Volcano Risk Manager")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.fonts = make_fonts()

        self.players: list[Player] = []
        self.input_text = ""
        self.state = "lobby"
        self.round_number = 1
        self.current_player_index = 0
        self.move_player_index = 0
        self.selected_move_cell: tuple[int, int] | None = None
        self.current_hazard: Hazard | None = None
        self.hazard_origin: tuple[int, int] | None = None
        self.hazard_direction: tuple[int, int] | None = None
        self.revealed_hazard: Hazard | None = None
        self.revealed_hazard_origin: tuple[int, int] | None = None
        self.revealed_hazard_direction: tuple[int, int] | None = None
        self.hazard_expires_at = 0.0
        self.move_queue: list[Player] = []
        self.expansion = VolcanoExpansion() if VolcanoExpansion is not None else None
        self.volcano_pos: tuple[int, int] | None = None
        self.volcano_revealed: bool = False
        self.show_settings: bool = False
        # default settings; actual hazards/weights are loaded from settings.json
        self.settings: dict = {"intensity": 1.0}
        self.settings_buttons: dict = {}
        self.last_hazard_probs: dict | None = None
        self.load_settings()
        self.normalize_settings()
        self.settings_scroll: int = 0
        self.settings_content_height: int = 0
        self.editing_desc: tuple[str, str] | None = None
        self.pattern_dropdown: str | None = None
        self.show_leaderboard: bool = True
        self.message = "Type a name and press Enter to join."
        self.message_until = time.time() + 9999
        self.island, self.outline = generate_island()
        self.leaderboard = load_leaderboard()
        self.last_round_summary = ""

    def _fallback_weighted_hazard_selection(self) -> None:
        # compute per-hazard and per-cell weights similar to the expansion but local
        rows = ROWS
        cols = COLS
        land_cells = [(x, y) for y in range(rows) for x in range(cols) if self.island[y][x]]
        if not land_cells:
            if not getattr(self, "hazards", None):
                raise RuntimeError("No hazards configured in settings.json")
            self.current_hazard = random.choice(self.hazards)
            self.hazard_origin = (0, 0)
            self.hazard_direction = None
            self.last_hazard_probs = {h.name: 1.0 / len(self.hazards) for h in self.hazards}
            return

        weights_map = {}
        totals = {}
        for h in self.hazards:
            name = h.name
            wlist = []
            tot = 0.0
            for c in land_cells:
                # use Manhattan normalized by grid diagonal
                d = manhattan(self.volcano_pos or (COLS // 2, ROWS // 2), c)
                maxd = math.hypot(COLS, ROWS)
                dnorm = min(1.0, d / (maxd or 1.0))
                ln = name.lower()
                if ln.startswith("ash"):
                    modifier = 0.6 + 1.4 * dnorm
                elif "pyro" in ln or "radius" in ln:
                    modifier = 1.6 - 1.2 * dnorm
                elif "lava" in ln or "mud" in ln:
                    modifier = 1.4 - 0.9 * dnorm
                else:
                    modifier = 1.0
                base = 1.0
                override = float(self.settings.get("weights", {}).get(name, 1.0))
                rboost = 1.0 + max(0.0, (self.round_number - 1)) * 0.03
                w = max(0.0, base * modifier * rboost) * override
                wlist.append(w)
                tot += w
            weights_map[name] = wlist
            totals[name] = tot

        total_all = sum(totals.values())
        probs = {name: (totals[name] / total_all if total_all > 0 else 1.0 / len(self.hazards)) for name in totals}
        # sample hazard
        names = list(totals.keys())
        hazard_weights = [totals[n] for n in names]
        if sum(hazard_weights) <= 0:
            chosen = random.choice(names)
        else:
            chosen = random.choices(names, weights=hazard_weights, k=1)[0]
        # sample epicenter
        cell_weights = weights_map[chosen]
        if sum(cell_weights) <= 0:
            epicenter = random.choice(land_cells)
        else:
            epicenter = random.choices(land_cells, weights=cell_weights, k=1)[0]
        # map name to Hazard
        for h in self.hazards:
            if h.name == chosen:
                # apply overrides
                overrides = self.settings.get("hazard_attrs", {}).get(h.name, {})
                dmg = int(overrides.get("damage", h.damage))
                spr = int(overrides.get("spread", h.spread))
                pat = overrides.get("pattern", h.pattern)
                desc = overrides.get("description", h.description)
                self.current_hazard = Hazard(h.name, dmg, pat, spr, desc)
                break
        else:
            if not getattr(self, "hazards", None):
                raise RuntimeError("No hazards configured in settings.json")
            h = random.choice(self.hazards)
            overrides = self.settings.get("hazard_attrs", {}).get(h.name, {})
            dmg = int(overrides.get("damage", h.damage))
            spr = int(overrides.get("spread", h.spread))
            pat = overrides.get("pattern", h.pattern)
            desc = overrides.get("description", h.description)
            self.current_hazard = Hazard(h.name, dmg, pat, spr, desc)
        self.hazard_origin = epicenter
        self.hazard_direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)]) if self.current_hazard.pattern == "line" else None
        self.last_hazard_probs = probs

    def set_message(self, text: str, seconds: float = 2.5) -> None:
        self.message = text
        self.message_until = time.time() + seconds

    def alive_players(self) -> list[Player]:
        return [player for player in self.players if player.money > 0]

    def occupied_cells(self) -> set[tuple[int, int]]:
        return {player.house for player in self.players if player.house is not None and player.money > 0}

    def reset_game(self) -> None:
        self.players.clear()
        self.input_text = ""
        self.state = "lobby"
        self.round_number = 1
        self.current_player_index = 0
        self.move_player_index = 0
        self.selected_move_cell = None
        self.current_hazard = None
        self.hazard_origin = None
        self.hazard_direction = None
        self.revealed_hazard = None
        self.revealed_hazard_origin = None
        self.revealed_hazard_direction = None
        self.hazard_expires_at = 0.0
        self.last_round_summary = ""
        self.island, self.outline = generate_island()
        self.set_message("Type a name and press Enter to join.", 2.5)

    def load_settings(self) -> None:
        try:
            if SETTINGS_FILE.exists():
                with SETTINGS_FILE.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    if isinstance(data, dict):
                        # optional increments/bounds config
                        if "increments_bounds" in data and isinstance(data["increments_bounds"], dict):
                            self.settings["increments_bounds"] = data["increments_bounds"]

                        # If file uses a single hazard_attrs section with per-hazard entries,
                        # parse those and populate weights and hazard_attrs accordingly.
                        if "hazard_attrs" in data and isinstance(data["hazard_attrs"], dict):
                            for hname, props in data["hazard_attrs"].items():
                                # per-hazard props may include weight/intensity/damage/spread/pattern/description
                                if isinstance(props, dict):
                                    # weight
                                    w = props.get("weight")
                                    if w is not None:
                                        try:
                                            self.settings.setdefault("weights", {})[hname] = float(w)
                                        except Exception:
                                            pass
                                    # copy numeric/other attrs
                                    entry = self.settings.setdefault("hazard_attrs", {}).setdefault(hname, {})
                                    for key in ("damage", "spread", "pattern", "description"):
                                        if key in props:
                                            entry[key] = props.get(key)
                        # Deprecated top-level 'weights'/'intensity' are no longer supported.
                        # All hazard configuration should be provided under 'hazard_attrs',
                        # and bounds/steps under 'increments_bounds'.
        except Exception:
            pass

    def save_settings(self) -> None:
        try:
            with SETTINGS_FILE.open("w", encoding="utf-8") as fh:
                json.dump(self.settings, fh, indent=2)
        except Exception:
            pass

    def normalize_settings(self) -> None:
        # Ensure settings include entries for all known hazards and for any hazards present
        # in the loaded settings file. Fill missing defaults from templates.
        weights = self.settings.setdefault("weights", {})
        hazard_attrs = self.settings.setdefault("hazard_attrs", {})

        # Ensure a weight entry exists for every hazard defined in settings
        for name in list(hazard_attrs.keys()):
            weights.setdefault(name, 1.0)

        # Fill missing attribute defaults and build runtime hazards list/mapping
        hazards: list[Hazard] = []
        hazard_by_name: dict[str, Hazard] = {}
        for name, attrs in list(hazard_attrs.items()):
            # ensure numeric defaults exist
            dmg = int(attrs.get("damage", 0) or 0)
            spr = int(attrs.get("spread", 0) or 0)
            pat = attrs.get("pattern", "square")
            desc = attrs.get("description", "")
            attrs.setdefault("damage", dmg)
            attrs.setdefault("spread", spr)
            attrs.setdefault("pattern", pat)
            attrs.setdefault("description", desc)
            # ensure per-hazard intensity and weight defaults
            attrs.setdefault("intensity", float(attrs.get("intensity", 1.0)))
            attrs.setdefault("weight", float(attrs.get("weight", 1.0)))
            # record mapping
            h = Hazard(name, dmg, pat, spr, desc)
            hazards.append(h)
            hazard_by_name[name] = h
            # populate weights map from attrs
            try:
                weights[name] = float(attrs.get("weight", 1.0))
            except Exception:
                weights[name] = 1.0

        # expose on the instance for runtime use
        self.hazards = hazards
        self.hazard_by_name = hazard_by_name
        self.settings["weights"] = weights
        self.settings["hazard_attrs"] = hazard_attrs
        # Ensure increments_bounds has sensible defaults
        ib = self.settings.setdefault("increments_bounds", {})
        ib.setdefault("intensity", {"min": 0.2, "max": 3.0, "increment": 0.1})
        ib.setdefault("weights", {"min": 0.05, "max": 3.0, "increment": 0.05})
        ib.setdefault("damage", {"min": 0, "max": None, "increment": 5})
        ib.setdefault("spread", {"min": 0, "max": None, "increment": 1})
        self.settings["increments_bounds"] = ib

    def start_placement(self) -> None:
        self.state = "place"
        self.current_player_index = 0
        self.set_message(f"{self.players[0].name}, click a land square to place your house.", 2.5)

    def start_hazard_phase(self) -> None:
        self.revealed_hazard = None
        self.revealed_hazard_origin = None
        self.revealed_hazard_direction = None
        # If the volcano expansion is present, reveal the main volcano on the first round
        if self.expansion and not self.volcano_revealed:
            # place the main volcano and show it as the first-event epicenter
            try:
                self.volcano_pos = self.expansion.place_volcano(self.island)
            except Exception:
                self.volcano_pos = None
            if self.volcano_pos is not None:
                self.current_hazard = Hazard("Volcano", 0, "square", 0, "Main volcano revealed")
                self.hazard_origin = self.volcano_pos
                self.hazard_direction = None
                self.volcano_revealed = True
                self.state = "hazard"
                self.hazard_expires_at = time.time() + 1.3
                self.set_message(f"Round {self.round_number}: Main volcano revealed at {self.hazard_origin}.", 2.0)
                self.last_round_summary = ""
                return

        # Otherwise use the expansion to choose hazard + epicenter if available, else fallback to base behavior
        if self.expansion and self.volcano_revealed and self.volcano_pos is not None:
            try:
                spec, epicenter, probs = self.expansion.choose_hazard(
                    self.volcano_pos, self.island, self.round_number, weights=self.settings.get("weights", {})
                )
                # apply user overrides for hazard attributes
                hattrs = self.settings.get("hazard_attrs", {}).get(spec.get("name", ""), {})
                dmg = int(hattrs.get("damage", spec.get("damage", 0)))
                spr = int(hattrs.get("spread", spec.get("spread", 0)))
                pat = hattrs.get("pattern", spec.get("pattern", "square"))
                desc = hattrs.get("description", spec.get("description", ""))
                self.current_hazard = Hazard(spec["name"], dmg, pat, spr, desc)
                self.hazard_origin = epicenter
                self.hazard_direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)]) if self.current_hazard.pattern == "line" else None
                self.last_hazard_probs = probs
            except Exception:
                self._fallback_weighted_hazard_selection()
        else:
            self._fallback_weighted_hazard_selection()

        self.state = "hazard"
        self.hazard_expires_at = time.time() + 1.1
        self.set_message(f"Round {self.round_number}: {self.current_hazard.name} revealed.", 1.3)
        self.last_round_summary = ""

    def hazard_display_state(self) -> tuple[Hazard | None, tuple[int, int] | None, tuple[int, int] | None]:
        if self.state == "hazard":
            return self.current_hazard, self.hazard_origin, self.hazard_direction
        return self.revealed_hazard, self.revealed_hazard_origin, self.revealed_hazard_direction

    def draw_hazard_cells(self, hazard: Hazard, origin: tuple[int, int], direction: tuple[int, int] | None) -> None:
        styles = {
            "Ashfall": ((170, 178, 186), (228, 234, 240), "dot"),
            "Lava Spur": ((255, 137, 58), (255, 209, 96), "square"),
            "Bomb Shower": ((255, 182, 68), (255, 102, 74), "cross"),
            "Pyroclastic Surge": ((186, 85, 53), (242, 134, 77), "diamond"),
            "Mudflow": ((145, 111, 73), (205, 167, 103), "line"),
            "Radius Blast": ((231, 91, 66), (255, 170, 90), "ring"),
            "Volcano": ((214, 93, 46), (120, 20, 10), "volcano"),
        }
        accent, glow, marker = styles.get(hazard.name, ((255, 120, 80), (255, 200, 150), "ring"))
        for cell in hazard_cells(hazard, origin, direction):
            rect = cell_rect(*cell).inflate(-10, -10)
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((*accent, 90))
            self.screen.blit(overlay, rect.topleft)
            pygame.draw.rect(self.screen, accent, rect, 2, border_radius=8)

        center_rect = cell_rect(*origin).inflate(-16, -16)
        center = center_rect.center
        if marker == "dot":
            pygame.draw.circle(self.screen, glow, center, max(6, center_rect.width // 6))
            pygame.draw.circle(self.screen, accent, center, max(10, center_rect.width // 4), 2)
        elif marker == "square":
            pygame.draw.rect(self.screen, glow, center_rect.inflate(-10, -10), border_radius=6)
            pygame.draw.rect(self.screen, accent, center_rect.inflate(-4, -4), 2, border_radius=6)
        elif marker == "cross":
            pygame.draw.line(self.screen, glow, (center[0] - 12, center[1]), (center[0] + 12, center[1]), 4)
            pygame.draw.line(self.screen, glow, (center[0], center[1] - 12), (center[0], center[1] + 12), 4)
            pygame.draw.circle(self.screen, accent, center, 14, 2)
        elif marker == "diamond":
            points = [(center[0], center[1] - 16), (center[0] - 16, center[1]), (center[0], center[1] + 16), (center[0] + 16, center[1])]
            pygame.draw.polygon(self.screen, glow, points)
            pygame.draw.polygon(self.screen, accent, points, 2)
        elif marker == "line":
            pygame.draw.line(self.screen, glow, (center[0] - 14, center[1]), (center[0] + 14, center[1]), 5)
            pygame.draw.line(self.screen, accent, (center[0] - 18, center[1] - 7), (center[0] + 18, center[1] - 7), 2)
            pygame.draw.line(self.screen, accent, (center[0] - 18, center[1] + 7), (center[0] + 18, center[1] + 7), 2)
        elif marker == "volcano":
            tri = [(center[0], center[1] - 16), (center[0] - 16, center[1] + 16), (center[0] + 16, center[1] + 16)]
            pygame.draw.polygon(self.screen, glow, tri)
            pygame.draw.polygon(self.screen, accent, tri, 2)
        else:
            pygame.draw.circle(self.screen, glow, center, 12)
            pygame.draw.circle(self.screen, accent, center, 16, 2)

    def apply_hazard(self) -> None:
        if self.current_hazard is None or self.hazard_origin is None:
            return
        affected = hazard_cells(self.current_hazard, self.hazard_origin, self.hazard_direction)
        hit_names = []
        for player in self.players:
            if player.money <= 0 or player.house is None:
                continue
            if player.house in affected:
                # compute damage including intensity and mitigations
                base = self.current_hazard.damage
                # use per-hazard intensity if present in settings, else fallback to 1.0
                intensity = float(self.settings.get("hazard_attrs", {}).get(self.current_hazard.name, {}).get("intensity", 1.0))
                dmg = int(base * intensity)
                if player.levee_active:
                    dmg = dmg // 2
                    player.levee_active = False
                player.money = max(0, player.money - dmg)
                hit_names.append(player.name)
                # insurance reimburses half of dmg after hit
                if player.insured:
                    refund = dmg // 2
                    player.money += refund
                    player.insured = False
                if player.money == 0:
                    player.alive = False
                    player.eliminated_round = self.round_number
        if hit_names:
            self.last_round_summary = f"{self.current_hazard.name} hit: {', '.join(hit_names)} (-{self.current_hazard.damage})"
        else:
            self.last_round_summary = f"{self.current_hazard.name} landed, but no houses were hit."
        self.revealed_hazard = self.current_hazard
        self.revealed_hazard_origin = self.hazard_origin
        self.revealed_hazard_direction = self.hazard_direction
        self.current_hazard = None
        self.hazard_origin = None
        self.hazard_direction = None
        self.state = "move"
        self.move_queue = [player for player in self.players if player.money > 0]
        self.move_player_index = 0
        self.selected_move_cell = None

    def finish_round(self) -> None:
        for player in self.alive_players():
            player.survived_rounds += 1
        if len(self.alive_players()) <= 1:
            self.end_game()
            return
        self.round_number += 1
        self.start_hazard_phase()

    def end_game(self) -> None:
        winner = self.alive_players()[0].name if len(self.alive_players()) == 1 else None
        push_leaderboard(self.players, self.round_number, winner)
        self.leaderboard = load_leaderboard()
        if winner:
            self.set_message(f"{winner} wins. Press R to restart.", 4.0)
        else:
            self.set_message("No player has money left. Press R to restart.", 4.0)
        self.state = "game_over"

    def current_move_player(self) -> Player | None:
        if 0 <= self.move_player_index < len(self.move_queue):
            return self.move_queue[self.move_player_index]
        return None

    def _hazard_template(self, name: str) -> Hazard | None:
        return getattr(self, "hazard_by_name", {}).get(name)

    def _hazard_attr(self, hazard_name: str, key: str, fallback):
        attrs = self.settings.get("hazard_attrs", {}).get(hazard_name, {})
        if key in attrs:
            return attrs[key]
        template = self._hazard_template(hazard_name)
        if template is not None:
            return getattr(template, key, fallback)
        return fallback

    def _draw_stepper_controls(
        self,
        base_x: int,
        base_y: int,
        box_y_mod: int,
        label: str,
        value_text: str,
        value_style: str,
        label_offset_x: int,
    ) -> tuple[pygame.Rect, pygame.Rect]:
        dec_rect = pygame.Rect(base_x + label_offset_x, base_y + box_y_mod, 36, 28)
        inc_rect = pygame.Rect(base_x + label_offset_x + dec_rect.width + 10, base_y + box_y_mod, 36, 28)
        pygame.draw.rect(self.screen, PANEL_ALT, dec_rect)
        pygame.draw.rect(self.screen, PANEL_ALT, inc_rect)
        self.draw_text(label, "tiny", MUTED, (base_x, base_y))
        self.draw_text("-", "body", TEXT, (dec_rect.x + 10, dec_rect.y + 2))
        self.draw_text("+", "body", TEXT, (inc_rect.x + 10, inc_rect.y + 2))
        self.draw_text(value_text, value_style, MUTED, (base_x + label_offset_x + dec_rect.width + inc_rect.width + 20, base_y))
        return dec_rect, inc_rect

    def _draw_settings_hazard_row(self, sbox: pygame.Rect, name: str, weight: float, y: int, patterns: list[str]) -> int:
        template = self._hazard_template(name)
        attrs = self.settings.get("hazard_attrs", {}).get(name, {})

        self.draw_text(name, "small", TEXT, (sbox.x + 12, y))

        self.settings_buttons[name] = {}

        line_spacing = 30
        attr_x = sbox.x + 20
        attr_y = y + line_spacing
        box_y_mod = -6

        pattern_x = sbox.right - 260
        self.draw_text("Pattern", "tiny", MUTED, (pattern_x, attr_y))
        cur_pattern = attrs.get("pattern", template.pattern if template is not None else "square")
        pattern_rect = pygame.Rect(pattern_x, attr_y + box_y_mod, 96, 28)
        pygame.draw.rect(self.screen, PANEL_ALT, pattern_rect)
        self.draw_text(cur_pattern, "tiny", TEXT, (pattern_rect.x + 6, pattern_rect.y + 6))

        self.settings_buttons[name]["pattern"] = pattern_rect

        attr_rows = []
        # Determine numeric attribute keys to show: include any numeric-like keys
        # present in the hazard's attrs dict (exclude pattern/description).
        for k, v in attrs.items():
            # if k in {"pattern", "description"}:
            #     continue
            if isinstance(v, (int, float)):
                display = f"Value: {attrs.get(k, getattr(template, k, 0))}"
                label = k.replace("_", " ").capitalize()
                attr_rows.append((k, label, display))


        # for key in numeric_keys:
        #     if key == "damage":
        #         display = f"Dmg: {attrs.get('damage', template.damage if template is not None else 0)}"
        #         label = "Damage"
        #     elif key == "spread":
        #         display = f"Spr: {attrs.get('spread', template.spread if template is not None else 0)}"
        #         label = "Spread"
        #     elif key == "intensity":
        #         display = f"{float(attrs.get('intensity', 1.0)):.2f}x"
        #         label = "Intensity"
        #     else:
        #         display = str(attrs.get(key, ""))
        #         label = key.replace("_", " ").capitalize()
        #     attr_rows.append((key, label, display))

        for attr_key_name, name_text, var_text in attr_rows:
            dec_rect, inc_rect = self._draw_stepper_controls(
                attr_x,
                attr_y,
                box_y_mod,
                name_text,
                var_text,
                "tiny",
                100,
            )
            self.settings_buttons[name][f"dec_{attr_key_name}"] = dec_rect
            self.settings_buttons[name][f"inc_{attr_key_name}"] = inc_rect
            attr_y += line_spacing

        desc = attrs.get("description", template.description if template is not None else "")
        desc_rect = pygame.Rect(sbox.x + 12, attr_y + 28, sbox.width - 36, 44)
        self.draw_wrapped(desc, desc_rect, "tiny", MUTED)

        edit_rect = pygame.Rect(sbox.right - 160, attr_y + 28, 80, 24)
        pygame.draw.rect(self.screen, PANEL_ALT, edit_rect)
        self.draw_text("Edit desc", "tiny", TEXT, (edit_rect.x + 8, edit_rect.y + 4))

        self.settings_buttons[name]["edit_desc"] = edit_rect

        if self.pattern_dropdown == name:
            opt_rects = []
            opt_y = pattern_rect.y + 34
            for opt in patterns:
                opt_rect = pygame.Rect(pattern_rect.x, opt_y, pattern_rect.width, 28)
                pygame.draw.rect(self.screen, PANEL_ALT, opt_rect)
                self.draw_text(opt, "tiny", TEXT, (opt_rect.x + 6, opt_rect.y + 6))
                opt_rects.append(opt_rect)
                opt_y += 30
            self.settings_buttons[name]["pattern_opts"] = opt_rects

        return edit_rect.bottom + 12

    def draw_text(self, text: str, font_name: str, color: tuple[int, int, int], pos: tuple[int, int]) -> None:
        surface = self.fonts[font_name].render(text, True, color)
        self.screen.blit(surface, pos)

    def draw_wrapped(self, text: str, rect: pygame.Rect, font_name: str, color: tuple[int, int, int]) -> None:
        font = self.fonts[font_name]
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            trial = word if not current else f"{current} {word}"
            if font.size(trial)[0] <= rect.width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        y = rect.y
        for line in lines:
            self.screen.blit(font.render(line, True, color), (rect.x, y))
            y += font.get_height() + 4

    def draw_board(self) -> None:
        pygame.draw.rect(self.screen, WATER_ALT, BOARD.inflate(18, 18), border_radius=22)
        pygame.draw.polygon(self.screen, WATER, self.outline)
        cell_w = BOARD.width // COLS
        cell_h = BOARD.height // ROWS

        if self.island:
            for row in range(ROWS):
                for col in range(COLS):
                    rect = pygame.Rect(BOARD.x + col * cell_w, BOARD.y + row * cell_h, cell_w, cell_h)
                    if self.island[row][col]:
                        edge = any(
                            nx < 0 or ny < 0 or nx >= COLS or ny >= ROWS or not self.island[ny][nx]
                            for nx, ny in ((col - 1, row), (col + 1, row), (col, row - 1), (col, row + 1))
                        )
                        pygame.draw.rect(self.screen, LAND_EDGE if edge else LAND, rect)
                    else:
                        pygame.draw.rect(self.screen, WATER if (col + row) % 2 else WATER_ALT, rect)
                    pygame.draw.rect(self.screen, GRID, rect, 1)

        hazard, origin, direction = self.hazard_display_state()
        if hazard and origin:
            self.draw_hazard_cells(hazard, origin, direction)

        if self.state == "move" and self.selected_move_cell is not None:
            pygame.draw.rect(self.screen, GOOD, cell_rect(*self.selected_move_cell).inflate(-10, -10), 3, border_radius=8)

        for player in self.players:
            if player.house is None:
                continue
            rect = cell_rect(*player.house).inflate(-16, -16)
            pygame.draw.rect(self.screen, HOUSE, rect, border_radius=6)
            pygame.draw.rect(self.screen, HOUSE_EDGE, rect, 2, border_radius=6)
            label = self.fonts["tiny"].render(player.name[:7], True, HOUSE_EDGE)
            self.screen.blit(label, label.get_rect(center=rect.center))

        # draw volcano icon when revealed
        if self.volcano_pos is not None:
            vx, vy = self.volcano_pos
            cx, cy = center_point(vx, vy)
            size = min(BOARD.width / COLS, BOARD.height / ROWS) * 0.28
            tri = [(cx, cy - size), (cx - size, cy + size), (cx + size, cy + size)]
            pygame.draw.polygon(self.screen, (200, 60, 40), tri)
            pygame.draw.polygon(self.screen, (120, 20, 10), tri, 2)

        # HUD icons for mitigations on houses (draw after volcano so they are visible)
        for player in self.players:
            if player.house is None:
                continue
            rect = cell_rect(*player.house)
            dot_r = 6
            if player.levee_active:
                pygame.draw.circle(self.screen, (40, 140, 200), (rect.right - 12, rect.top + 12), dot_r)
            if player.insured:
                pygame.draw.circle(self.screen, (250, 200, 60), (rect.right - 28, rect.top + 12), dot_r)

    def draw_panel(self) -> None:
        pygame.draw.rect(self.screen, PANEL_BG, PANEL, border_radius=18)
        inner = PANEL.inflate(-24, -24)
        self.draw_text("Volcano Risk Manager", "title", ACCENT, (inner.x, inner.y))

        if time.time() < self.message_until:
            self.draw_text(self.message, "body", TEXT, (inner.x, inner.y + 42))
        # controls
        self.draw_text("Press O to toggle Settings", "tiny", MUTED, (inner.bottom + 100, inner.bottom - 10))

        if self.state == "lobby":
            self.draw_text("Lobby", "body", TEXT, (inner.x, inner.y + 82))
            self.draw_wrapped(
                "Add players by typing a name and pressing Enter. Use Backspace to edit. When at least two players are joined and the input is empty, press Enter to start.",
                pygame.Rect(inner.x, inner.y + 114, inner.width, 88),
                "small",
                MUTED,
            )
            pygame.draw.rect(self.screen, PANEL_ALT, pygame.Rect(inner.x, inner.y + 214, inner.width, 42), border_radius=10)
            self.draw_text(f"Name: {self.input_text}_", "body", GOOD if self.input_text else MUTED, (inner.x + 10, inner.y + 221))
        elif self.state == "place":
            player = self.players[self.current_player_index]
            self.draw_text(f"Placement turn: {player.name}", "body", ACCENT, (inner.x, inner.y + 82))
            self.draw_wrapped(
                f"Click a land square to place {player.name}'s house. Houses cannot overlap. Everyone starts with ${START_MONEY}.",
                pygame.Rect(inner.x, inner.y + 114, inner.width, 92),
                "small",
                MUTED,
            )
        elif self.state == "hazard":
            hazard = self.current_hazard
            if hazard:
                self.draw_text(f"Round {self.round_number}", "body", TEXT, (inner.x, inner.y + 82))
                self.draw_text(hazard.name, "body", BAD, (inner.x, inner.y + 120))
                self.draw_wrapped(hazard.description, pygame.Rect(inner.x, inner.y + 160, inner.width, 92), "small", MUTED)
                self.draw_text(f"Damage: ${hazard.damage}", "body", ACCENT, (inner.x, inner.y + 160))
                self.draw_text("Click a land square to reveal the hazard center.", "small", MUTED, (inner.x, inner.y + 192))
                probs = getattr(self, "last_hazard_probs", None)
                if probs:
                    y = inner.y + 230
                    self.draw_text("Selection probabilities:", "small", MUTED, (inner.x, y))
                    y += 18
                    for name, p in sorted(probs.items(), key=lambda kv: kv[1], reverse=True)[:6]:
                        self.draw_text(f"{name}: {p*100:.1f}%", "tiny", MUTED, (inner.x + 8, y))
                        y += 16
        elif self.state == "move":
            player = self.current_move_player()
            self.draw_text(f"Round {self.round_number}", "body", TEXT, (inner.x, inner.y + 82))
            if player:
                self.draw_text(f"Move: {player.name}", "body", GOOD, (inner.x, inner.y + 114))
                self.draw_wrapped(
                    f"Click a destination square to move, or press Enter to skip. Cost = Manhattan distance x ${MOVE_COST_PER_TILE}.",
                    pygame.Rect(inner.x, inner.y + 148, inner.width, 84),
                    "small",
                    MUTED,
                )
                if self.selected_move_cell is not None and player.house is not None:
                    cost = manhattan(player.house, self.selected_move_cell) * MOVE_COST_PER_TILE
                    self.draw_text(f"Selected move cost: ${cost}", "body", ACCENT, (inner.x, inner.y + 242))
                self.draw_text("Press S to skip your move.", "small", MUTED, (inner.x, inner.y + 222))
                # Mitigation purchase buttons
                buy_x = inner.x + 8
                buy_y = inner.y + 252
                levee_rect = pygame.Rect(buy_x, buy_y, 168, 34)
                ins_rect = pygame.Rect(buy_x, buy_y + 40, 168, 34)
                pygame.draw.rect(self.screen, PANEL_ALT, levee_rect, border_radius=8)
                pygame.draw.rect(self.screen, PANEL_ALT, ins_rect, border_radius=8)
                self.draw_text(f"Buy levee (${120})", "small", TEXT, (levee_rect.x + 10, levee_rect.y + 6))
                self.draw_text(f"Buy insurance (${80})", "small", TEXT, (ins_rect.x + 10, ins_rect.y + 6))
                # store for click handling
                self._mitigation_rects = {"levee": levee_rect, "insurance": ins_rect}
        elif self.state == "game_over":
            winner = self.alive_players()[0].name if len(self.alive_players()) == 1 else None
            self.draw_text("Game over", "body", TEXT, (inner.x, inner.y + 82))
            self.draw_text(f"Winner: {winner or 'none'}", "body", GOOD if winner else BAD, (inner.x, inner.y + 114))
            self.draw_text("Press R to restart or L to toggle the leaderboard.", "small", MUTED, (inner.x, inner.y + 148))

        # players section
        self.draw_text("Players", "body", ACCENT, (inner.x, inner.y + 392))
        y = inner.y + 424
        for player in self.players:
            status = "alive" if player.money > 0 else f"out at round {player.eliminated_round or self.round_number}"
            label = f"{player.name}: ${player.money} | {status}"
            color = GOOD if player.money > 0 else BAD
            self.draw_text(label, "small", color, (inner.x, y))
            y += 22

        if self.show_leaderboard:
            leaderboard = load_leaderboard()
            if leaderboard:
                box = pygame.Rect(inner.x, inner.bottom - 185, inner.width, 170)
                pygame.draw.rect(self.screen, PANEL_ALT, box, border_radius=12)
                self.draw_text("Leaderboard", "body", ACCENT, (box.x + 12, box.y + 10))
                top = sorted(leaderboard, key=lambda r: (r.get("survived_rounds", 0), r.get("final_money", 0)), reverse=True)[:6]
                ly = box.y + 44
                for record in top:
                    self.draw_text(
                        f"{record.get('name', '?')} - {record.get('survived_rounds', 0)} rounds - ${record.get('final_money', 0)}",
                        "tiny",
                        TEXT,
                        (box.x + 12, ly),
                    )
                    ly += 20
        else:
            self.draw_text("Press L to show the leaderboard.", "tiny", MUTED, (inner.x, inner.bottom - 170))

        # settings overlay
        if self.show_settings:
            sbox = pygame.Rect(BOARD.x + 60, BOARD.y + 40, BOARD.width - 120, BOARD.height - 80)
            pygame.draw.rect(self.screen, PANEL_BG, sbox, border_radius=12)
            self.draw_text("Settings", "body", ACCENT, (sbox.x + 12, sbox.y + 8))
            self.screen.set_clip(sbox)
            y = sbox.y + 44 - self.settings_scroll
            self.settings_buttons = {}
            patterns = ["square", "diamond", "cross", "line"]
            # Build a deterministic list of hazard names from weights and hazard_attrs
            combined_keys: list[str] = []
            for key in list(self.settings.get("weights", {}).keys()) + list(self.settings.get("hazard_attrs", {}).keys()) + [h.name for h in getattr(self, "hazards", [])]:
                if key not in combined_keys:
                    combined_keys.append(key)
            for name in combined_keys:
                weight = self.settings.get("weights", {}).get(name, 1.0)
                y = self._draw_settings_hazard_row(sbox, name, weight, y, patterns)
            self.screen.set_clip(None)
            self.settings_content_height = max(0, (y - (sbox.y + 44) + self.settings_scroll))

        # description editor modal
        if self.editing_desc is not None:
            name, cur = self.editing_desc
            modal = pygame.Rect(WIDTH // 2 - 260, HEIGHT // 2 - 120, 520, 240)
            pygame.draw.rect(self.screen, PANEL_BG, modal, border_radius=8)
            pygame.draw.rect(self.screen, PANEL_ALT, modal, 2, border_radius=8)
            self.draw_text(f"Editing description for {name}", "body", ACCENT, (modal.x + 12, modal.y + 8))
            self.draw_wrapped(cur or "(empty)", pygame.Rect(modal.x + 12, modal.y + 48, modal.width - 24, modal.height - 96), "small", TEXT)
            self.draw_text("Enter to save, Esc to cancel", "tiny", MUTED, (modal.x + 12, modal.y + modal.height - 28))
            

    def draw_top(self) -> None:
        pygame.draw.rect(self.screen, PANEL_ALT, pygame.Rect(0, 0, WIDTH, 100))
        titles = {
            "lobby": "Lobby",
            "place": "Place houses",
            "hazard": "Hazard reveal",
            "move": "Move phase",
            "game_over": "Game over",
        }
        self.draw_text(f"Volcano Risk Manager - {titles[self.state]}", "title", TEXT, (40, 22))
        if self.state in {"hazard", "move"} and self.last_round_summary:
            self.draw_text(self.last_round_summary, "small", ACCENT, (40, 64))

    def draw_lobby_help(self) -> None:
        box = pygame.Rect(40, 714, 760, 84)
        pygame.draw.rect(self.screen, PANEL_BG, box, border_radius=14)
        self.draw_text("How to play", "small", ACCENT, (box.x + 12, box.y + 10))
        self.draw_wrapped(
            "Add 2-8 players, place houses on the island, then survive random volcanic hazards while paying to move away from danger or repair your house. \n",
            pygame.Rect(box.x + 12, box.y + 34, box.width - 24, 40),
            "tiny",
            MUTED,
        )

    def add_player(self, name: str) -> None:
        clean = " ".join(name.strip().split())
        if not clean:
            return
        if len(self.players) >= 8:
            self.set_message("This simple version supports up to 8 players.")
            return
        if any(player.name.lower() == clean.lower() for player in self.players):
            self.set_message("That name already joined.")
            return
        palette = [
            (243, 177, 92),
            (112, 202, 255),
            (246, 120, 173),
            (143, 228, 155),
            (243, 138, 72),
            (183, 146, 255),
            (245, 210, 104),
            (123, 223, 205),
        ]
        self.players.append(Player(clean, color=palette[len(self.players) % len(palette)]))
        self.set_message(f"{clean} joined the lobby.")

    def place_house(self, cell: tuple[int, int]) -> None:
        player = self.players[self.current_player_index]
        if not self.island[cell[1]][cell[0]]:
            self.set_message("That square is water.")
            return
        if cell in self.occupied_cells():
            self.set_message("That square already has a house.")
            return
        player.house = cell
        self.current_player_index += 1
        if self.current_player_index >= len(self.players):
            self.round_number = 1
            self.start_hazard_phase()
        else:
            self.set_message(f"{self.players[self.current_player_index].name}, place your house.")

    def confirm_move(self) -> None:
        player = self.current_move_player()
        if player is None or player.house is None:
            return
        if self.selected_move_cell is None:
            self.set_message(f"{player.name} stays put.")
            self.next_move_player()
            return
        if self.selected_move_cell == player.house:
            self.next_move_player()
            return
        cost = manhattan(player.house, self.selected_move_cell) * MOVE_COST_PER_TILE
        if cost > player.money:
            self.set_message(f"{player.name} cannot afford that move.")
            return
        player.money -= cost
        player.house = self.selected_move_cell
        if player.money <= 0:
            player.money = 0
            player.alive = False
            player.eliminated_round = self.round_number
        self.set_message(f"{player.name} moved for ${cost}.")
        self.next_move_player()

    def next_move_player(self) -> None:
        self.selected_move_cell = None
        self.move_player_index += 1
        if self.move_player_index >= len(self.move_queue):
            self.finish_round()
        else:
            self.set_message(f"{self.move_queue[self.move_player_index].name}, choose your move.")

    def handle_click(self, pos: tuple[int, int]) -> None:
        cell = pick_land_cell(pos, self.island)
        # settings adjustments
        if self.show_settings:
            for name, rects in self.settings_buttons.items():
                # pattern options
                if "pattern_opts" in rects:
                    for orc in rects["pattern_opts"]:
                        if orc.collidepoint(pos):
                            # find which option
                            idx = rects["pattern_opts"].index(orc)
                            opts = ["square", "diamond", "cross", "line"]
                            choice = opts[idx]
                            attrs = self.settings.setdefault("hazard_attrs", {})
                            entry = attrs.setdefault(name, {})
                            entry["pattern"] = choice
                            self.save_settings()
                            self.pattern_dropdown = None
                            return
                # generic stepper buttons (dec_/inc_) handling
                for key, rect in list(rects.items()):
                    if not isinstance(key, str):
                        continue
                    if (key.startswith("dec_") or key.startswith("inc_")) and rect.collidepoint(pos):
                        action, attr_key = key.split("_", 1)
                        # numeric hazard attrs
                        attrs = self.settings.setdefault("hazard_attrs", {})
                        entry = attrs.setdefault(name, {})
                        # determine bounds and step for this attribute
                        bounds = self.settings.get("increments_bounds", {}).get(attr_key, {})
                        step = bounds.get("increment", 1)
                        mn = bounds.get("min", 0)
                        mx = bounds.get("max", None)

                        cur_val = entry.get(attr_key, 0) or 0
                        # handle integers specially
                        if isinstance(cur_val, int):
                            if action == "dec":
                                new = cur_val - int(step)
                            else:
                                new = cur_val + int(step)
                            if mn is not None:
                                new = max(int(mn), new)
                            if mx is not None:
                                new = min(int(mx), new)
                            entry[attr_key] = new
                        else:
                            # float-like
                            curf = float(cur_val)
                            if action == "dec":
                                newf = curf - float(step)
                            else:
                                newf = curf + float(step)
                            if mn is not None:
                                newf = max(float(mn), newf)
                            if mx is not None:
                                newf = min(float(mx), newf)
                            entry[attr_key] = round(newf, 2)
                        self.save_settings()
                        return

                # pattern button
                if "pattern" in rects and rects["pattern"].collidepoint(pos):
                    # toggle dropdown
                    if self.pattern_dropdown == name:
                        self.pattern_dropdown = None
                    else:
                        self.pattern_dropdown = name
                    return

                # edit description
                if "edit_desc" in rects and rects["edit_desc"].collidepoint(pos):
                    # start editing description
                    default_desc = ""
                    tmpl = getattr(self, "hazard_by_name", {}).get(name)
                    if tmpl is not None:
                        default_desc = tmpl.description
                    cur = self.settings.get("hazard_attrs", {}).get(name, {}).get("description", default_desc)
                    self.editing_desc = (name, cur)
                    return

        # mitigation button clicks (only during move)
        if getattr(self, "_mitigation_rects", None) and self.state == "move":
            cur = self.current_move_player()
            if cur:
                if self._mitigation_rects["levee"].collidepoint(pos):
                    cost = 120
                    if cur.money >= cost:
                        cur.money -= cost
                        cur.levee_active = True
                        self.set_message(f"{cur.name} bought a levee.")
                    else:
                        self.set_message(f"{cur.name} can't afford a levee.")
                    return
                if self._mitigation_rects["insurance"].collidepoint(pos):
                    cost = 80
                    if cur.money >= cost:
                        cur.money -= cost
                        cur.insured = True
                        self.set_message(f"{cur.name} bought insurance.")
                    else:
                        self.set_message(f"{cur.name} can't afford insurance.")
                    return
        if self.state == "lobby":
            return
        if self.state == "place":
            if cell is not None:
                self.place_house(cell)
            return
        if self.state == "hazard":
            if cell is not None:
                self.hazard_origin = cell
                self.apply_hazard()
                if len(self.alive_players()) <= 1:
                    self.end_game()
                else:
                    self.set_message("Survivors may move their houses.")
            return
        if self.state == "move" and cell is not None:
            player = self.current_move_player()
            if player is None:
                return
            if cell in self.occupied_cells() and cell != player.house:
                self.set_message("That square cannot be used.")
                return
            self.selected_move_cell = cell
            if player and player.house is not None:
                cost = manhattan(player.house, cell) * MOVE_COST_PER_TILE
                self.set_message(f"Selected move cost: ${cost}. Press Enter to confirm.")

    def handle_keydown(self, event: pygame.event.Event) -> None:
        # if editing description, capture keys here
        if self.editing_desc is not None:
            name, cur = self.editing_desc
            if event.key == pygame.K_RETURN:
                # save
                attrs = self.settings.setdefault("hazard_attrs", {})
                entry = attrs.setdefault(name, {})
                entry["description"] = cur
                self.save_settings()
                self.editing_desc = None
                return
            elif event.key == pygame.K_ESCAPE:
                self.editing_desc = None
                return
            elif event.key == pygame.K_BACKSPACE:
                cur = cur[:-1]
                self.editing_desc = (name, cur)
                return
            elif event.unicode and event.unicode.isprintable():
                cur = cur + event.unicode
                self.editing_desc = (name, cur)
                return

        # toggle settings with O
        if event.key == pygame.K_o:
            self.show_settings = not self.show_settings
            return
        if event.key == pygame.K_l and self.state != "lobby":
            self.show_leaderboard = not self.show_leaderboard
            return
        if self.state == "lobby":
            if event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_RETURN:
                if self.input_text.strip():
                    self.add_player(self.input_text)
                    self.input_text = ""
                elif len(self.players) >= 2:
                    self.start_placement()
                else:
                    self.set_message("Add at least two players first.")
            elif event.key == pygame.K_ESCAPE:
                self.input_text = ""
            elif event.unicode and event.unicode.isprintable() and len(self.input_text) < 18:
                self.input_text += event.unicode
        elif self.state == "move":
            if event.key == pygame.K_RETURN:
                self.confirm_move()
            elif event.key in {pygame.K_s, pygame.K_SPACE}:
                self.next_move_player()
            elif event.key == pygame.K_ESCAPE:
                self.selected_move_cell = None
        elif self.state == "game_over":
            if event.key == pygame.K_r:
                self.reset_game()

    def update(self) -> None:
        if self.state == "hazard" and time.time() >= self.hazard_expires_at:
            self.apply_hazard()
            if len(self.alive_players()) <= 1:
                self.end_game()

    def draw(self) -> None:
        self.screen.fill(BG)
        self.draw_board()
        self.draw_top()
        self.draw_panel()
        if self.state == "lobby":
            self.draw_lobby_help()
        pygame.display.flip()

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)
                elif event.type == pygame.MOUSEWHEEL:
                    if self.show_settings:
                        # scroll content: positive y means up
                        self.settings_scroll = max(0, self.settings_scroll - int(event.y * 30))
                        # clamp to content height
                        self.settings_scroll = min(self.settings_scroll, max(0, self.settings_content_height - (BOARD.height - 80)))

            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()


def main() -> None:
    Game().run()


if __name__ == "__main__":
    main()