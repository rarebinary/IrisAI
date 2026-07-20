# Playstyle System (.iris Scripts)

## Overview

Playstyles are Python scripts (`.iris` files) that determine in-game behavior. They are executed via Python's `exec()` with a sandboxed context. The active playstyle is set in `bot_config.toml` → `current_playstyle`.

## Script Format

### Header (line 1 - JSON metadata)
```python
# {"name": "Smart Universal", "description": "...", "brawlers": ["all"], "gamemodes": ["all"], "author": "Slarckvul"}
```

### Body (Python code)
The script must compute a `movement` variable — a tuple `(x, y)` where `-1.0 ≤ x,y ≤ 1.0` representing joystick direction.

## Available Context Variables

Available in the `exec()` context (from `play.py` → `Play.loop()`):

| Variable | Type | Description |
|----------|------|-------------|
| `player` | `(x, y, w, h)` or None | Player bounding box |
| `enemies` | `[(x1,y1,w1,h1), ...]` | Enemy bounding boxes |
| `teammates` | `[(x1,y1,w1,h1), ...]` | Teammate bounding boxes |
| `walls` | `[(x1,y1), ...]` | Wall tile center points |
| `bushes` | `[(x1,y1), ...]` | Bush tile center points |
| `loop_count` | int | Current frame iteration count |
| `game_state` | dict | Current game state (mode, map info) |
| `joystick` | `(x, y)` | Current joystick position |
| `super_ready` | bool | Super ability charged |
| `gadget_ready` | bool | Gadget available |
| `hypercharge_ready` | bool | Hypercharge available |
| `brawler_range` | float | Brawler attack range (game units) |
| `brawler_safe_range` | float | Brawler safe retreat range |
| `brawler_super_range` | float | Brawler super range |
| `poison_gas` | dict | Directional poison gas: `{"up": count, "down": count, "left": count, "right": count}` |
| `movement` | `(x, y)` or None | Current movement vector from previous iteration |
| `player_hit_circle` | `(cx, cy, radius)` | Player hit circle for collision |
| `can_attack_through_walls` | bool | Whether brawler attacks ignore walls |

## Available Functions

Functions callable from playstyle scripts:

| Function | Description |
|----------|-------------|
| `find_closest_enemy()` | Returns `(x, y, distance)` of closest enemy |
| `find_closest_teammate()` | Returns `(x, y, distance)` of closest teammate |
| `get_entity_pos(box)` | Returns `(cx, cy)` center of bounding box |
| `get_distance(p1, p2)` | Euclidean distance between 2 points |
| `is_there_enemy()` | True if enemies exist |
| `is_enemy_hittable()` | True if closest enemy is in range + LOS |
| `is_path_blocked(x1,y1,x2,y2)` | True if walls block line between points |
| `is_there_poison_gas()` | True if player is in gas |
| `get_actual_player_box()` | Returns player bounding box (adjusted) |
| `get_brawler_range()` | Returns brawler attack range |
| `get_random_movement()` | Returns random `(x, y)` direction |
| `use_super()` | Activate super ability |
| `use_gadget()` | Activate gadget |
| `use_hypercharge()` | Activate hypercharge |
| `attack(touch_up=True, touch_down=True)` | Trigger attack |
| `must_brawler_hold_attack()` | True if brawler requires held attack |
| `rotate_movement(dx, dy, angle)` | Rotate vector by angle degrees |
| `get_player_hit_circle()` | Returns (cx, cy, radius) for player hit circle |
| `clamp(x, low, high)` | Clamp value to range |
| `get_entity_pos(box)` | Returns entity center coordinates |
| `get_distance(p1, p2)` | Euclidean distance between 2 points |

## Safe Globals

Scripts run with `SAFE_GLOBALS` — a restricted set of builtins and modules:
- `True`, `False`, `None`
- `abs`, `all`, `any`, `bool`, `callable`, `dict`, `enumerate`, `float`, `hash`, `int`
- `isinstance`, `len`, `list`, `map`, `max`, `min`, `pow`, `range`, `round`
- `set`, `slice`, `sorted`, `str`, `sum`, `tuple`, `type`, `zip`
- `math` — safe math functions (sin, cos, sqrt, atan2, pi, etc.)
- `random` — `random.random`, `random.randint`, `random.choice`, `random.uniform`
- `time` — `time.time`, `time.sleep`

No imports allowed. No file/network access. No access to `__builtins__`, `exec`, `eval`, `open`, `import`, `os`, `sys`, `subprocess`.

## Available Playstyles

| File | Description |
|------|-------------|
| `default_up.iris` | Moves UP when no enemies, basic combat |
| `default_right.iris` | Moves RIGHT when no enemies, basic combat |
| `follower.iris` | Follows teammates when no enemies |
| `showdown_survivor.iris` | Follows teammates, avoids poison gas, moves to center |
| `team_showdown.iris` | Follows teammates + poison gas avoidance |
| `universal_smart_v5_Slarckvul_Eddition.iris` | Advanced: archetype-based combat (ASSASSIN/TANK/SNIPER/LOBS/RANGED), wall-aware, ability usage, gas avoidance |
| `universal_smart_v5_Slarckvul_RUSH.iris` | Variant with multi-enemy spacing |
| `skeleton.py` | Reference template with all available context variables and function signatures (not a valid .iris file — use as documentation) |

## Creating a Custom Playstyle

1. Copy `skeleton.py` as a reference
2. Create a new `.iris` file in `playstyles/`
3. Add JSON metadata as first line comment
4. Write Python code that computes `movement = (x, y)`
5. Set `current_playstyle` in `bot_config.toml` to your filename (without extension)
6. Restart the bot — the new playstyle will be loaded on next match

## Playstyle Selection

The active playstyle can be changed via:
- `bot_config.toml` → `current_playstyle`
- Web UI → Playstyles section
- At runtime when switching between pages of the playstyles list
