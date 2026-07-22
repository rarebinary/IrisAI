# Configuration System

All configuration is in `cfg/`. The system uses TOML for structured config and JSON for data.

> **Note:** Config file and code defaults are now aligned (Bug 13, 14 fixed).

## File Reference

### general_config.toml

| Key | File Value | Code Default | Description |
|-----|-----------|-------------|-------------|
| `cpu_or_gpu` | `"auto"` | `"auto"` | macOS inference mode: `auto`, `coreml`, or `cpu` |
| `max_ips` | `60` | `"auto"` | Iterations per second (main loop speed) |
| `trophies_multiplier` | `1` | `1.0` | Multiply trophy gains/losses |
| `run_for_minutes` | `0` | `60` | Auto-stop after N minutes (0 = no limit) |
| `emulator_port` | `5555` | `5555` | Android emulator ADB port |
| `api_base_url` | `"default"` | `"localhost"` | API endpoint for match results |
| `brawl_stars_package` | `"com.supercell.brawlstars"` | `"com.supercell.brawlstars"` | BS package name (auto-discovered; known variants are persisted back to TOML) |
| `ocr_scale_down_factor` | `0.6` | `0.75` | EasyOCR image scale (clamped 0.5-1.0) |
| `used_threads` | `4` | `"auto"` | Thread pool size for model inference |
| `player_tag` | `"#"` | `""` | Brawl Stars player tag |
| `play_order` | `"lowest_to_highest"` | `"in_order"` | Queue sort order |
| `alarm_enabled` | `true` | `True` | Play alarm sound on events |
| `default_trophy_target` | `500` | `750` | ❌ Not used in code |
| `auto_load_queue_on_startup` | `true` | `False` | Restore queue from file on boot |

Any other `cpu_or_gpu` value is rejected during health checks and model startup. This prevents old profiles from silently selecting the wrong provider.

### bot_config.toml

| Key | File Value | Code Default | Description |
|-----|-----------|-------------|-------------|
| `play_again_on_win` | `"yes"` | `True` | Click "play again" after victory |
| `minimum_movement_delay` | `0.35` | `0.05` | Seconds between movement updates |
| `unstuck_movement_delay` | `6.0` | `20` | Seconds before stuck rotation triggers |
| `unstuck_movement_hold_time` | `3.0` | `3` | Seconds to hold rotated direction |
| `perceived_tile_size` | `75` | `80` | Wall tile size in pixels |
| `centered_wall_detection` | `false` | `False` | Use centered wall crop |
| `wall_model_classes` | `["wall","bush","close_bush"]` | same | Wall model output classes |
| `wall_detection_confidence` | `0.7` | `0.5` | YOLO wall confidence threshold |
| `entity_detection_confidence` | `0.5` | `0.5` | YOLO entity confidence threshold |
| `seconds_to_hold_attack_after_reaching_max` | `1.5` | `0.3` | Extra hold attack time |
| `current_playstyle` | `"aggressive_universal.iris"` | `"team_follow.iris"` | Active .iris script |
| `max_losses` | `1` | `0` | Max losses before switching brawler |
| `max_consecutive_losses` | `0` | `0` | Max consecutive losses before switch |
| `super_pixels_minimum` | `1800.0` | `100` | Min HSV pixels for super ready |
| `gadget_pixels_minimum` | `1300.0` | `100` | Min HSV pixels for gadget ready |
| `hypercharge_pixels_minimum` | `1800.0` | `100` | Min HSV pixels for hypercharge ready |
| `idle_pixels_minimum` | `75000.0` | `500` | Min gray pixels for idle detection |

### time_tresholds.toml

> **Note:** Key names in TOML match config_loader.py expectations (Bug 12 verified — already aligned).

| Key | File Value | Code Default | Description |
|-----|-----------|-------------|-------------|
| `state_check` | `3.0` | `2` | Check game state every N sec |
| `no_detections` | `30` | `30` | No entities detected for N sec → action |
| `idle` | `3.0` | `5` | Check idle screen every N sec |
| `gadget` | `0.15` | `5` | Check gadget readiness every N frames |
| `hypercharge` | `0.15` | `5` | Check hypercharge readiness every N frames |
| `super` | `0.15` | `5` | Check super readiness every N frames |
| `wall_detection` | `0.15` | `2` | Run wall detection every N frames |
| `no_detection_proceed` | `8.0` | `60` | Press proceed after N frames without detections |
| `check_if_brawl_stars_crashed` | `10` | `20` | Check BS crash every N seconds |

### buttons_config.toml

Screen coordinates for interactive buttons (at 1920×1080 reference):

| Key | Coords | Used By | Status |
|-----|--------|---------|--------|
| `hypercharge` | `[1400, 900]` | `play.py` | ✅ |
| `gadget` | `[1640, 990]` | `play.py` | ✅ |
| `attack` | `[1725, 800]` | `play.py` | ✅ |
| `proceed` | `[1660, 980]` | `play.py`, `stage_manager.py` | ✅ |
| `super` | `[1510, 880]` | `play.py` | ✅ |
| `play_again` | `[1360, 920]` | `stage_manager.py` | ✅ |
| `continue_or_equip` | `[700, 1000]` | `stage_manager.py` | ✅ |
| `idle_reconnect` | `[540, 630]` | Reload idle/cannot-rejoin alerts | ✅ |
| `brawlers_menu` | `[110, 490]` | `lobby_automation.py` | ✅ |
| `select_brawler` | `[150, 950]` | `lobby_automation.py` | ✅ |
| ~~`middle_got_it`~~ | — | Removed (Bug 18) | ✅ Dead code purged |
| ~~`buffie_machine`~~ | — | Removed (Bug 18) | ✅ Dead code purged |
| ~~`middle`~~ | — | Removed (Bug 18) | ✅ Dead code purged |
| ~~`middle_noodle`~~ | — | Removed (Bug 18) | ✅ Dead code purged |

### webhook_config.toml

| Key | Description |
|-----|-------------|
| `webhook_url` | Discord webhook URL (⚠️ bare key access, crash if missing) |
| `discord_id` | Authorized Discord user ID |
| `discord_bot_token` | Discord bot token for slash commands |
| `discord_guild_id` | Discord guild ID for command tree sync |
| `telegram_token` | Telegram bot token |
| `telegram_chat_id` | Telegram chat ID |
| `ping_when_stuck` | Notify on stuck |
| `ping_when_target_is_reached` | Notify on target reached |
| `ping_every_x_match` | Ping every N matches (0 = disabled) |
| `ping_every_x_minutes` | Ping every N minutes (0 = disabled) |

### debug_settings.toml

| Key | File Value | Description |
|-----|-----------|-------------|
| `verbose_debug` | `false` | Verbose debug logging |
| `state_finder_debug` | `false` | Write state-finder debug frames every 5s |
| `re_apply_movement` | `false` | Always re-send movement even if unchanged |
| `debug_view` | `false` | Enable debug overlay subprocess |
| `debug_view_fps` | `10` | Debug overlay FPS |
| `advanced_debug_visuals` | `false` | Advanced overlay visuals (early access) |
| `record_debug_preview_clips` | `false` | Record MP4 clips on detection events |
| `debug_capture_max_files` | `100` | Maximum number of diagnostic images and clips retained |
| `debug_capture_max_mb` | `500` | Maximum combined diagnostic capture storage in MB |

### login.toml

```toml
key = ""  # API key for cloud features. ENV: IRIS_API_KEY (Bug 15 verified — mapping exists in config_loader.py:21)
```

### brawlers_info.json

Per-brawler data fetched from Brawlify API. Includes `attack_range`, `safe_range`, `super_range`, `ignore_walls_for_attacks`, `ignore_walls_for_supers`, `hold_attack`, `super_type`, `rarity`, `class`.

### names.json

Brawler name aliases for OCR matching (lowercase -> list of variants).

## Loading Mechanism

- `utils.py` → `load_toml_as_dict(filename)` reads and caches TOML files in a `ThreadSafeDict`
- Cache is invalidated by `invalidate_toml_cache()` and `save_dict_as_toml()`
- ~~**Bug:** `lstrip('/\\')` corrupts absolute paths in `load_toml_as_dict`, `invalidate_toml_cache`, and `save_dict_as_toml`~~ ✅ Already fixed (Bug 3 verified)
- **Bug:** TOML cache is never invalidated by external file changes
- `config_loader.py` provides `get_config(path, key, default, expected_type)` with env var override
- Queue data is normalized by `clean_queue()`, which now skips malformed imported entries and supplies safe numeric defaults for missing `wins`, `trophies`, `push_until`, and `win_streak`.
- `brawl_stars_package` is now present in both TOML and code defaults. `bs_package_name` remains only as a legacy/default alias and should not be used by new code.

## Robustness Notes

- Template matching now returns `False` for empty crops or templates larger than the target region instead of allowing OpenCV to raise an assertion error.
- The TOML cache is updated by `save_dict_as_toml()` and can be invalidated with `invalidate_toml_cache()`. External file changes are still not auto-detected, so long-running processes should call the invalidation helper after out-of-band writes.
- Secrets can be supplied through `IRIS_*` environment variables listed in `config_loader.ENV_MAPPING`; Web UI payloads mask sensitive webhook settings before returning them.
- Runtime data uses `.iris_runtime/` by default. Set `IRIS_RUNTIME_DIR` to move queue state, match history, logs, and debug frames outside the repository for packaged or multi-user installs.
- `health.py` validates readable TOML files and reports missing non-legacy keys that are falling back to code defaults.

## Settings Sections (Web UI)

1. **General** — 12 fields (cpu/gpu, max_ips, trophies_multiplier, run_for_minutes, player_tag, default_trophy_target, play_order, ocr_scale_down_factor, brawl_stars_package, emulator_port, auto_load_queue, alarm_enabled)
2. **Bot** — 14 fields (play_again_on_win, movement/stuck delays, tile_size, detection confidences, pixel thresholds, loss limits)
3. **Timer Frequencies** — 8 fields (super, hypercharge, gadget, wall_detection, no_detection_proceed, state_check, idle, crash_check)
4. **Webhook** — 10 fields (Discord/Telegram webhooks, tokens, ping settings)
5. **Debug** — 7 fields (view toggles, FPS, verbose/state_finder debug, re_apply_movement)

> ~~**Known bug:** `services.py` defaults do not match `config_loader.py` defaults for `perceived_tile_size`, `super_pixels_minimum`, `entity_detection_confidence`.~~ ✅ Fixed (Bug 14). All three now aligned with config_loader.py.
