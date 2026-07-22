# Playstyle System (`.iris` Scripts)

## Overview

Playstyles are restricted Python scripts stored in `playstyles/`. `Play.loop()`
builds a context from the latest detections, and `interpret_iris_code()` executes
the selected script. The active filename is stored as `current_playstyle` in
`cfg/bot_config.toml`.

Every bundled `.iris` file is executed by the regression suite with empty and
populated entity detections. This catches missing context values and incorrect
helper arguments before release.

## File Format

The first line is JSON metadata without a comment prefix:

```json
{"name":"Lane Up","description":"Moves up when clear.","brawlers":["all"],"gamemodes":["all"],"author":"Official"}
```

The remaining lines are Python code. They must assign `movement` to an `(x, y)`
tuple. Values are pixel offsets and are clamped by Iris to the configured
joystick radius, normally `-75` to `75` on each axis. Scripts may also call the
attack and ability helpers.

## Context Variables

| Variable | Type | Description |
|---|---|---|
| `player_data` | `[x1, y1, x2, y2]` | Current player bounding box |
| `enemy_data` | list of boxes | Detected enemies |
| `teammate_data` | list of boxes | Detected teammates |
| `teammates_data` | list of boxes | Compatibility alias for `teammate_data` |
| `brawler` | string | Selected brawler name |
| `walls`, `bushes` | list of boxes | Detected map geometry |
| `brawlers_info` | dict | Brawler attack metadata |
| `is_super_ready`, `is_gadget_ready`, `is_hypercharge_ready` | bool | Ability readiness |
| `TILE_SIZE` | number | Scaled perceived tile size |
| `JOYSTICK_RADIUS` | number | Maximum base joystick displacement |
| `width`, `height` | number | Reference game resolution (`1920x1080`) |
| `center` | tuple | Reference screen center (`960, 540`) |
| `persistent_data` | dict | Mutable values kept between frames |
| `current_brawler` | string or `None` | Previously active brawler |
| `last_movement` | tuple or string | Last accepted movement |
| `last_movement_change_time` | number | Last movement-change timestamp |
| `seconds_to_hold_attack_after_reaching_max` | number | Extra held-attack duration |
| `time`, `random` | modules | Restricted standard helpers |
| `debug` | bool | Verbose playstyle diagnostics enabled |

## Context Functions

| Function | Purpose |
|---|---|
| `get_entity_pos(box)` | Return the center of a detection box |
| `get_distance(point_a, point_b)` | Return Euclidean distance |
| `get_actual_player_box(player_data)` | Return the adjusted player hit box |
| `get_brawler_range(brawler)` | Return `[safe, attack, super]` ranges |
| `is_there_enemy(data)`, `is_there_teammate(data)` | Check whether detections exist |
| `count_enemies_in_area(data, pos, radius)` | Count nearby enemies |
| `count_teammates_in_area(data, pos, radius)` | Count nearby teammates |
| `find_closest_enemy(data, pos, walls, skill_type)` | Return `(position, distance)` or `(None, None)` |
| `find_closest_teammate(data, pos, walls)` | Return `(position, distance)` or `(None, inf)` |
| `is_enemy_hittable(player_pos, enemy_pos, walls, skill_type)` | Check line of sight |
| `is_path_blocked(player_box, movement, walls, distance=None)` | Check wall collision for a movement vector |
| `is_there_poison_gas(player_data, threshold=7000, area_from_player_checked=1.5)` | Return directional gas pixel counts |
| `get_random_movement()` | Return a random joystick vector |
| `rotate_movement(movement, angle_radians)` | Rotate a movement vector |
| `must_brawler_hold_attack(brawler, brawlers_info)` | Check held-attack behavior |
| `attack(...)`, `use_super()`, `use_gadget()`, `use_hypercharge()` | Send combat controls |

Power cubes and player HP are not currently detected by the entity model. A
playstyle must not infer them from `player_data`.

## Bundled Playstyles

| File | Behavior |
|---|---|
| `aggressive_universal.iris` | General chase, retreat, attack, and ability use |
| `aggressive_rush.iris` | Constant forward pressure for close-range brawlers |
| `aggressive_balanced.iris` | Push with support and retreat when outnumbered |
| `knockout.iris` | Conservative ranged positioning |
| `lane_up.iris` | Prefer the upper lane when no enemy is visible |
| `lane_right.iris` | Prefer the right lane when no enemy is visible |
| `showdown_survival.iris` | Avoid close enemies and return toward map center |
| `showdown_team.iris` | Stay near a teammate and retreat when outnumbered |
| `team_follow.iris` | Follow the closest teammate and attack nearby enemies |
| `skeleton.py` | Reference context for authors; not executable as a playstyle |

## Safety Boundary

`utils.is_safe_ast()` rejects imports, private or dunder attributes, and direct
use of dangerous dynamic functions such as `exec`, `eval`, and `__import__`.
Execution receives an empty builtins mapping plus a small allowlist of numeric,
collection, `math`, `random`, and timing helpers. A failed script returns no
movement and the controller releases the joystick.

This is a local safety boundary for trusted playstyles, not a hardened security
sandbox for untrusted code.

## Creating a Playstyle

1. Use `playstyles/skeleton.py` as the context reference.
2. Create a `.iris` file and add valid JSON metadata on its first line.
3. Assign an `(x, y)` tuple to `movement` on every execution path.
4. Import and activate it from the Web UI, or set `current_playstyle` manually.
5. Run `python3 -m unittest -v tests.test_core_safety` before sharing it.

Current combat limitations include no ammo tracking, aim prediction, health
reading, objective strategy, or dedicated power-cube detector.
