# VolcanoHazard

VolcanoRisk Manager — a small local multiplayer game written with pygame.

Players place houses on a procedurally generated island and try to survive rounds of volcanic hazards while managing money and mitigation purchases.

Run

```bash
conda activate VolcanoHazard
python main.py
```

Basic rules

- Add players in the lobby by typing names and pressing Enter (2–8 players).
- Each player places one house on a land tile.
- Each round a hazard is revealed (see Hazards below). If a house lies in the hazard pattern it takes damage (money lost).
- After damage, surviving players take turns to optionally move their house; moving costs `Manhattan distance × MOVE_COST_PER_TILE`.
- The last player with money remaining wins; results are appended to `leaderboard.json`.

Controls

- Mouse: click board squares to place/reveal/move as prompted.
- Enter: confirm actions (join, place, or confirm move).
- S (or Space): skip a move during the Move phase.
- O: open/close the Settings panel.
- Mouse wheel: scroll the Settings panel when it's open.
- R: restart after game over.
- L: toggle the leaderboard in the panel.

Mitigations (buy during Move phase)

- Buy levee — $120: halves the damage from the next hazard that would hit your house (one-time), shown as a blue dot on your house.
- Buy insurance — $80: after your house is hit, refunds half of the damage taken (one-time), shown as a yellow dot on your house.

Settings and expansion

- Press `O` to open the Settings overlay. It is scrollable and shows every hazard with controls to adjust:
	- selection weight (affects how likely a hazard is chosen),
	- damage (adjust in steps),
	- spread (pattern size),
	- pattern (choose from `square`, `diamond`, `cross`, `line`), and
	- description (editable text).
- Settings persist to `settings.json` and are applied at runtime — you can tune the behaviour of hazards and the overall intensity multiplier.

- Optional volcano expansion: if `volcano_expansion.py` is present the game will place a main volcano on the island during the first round and subsequent hazards will be sampled with probabilities that depend on distance from that volcano (e.g., pyroclastic surges and lava more likely close to the volcano; ashfall more likely farther away). The Settings panel still modifies the final sampling probabilities (weights multiply the expansion's distance-based weights).

Hazards (defaults)

- Ashfall — light ashfall affecting a small diamond; default damage ~ $60.
- Lava Spur — concentrated lava burst (square); default damage ~ $100.
- Bomb Shower — cross-shaped shower of bombs; default damage ~ $140.
- Pyroclastic Surge — hot surge spreading in a wider diamond; default damage ~ $180.
- Mudflow — fast-moving line of debris; default damage ~ $120.
- Radius Blast — heavy blast affecting a tight area; default damage ~ $220.

Notes

- The expansion module is optional and lives in `volcano_expansion.py`. If present it will be used automatically.
- The game stores player leaderboard entries in `leaderboard.json` and settings in `settings.json` in the game folder.
- The codebase is intentionally compact and designed for local play with simple, tweakable rules. If you want any UI refinements (sliders, tooltips, or small graphics), tell me which and I'll add them.

Enjoy — and watch out for the volcano!
