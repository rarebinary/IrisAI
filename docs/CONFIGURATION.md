# Configuration System

All configuration is in `cfg/`. The system uses TOML for structured config and JSON for data.

## File Reference

### general_config.toml
```toml
[general]
cpu_or_gpu = "cpu"                    # cpu | cuda | coreml | directml | auto
max_ips = 30                           # iterations per second (main loop speed)
trophies_multiplier = 1.0             # multiply trophy gains/losses
run_for_minutes = 60                   # auto-stop after N minutes (0 = no limit)
emulator_port = 5555                   # Android emulator ADB port
api_base_url = "http://localhost:1337" # API endpoint for match results
bs_package_name = "com.supercell.braw" # Brawl Stars package (auto-discovered)
ocr_scale_down_factor = 0.75           # EasyOCR image scale (lower=faster, clamped 0.5-1.0)
process_every_n_frames = 2             # process every Nth frame
used_threads = 4                       # thread pool size for model inference (auto or int)
player_tag = "#..."                    # Brawl Stars player tag
play_order = "lowest_to_highest"       # lowest_to_highest | highest_to_lowest | in_order
alarm_enabled = true                   # play sound on certain events
default_trophy_target = 750            # default trophy target when adding to queue
auto_load_queue_on_startup = false     # restore queue from saved file on boot
```

### bot_config.toml
```toml
[bot]
play_again_on_win = true               # click "play again" after victory
minimum_movement_delay = 0.05          # seconds between movement updates
unstuck_movement_delay = 20            # seconds before stuck rotation triggers
unstuck_movement_hold_time = 3         # seconds to hold rotated direction
perceived_tile_size = 80               # wall tile size in pixels
centered_wall_detection = false        # use centered wall crop instead of full
entity_detection_confidence = 0.5      # YOLO entity confidence threshold
wall_detection_confidence = 0.5        # YOLO wall confidence threshold
re_apply_movement = false              # always re-send movement even if unchanged
current_playstyle = "default_up"       # active .iris script (no extension)
max_losses = 5                         # max losses before switching brawler
max_consecutive_losses = 3             # max consecutive losses before switch
seconds_to_hold_attack_after_reaching_max = 0.3  # hold attack after max range
super_pixels_minimum = 100             # min pixels to detect super ready
gadget_pixels_minimum = 100            # min pixels to detect gadget ready
hypercharge_pixels_minimum = 100       # min pixels to detect hypercharge ready
idle_pixels_minimum = 100              # min gray pixels to detect idle
```

### lobby_config.toml
Controls template matching regions and pixel counter crop areas:
```toml
[template_matching]
lobby = {x=0, y=0, w=1920, h=1080}
match_making = {x=0, y=0, w=1920, h=1080}
# ... per-state detection regions (all use normalized region coords)

[pixel_counter_crop_area]
super = {x=0, y=900, w=200, h=100}      # crop area for super detection
gadget = {x=50, y=950, w=150, h=80}     # crop area for gadget detection
hypercharge = {x=100, y=850, w=100, h=100} # crop for hypercharge
```

### buttons_config.toml
Screen coordinates for interactive buttons:
```toml
attack = {x=1750, y=950}
super = {x=1650, y=900}
gadget = {x=1500, y=950}
proceed = {x=960, y=950}
# ... per-resolution button positions
```

### time_tresholds.toml
```toml
state_check_seconds = 2                # check game state every N sec
no_detections_timeout = 30             # no entities detected for N sec → action
idle_check_seconds = 5                 # check idle screen every N sec

[timer_frequencies]
wall_detection = 2                     # run wall detection every N frames
super = 5                              # check super readiness every N frames
hypercharge = 5                        # check hypercharge readiness every N frames
gadget = 5                             # check gadget readiness every N frames
no_detection_proceed = 60              # press "proceed" after N frames without detections
check_if_brawl_stars_crashed = 20      # check BS crash every N seconds
```

### webhook_config.toml
```toml
webhook_url = "https://discord.com/api/webhooks/..."
discord_id = 123456789                 # authorized Discord user ID
bot_token = "..."                      # Discord bot token
discord_guild_id = 123456789           # Discord guild ID (for command tree sync)
telegram_token = "..."                 # Telegram bot token
telegram_chat_id = "..."               # Telegram chat ID
ping_when_stuck = true                 # notify when bot gets stuck
ping_when_target_is_reached = true     # notify when brawler reaches target
ping_every_x_match = 0                 # ping every N matches (0 = disabled)
ping_every_x_minutes = 0               # ping every N minutes (0 = disabled)
min_trophies_to_ping = 500             # minimum trophies to send notifications
```

### debug_settings.toml
```toml
enabled = true                         # enable debug view
fps = 30                               # debug overlay FPS
show_boxes = true                      # show detection boxes
show_ranges = true                     # show attack/super ranges
show_joystick = true                   # show joystick input
show_los = false                       # show line-of-sight rays
clip_recording = false                 # enable MP4 clip recording
verbose_debug = false                  # verbose debug logging
state_finder_debug = false             # write state-finder debug frames every 5s
re_apply_movement = false              # always re-send movement to device
advanced_debug_visuals = false         # advanced overlay visuals (early access)
record_debug_preview_clips = false     # record MP4 clips on detection events
```

### login.toml
```toml
api_key = ""                           # API key for cloud features
# Empty in open-source mode; localhost API bypasses auth
```

### brawlers_info.json
Per-brawler data structure:
```json
{
  "shelly": {
    "attack_range": 7.67,
    "safe_range": 7.67,
    "super_range": 9.0,
    "ignore_walls": false,
    "hold_attack": false,
    "super_type": "projectile",
    "rarity": "Trophy Road",
    "class": "Damage Dealer"
  }
}
```

### names.json
Brawler name aliases for OCR matching:
```json
{
  "shelly": ["shelly", "shelly "],
  "mr p": ["mr p", "mr. p", "mrp"],
  "larry & lawrie": ["larry & lawrie", "larry+lawrie"]
}
```

## Loading Mechanism

`utils.py` → `load_toml_as_dict(filename)`:
- Loads from `cfg/<filename>.toml`
- Caches results (1st load reads disk, subsequent loads return cached)
- `invalidate_toml_cache()` clears cache for reload
- `save_dict_as_toml()` writes back to disk
- The Web UI uses `WebDataService.load_config()` / `save_config()` with schema-based serialization

## Settings Sections (Web UI)
1. **General**: cpu/gpu, max_ips, trophies multiplier, run timer, emulator port, play_order, ocr_scale_down_factor, default_trophy_target, alarm_enabled, auto_load_queue
2. **Bot**: play_again_on_win, movement delay, unstuck settings, tile_size, confidence thresholds, pixel thresholds, loss limits
3. **Lobby**: template match regions, pixel counter crop areas
4. **Buttons**: per-resolution button coordinates
5. **Webhook**: Discord/Telegram webhooks, Discord guild ID, notification settings
6. **Debug**: view toggles, FPS, clip recording, verbose_debug, state_finder_debug, re_apply_movement, advanced_visuals
7. **Timer Frequencies**: per-component cycle rates (super, hypercharge, gadget, wall_detection, crash check, etc.)
