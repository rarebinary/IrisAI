# Components

## main.py — Entry Point & Orchestrator

**Key Class:** `Main` (inner class of `iris_main()`)

### Initialization Flow
```
iris_main(discord_bot, queue_data, stop_event, runtime_control)
  ├── Monkey-patch inspect.getfile (Nuitka compat)
  ├── Apply queue play order (lowest_to_highest/highest_to_lowest/in_order)
  ├── Clean queue data (remove brawlers at target), raise ValueError if empty
  ├── Save brawler data
  ├── Load playstyle script via load_iris_script()
  ├── WindowController(scrcpy + ADB, optional max_ips)
  ├── Play(3 ONNX models, wall/tile detection)
  ├── TimeManagement(timer thresholds)
  ├── LobbyAutomation(EasyOCR)
  ├── StageManager(menu FSM, brawlers, lobby_automator, runtime_control)
  ├── TrophyObserver(trophy tracking) — synced from first queue brawler
  ├── RuntimeManager(start/pause/stop)
  ├── Start state checker thread (daemon, runs at frame rate)
  ├── (Flask is created in __main__, not inside iris_main)
  └── Main.main() loop
```

### Entry Point (`main()` at module level)
1. Print splash screen (ASCII art logo with cyan box)
2. Set up session logging via `terminal_ui.setup_session_logging()` — all stdout/stderr tee'd to `logs/session_<timestamp>.log`
3. Start Flask web UI on first available port (5185+)
4. Install `sys.excepthook` to show crash banner on unhandled exceptions

### Main.main() Loop
1. If state == "lobby": check stop/pause signals (honored only in lobby)
2. Auto-pick first brawler if not yet picked (on failure, rotate to end of queue and retry; max 3 "stuck" retries before continuing with current selection)
3. Enforce `run_for_minutes` timer (3min cooldown after target expires)
4. Print status line every second (~1 IPS): `IPS | Brawler | State | Trophies | Playstyle | Session Time` via `update_status()` (saves cursor at start of loop, restores + clears on each update to handle terminal resize)
5. Periodically check for BS crashes via `device.app_current()`
6. Get latest frame; if stale >15s → release movement, reconnect scrcpy; if >30s → restart BS
7. Call `manage_time_tasks(frame)`:
   - State check timeout → run `get_state` + dispatch via StageManager
   - No-detections timeout (>8min) → restart BS
   - Idle check → call `lobby_automator.check_for_idle(frame)`
   - Periodic webhook pings
8. Call `Play.main(frame, brawler, main, last_frame_time)` for in-game AI
9. Throttle to `max_ips` if configured
10. Warn if IPS < 15

### Key Utilities
- `apply_play_order()` — Sorts brawler queue by trophies (`"lowest_to_highest"` ascending, `"highest_to_lowest"` descending, or `"in_order"` for no sort). Sets `automatically_pick = True` on all items after sorting.
- `find_open_port(start_port=5185)` — Finds available port for Flask UI, starting at 5185, trying up to 50 ports on 127.0.0.1.
- `restart_brawl_stars()` — ADB stop/start app with stuck detection. Resets detection timers. Notifies user on failure.
- `play_alarm()` — Plays alarm sound via `afplay` subprocess on macOS.
- `should_stop()` / `should_pause()` — Check `stop_event` or `runtime_control` signals.
- `sleep_interruptible(duration, allow_pause)` — Sleeps with stop/pause polling, returns interruption reason.
- `stop_gracefully()` — Releases joystick, stops state checker, closes window controller.

---

## play.py — In-Game AI Engine

**Key Class:** `Play`

The core in-game behavior system. All entity detection, movement, and combat logic.

### Key Constants
- `PLAYER_HIT_CIRCLE_RADIUS = 53` (pixels, scaled by screen ratio)
- `JOYSTICK_RADIUS = 75` (pixels)
- `POISON_LOW_HSV = (30, 90, 221)`, `POISON_HIGH_HSV = (57, 114, 235)`

### Models Loaded
| Model | Purpose | Classes |
|-------|---------|---------|
| `mainInGameModel.onnx` | Entity detection | player, enemy, teammate |
| `tileDetector.onnx` | Full-frame wall/bush | wall tiles (3 or 5 classes) |
| `closeTileDetector.onnx` | Centered-crop wall/bush | wall tiles (fallback) |

### Main Loop (per frame)

```
Play.main(frame, brawler, main, frame_time=0.0)
  ├── Skip if state != "match"
  ├── Dedup if frame_time unchanged (reuse last cache via _last_data_cache)
  ├── Parallel inference (ThreadPoolExecutor with 2 workers):
  │   ├── get_main_data() — entity YOLO detection
  │   └── get_tile_data() — wall/bush detection (only if due, and not centered mode)
  ├── Process tile data → separate walls from bushes
  ├── Validate game data, track no-detection timers
  ├── If data invalid (no player): release movement, check no_detection_proceed delay,
  │   may press "proceed" or re-detect state
  ├── Check super/gadget/hypercharge readiness (HSV pixel counting in crops, at intervals)
  ├── Check poison gas (HSV masking around player, returns directional dict)
  └── Play.loop(brawler, data, current_time)
        ├── Build context dict (entities, walls, abilities, ranges, hit_circles, etc.)
        ├── Enforce minimum_movement_delay
        ├── interpret_iris_code() → movement (x,y)
        └── unstuck_movement_if_needed(movement) → rotated vector if stuck
```

### Detection Systems

**Entity Detection:** YOLO ONNX → bounding boxes for player/enemy/teammate. Uses Non-Maximum Suppression (`_numpy_nms`) to filter overlapping detections.

**Wall/Bush Detection:** Two ONNX models analyze the game field. Wall data is cached and processed in background threads on a timer (default every 2 frames).
- Full-frame: `tileDetector.onnx` processes entire screen
- Centered: `closeTileDetector.onnx` processes cropped region around player (configurable fallback)

**Ability Readiness:** Crops specific regions of the screen (defined in `lobby_config.toml` → `pixel_counter_crop_area`) and counts HSV pixels to determine if super/gadget/hypercharge buttons are active. Uses per-ability pixel thresholds from `bot_config.toml` (`super_pixels_minimum`, `gadget_pixels_minimum`, `hypercharge_pixels_minimum`).

**Poison Gas Detection:** Crops a 1.5× region around the player and checks HSV values for the poison gas indicator color. Returns a directional dict `{"up": count, "down": count, "left": count, "right": count}`.

### Movement System

1. `.iris` script is executed via `interpret_iris_code()` with game context
2. Script returns `movement` = `(x, y)` where -1.0 ≤ x,y ≤ 1.0
3. Coordinates are clamped by `clamp_movement()` to `[-JOYSTICK_RADIUS*ratio, +JOYSTICK_RADIUS*ratio]`
4. Scaled coordinates are sent via `do_movement()` as touch events (touch_down anchor + touch_move target)

### Unstuck System

If movement direction hasn't changed for `unstuck_movement_delay` seconds (configurable in `bot_config.toml`):
1. Movement vector is converted to one of 16 compass directions (0-15)
2. Rotation angle starts at `angle_step * π/4` and increases on each subsequent attempt
3. Rotation alternates sign (`+angle`, `-angle`, `+2*angle`, `-2*angle`, etc.)
4. Once rotated, the direction is held for `unstuck_movement_hold_time` seconds
5. Resets on direction change or invalid movement

### Line of Sight & Collision

- **LOS:** `walls_block_line_of_sight()` — Raycasting from player to enemy, checking intersection with wall tiles via `cv2.clipLine`
- **Swept Circle:** `walls_block_swept_circle()` — Hit-circle collision detection (player hitbox vs walls) using `point_rect_distance_sq()`. Each wall rect is expanded by the hit circle radius before intersection testing.
- **Wall Classes:** Configurable wall model classes (3 or 5 classes) in `bot_config.toml`
- **is_path_blocked():** Checks if a circle swept along a movement direction would intersect wall tiles
- **can_attack_through_walls():** Returns `True` if brawler has `ignore_walls_for_attacks` or `ignore_walls_for_supers` in brawler info
- **must_brawler_hold_attack():** Returns `True` if brawler's `hold_attack > 0`

---

## detect.py — YOLO ONNX Wrapper

**Key Class:** `Detect`

Generic ONNX inference wrapper for YOLO models.

### Provider Selection (priority)
1. CUDA (NVIDIA GPU) → `TensorrtExecutionProvider` / `CUDAExecutionProvider`
2. CoreML (Apple Silicon) → `CoreMLExecutionProvider`
3. DirectML (Windows) → `DmlExecutionProvider`
4. CPU → `CPUExecutionProvider`

### Pipeline
```
detect_objects(image)
  ├── Preprocess: letterbox resize to 640×640, normalize to [0,1]
  ├── ONNX Runtime inference
  ├── Postprocess: _normalize_yolo_output() → _postprocess_raw() → _numpy_nms()
  └── Return: {class_name: [[x1,y1,x2,y2], ...]}
```

### Supported YOLO Output Shapes
- `1×84×8400` (standard)
- `1×8400×84` (transposed)
- `(84, 8400)`, `(8400, 84)` — flat variants

### Thread Configuration
- Thread count from config: `auto` → `min(max(2, CPU//2), 6)`, or explicit integer
- Sets `cv2.setNumThreads` and `torch.set_num_threads`

---

## stage_manager.py — Menu State Machine

**Key Class:** `StageManager`

Handles all non-gameplay screens (menus, results, rewards, shop).

### State Machine

States and their handlers (from `self.states` dict):

| State | Handler | Action |
|-------|---------|--------|
| `lobby` | `start_game()` | Check trophy/wins targets, queue next brawler, press proceed |
| `match_making` | — | Wait (auto) |
| `match` | — | Delegate to `Play.main()` |
| `brawler_selection` | `lambda: 0` | No-op (handled by start_game's auto-select logic) |
| `shop` | `quit_shop()` | Click top-left corner to close |
| `popup` | `close_pop_up()` | Template-match close button |
| `end_victory` / `end_defeat` / `end_draw` | `end_game()` | Process results, "play again" or switch brawler |
| `end_trio_showdown_0` through `end_trio_showdown_3` | `end_game()` | Showdown placement results |
| `star_drop_regular` / `star_drop_angelic` / `star_drop_demonic` / `star_drop_starr_nova` | `click_star_drop(type)` | Handle star drops |
| `trophy_reward` | `press("proceed")` | Trophy reward screen |
| `prestige_milestone` | `press("continue_or_equip")` | Prestige milestone |
| `nano_noodles` | `click_nano_noodles()` | Special event |
| `idle_disconnect` | `handle_idle_disconnect()` | Restart BS on idle/disconnect |

### start_game()
1. Wait 3s for API update (early_access)
2. If `_pending_brawler_switch` is set: try to select new brawler via `LobbyAutomation.select_brawler()`, rotate to end of queue on failure
3. Check if current brawler reached trophy/wins target
4. If yes, switch to next brawler in queue; if queue is empty, stop bot
5. Handle play order rotation
6. Send match webhook ping if due
7. Press the "proceed" button to start match

### end_game()
1. Loop up to 35s while state starts with "end"
2. After 25s, parse game result via `TrophyObserver.parse_game_result()`
3. Update trophy stats: `add_trophies()`, track win/lose streaks
4. Save to `match_history.csv`
5. Send to remote API (unless localhost)
6. On victory and `play_again_on_win` is True: press "play_again"
7. On loss/draw: increment loss counter, check `max_losses`/`max_consecutive_losses`
8. If loss limit exceeded: rotate to lowest-trophy brawler via `_rotate_to_lowest_trophy_brawler()`
9. If end screen visible >35s: restart BS

---

## state_finder.py — Game State Detection

**Key Function:** `get_state(screenshot)`

### Detection Priority Order
1. End-of-match results (victory/defeat/draw/showdown placement via `find_game_result()`)
2. Lobby → `lobby_menu.png`
3. Match making → `exit_match_making.png`
4. Brawler selection → `brawler_menu_heart.png`
5. Shop → `powerpoint.png`
6. Offer popup → `close_popup.png`
7. Brawl pass → `brawl_pass_house.png`
8. Star road → `go_back_arrow.png`
9. Prestige milestone → `prestige_continue.png`
10. Nano noodles → `nano_noodles.png`
11. Star drops (4 types: regular, angelic, demonic, starr_nova)
12. Trophy reward screen → `trophies_screen.png`
13. Idle/disconnect → `idle_disconnect.png` (threshold 0.6)
14. Default: "match"

### How It Works
- Uses `cv2.matchTemplate` with `TM_CCOEFF_NORMED` on template images from `images/states/`
- Region-based matching from `lobby_config.toml` → `template_matching` section
- Each state has a defined region of interest and confidence threshold (default 0.75, idle at 0.6)
- Templates are cached globally by `(path, width, height)` key
- `find_game_result()` checks `images/end_results/` for:
  - Showdown placement (1st-4th) with `SHOWDOWN_PLACE_THRESHOLD = 0.9`
  - Victory, defeat, draw templates
- Debug frame writing every 5s if `state_finder_debug` is enabled

---

## window_controller.py — ADB + Scrcpy Controller

**Key Class:** `WindowController`

### Device Discovery
- `discover_device()` — Scans common Android emulator ports in parallel (up to 20 threads)
- Ports scanned: [5137, 5555, 16384, 7555, 5635, 62001, 62025, 62026, 7556, 7565, 16416, 5554] + ranges 5556-5566 + 5565-5756 step 10
- Respects `emulator_port` config for preferred port
- Uses `adbutils` library for ADB communication
- Auto-discovers Brawl Stars package from `KNOWN_BS_PACKAGES = ("com.supercell.brawlstars", "bsd.suitcase.release")`
- `force_rediscover()` — Stops scrcpy, restarts ADB, re-discovers device
- `restart_adb_server()` — Kills and restarts ADB daemon

### Frame Capture
- Starts `scrcpy.Client` in threaded mode for continuous low-latency screen capture
- H.264 video decoded via PyAV (FFmpeg bindings), bitrate 8Mbps
- Optional `max_fps` throttling passed to scrcpy client
- `get_latest_frame()` returns `(frame, timestamp)` tuple — thread-safe access
- Stale frame detection at `FRAME_STALE_TIMEOUT = 15` seconds
- Waits up to 15s for first frame on startup

### Touch Injection
| Method | Action |
|--------|--------|
| `touch_down(x, y, pointer_id=0)` | Press at coordinates |
| `touch_move(x, y, pointer_id=0)` | Move touch |
| `touch_up(x, y, pointer_id=0)` | Release |
| `click(x, y)` | Quick tap (with ratio scaling, touch_up/down toggles) |
| `swipe(x1, y1, x2, y2, duration)` | Linear interpolation swipe (25px step) |
| `press(key)` | Key event via buttons_config (attack, super, gadget, etc.) |
| `move(x, y)` | Joystick: touch_down at center, touch_move to target. Optimized to skip if `re_apply_movement=False` and position unchanged |
| `release_movement()` | Release joystick (touch_up at center) |

### Pointer IDs
- `PID_JOYSTICK = 1` — Joystick control
- `PID_ATTACK = 2` — Attack button

### Resilience
- `FRAME_STALE_TIMEOUT = 15` seconds
- `reconnect_scrcpy(max_retries=3)` — Full reconnection: stop scrcpy, reconnect ADB, re-create client, wait for fresh frame (< 2s age)
- `restart_brawl_stars()` — Stop/start app via ADB, with background thread + timeout
- `stop_scrcpy_with_timeout(timeout=2.0)` — Stops scrcpy in a thread with join timeout
- Retry with reconnect on touch failures

---

## lobby_automation.py — Brawler Selection via OCR

**Key Class:** `LobbyAutomation`

### select_brawler(brawler_name, get_latest_state, stop_event, runtime_control)
1. Click brawlers menu button, wait 0.5s
2. Loop up to 100 iterations:
   - Take screenshot, downsize by `ocr_scale_down_factor` (clamped 0.5-1.0, from `general_config.toml`)
   - Run EasyOCR via `extract_text_and_positions()`
   - Clean up OCR results (remove spaces/dots/hyphens)
   - Run **template matching** on full-resolution screenshot (`is_in_brawler_selection`, `is_in_lobby` from `state_finder`) to determine actual screen state
   - If template confirms brawler_selection → proceed with OCR matching regardless of OCR text
   - Else if template says lobby OR OCR detects "shop" text → retry (screen may not have updated, up to 6 attempts then return "stuck")
   - Else if background state checker says not brawler_selection → abort
   - Match brawler name directly or via aliases from `cfg/names.json`
   - On match: click on detected text center (with y-offset), click "select" button
   - Scroll down via swipe (first scroll: short 850px; subsequent: full 650px)
3. Returns: `"success"`, `"failed"`, `"error"`, `"aborted"`, or `"stuck"`
4. Supports interruptible sleep with stop/pause checking
5. In `main.py`, if `select_brawler` returns "stuck" 3+ times, the bot skips auto-pick and continues with the current brawler selection (prevents infinite retry loops)

### check_for_idle()
- Crops center area `(460..1460, 400..675)`
- Detects idle screens via gray pixel counting (HSV range `((0,0,10)-(30,60,67))`)
- Threshold: `idle_pixels_minimum` from bot_config (default 500)
- Clicks reconnect button on idle/disconnect screens

---

## trophy_observer.py — Trophy & Win Tracking

**Key Classes:** `TrophyObserver`, `ParsedGameResult` (dataclass), `GameMode` (enum: CLASSIC, TRIO_SHOWDOWN), `MatchResult` (enum: VICTORY, DRAW, DEFEAT)

### Trophy Calculation
Complex range-based system per trophy bracket:

| Trophy Range | Win Gain | Loss Cost |
|-------------|----------|-----------|
| < 1999 | +8 to +10 | -1 to -4 |
| < 2499 | +6 to +8 | -4 to -6 |
| < 2999 | +5 to +7 | -6 to -8 |
| < 3099 | +4 to +6 | -7 to -9 |
| ≥ 3099 | +1 to +5 | -8 to -15 |

- Win streak bonus: `min(win_streak - 1, 10)` only for trophies < 2000; 0 otherwise
- Showdown/trio: per-placement deltas at each bracket, win_streak_gain applies if place < 2
- Trophy multiplier from `general_config.toml`
- Hard floors: trophies can't go below 1000 if ≥ 1000, or below 2000 if ≥ 2000
- End-game loss threshold protection (stops losing at configured limits)

### Match History
- Saved to `cfg/match_history.csv` via pandas DataFrame
- Columns: datetime, brawler, game_mode, result, trophy_change, trophies, win_streak
- `send_results_to_api()` pushes unsent matches to `https://{api_base_url}/api/matches` (disabled on localhost)
- Logged: win_streak, lose_streak, total_losses, match_counter

### ParsedGameResult
```python
@dataclass
class ParsedGameResult:
    gamemode: GameMode        # CLASSIC or TRIO_SHOWDOWN
    result: MatchResult       # VICTORY, DRAW, or DEFEAT
    place: Optional[int] = None  # Showdown placement (0-3)
    raw_string: str = ""
```

---

## time_management.py — Periodic Timer Scheduler

**Key Class:** `TimeManagement`

Threshold-based timers from `cfg/time_tresholds.toml`. `check_time(type)` compares `current_time - timer` against threshold and resets timer on each True return.

| Timer | Purpose | Config Key |
|-------|---------|------------|
| `state_check()` | Frequency of game state checking | `state_check_seconds` |
| `no_detections_check()` | Timeout for detection failures | `no_detections_timeout` |
| `idle_check()` | Frequency of idle screen checking | `idle_check_seconds` |

Additional timers for periodic tasks in `Play` (from `time_tresholds.toml` → `timer_frequencies`):
| Timer | Purpose |
|-------|---------|
| `super` | Check super readiness interval (frames) |
| `hypercharge` | Check hypercharge readiness interval (frames) |
| `gadget` | Check gadget readiness interval (frames) |
| `wall_detection` | Run wall detection every N frames |
| `no_detection_proceed` | Press "proceed" after N frames without detection |
| `check_if_brawl_stars_crashed` | Check for BS crash every N seconds |

---

## debug_view.py — Real-Time Debug Overlay

**Key Classes:** `DebugViewPublisher`, `DebugClipRecorder`

### DebugViewPublisher
- Creates `multiprocessing.shared_memory` segments for zero-copy frame sharing
- Spawns subprocess running `run_viewer_worker()` with OpenCV
- FPS throttled (default 30fps, configurable from `debug_settings.toml`)
- Static `from_config()` classmethod creates instance from settings
- On error: auto-disables debug view and closes

### Viewer Rendering
- `draw_debug_data()` master function renders:
  - Player (green box + hit circle), enemies (red), teammates (blue)
  - Attack range (red circle) and super range (yellow circle)
  - Wall tiles and bushes
  - Poison gas direction lines (green, per-direction)
  - LOS ray lines (white) and hit circles
  - Joystick path probe (colored arc sectors: red=blocked, green=open)
  - Movement indicator
  - State text overlay
- Key bindings: `F`/`F11` toggle fullscreen, `ESC`/`q`/`Q` quit

### DebugClipRecorder
- Records debug overlay to MP4 when player is detected
- Pre-buffers frames before player detection for context
- Requires minimum `min_player_seen_before_recording` frames before starting
- Stops recording when player not seen for `missing_player_grace` seconds
- Uses `cv2.VideoWriter` with MP4V codec

### IPC
- Publisher serializes detection data as JSON into shared memory (256KB buffer)
- Frame data shared via a second shared memory segment (raw bytes)
- Header format: 8 bytes frame_id + 4 bytes data_size
- Truncates data if walls array exceeds buffer size

---

## scrcpy/ — Bundled Python Scrcpy Client

### core.py — Client
- `Client.deploy_server()` — Uploads `scrcpy-server.jar` to Android device
- `Client.start()` — Establishes video + control sockets via ADB tunnels
- `Client.stream_loop()` — Decodes H.264 via PyAV, dispatches frames to listeners
- Threaded mode for non-blocking frame capture

### control.py — ControlSender
Decorator-based injection: `@inject(control_type)` packs type byte + payload and sends via control socket with lock.

Methods:
- `keycode(keycode, action, repeat)` — Send key event
- `text(text)` — Send text input
- `touch(x, y, action, touch_id)` — Touch event (down/up/move)
- `scroll(x, y, h, v)` — Scroll event
- `back_or_turn_screen_on(action)` — Back key / screen on
- `expand_notification_panel()` / `expand_settings_panel()` / `collapse_panels()`
- `set_clipboard(text, paste)` / `get_clipboard() -> str`
- `set_screen_power_mode(mode)` — Screen on/off
- `rotate_device()` — Rotate screen
- `swipe(x1, y1, x2, y2, move_step_length=5, move_steps_delay=0.005)` — Step-by-step swipe

### const.py
All Android keycodes (`KEYCODE_*`), action constants (`ACTION_DOWN/UP/MOVE`), event types.

---

## webui/ — Flask Web Dashboard

### app.py — Flask App
- `create_app(iris_main, start_discord_bot)` — WSGI factory
- Routes: queue management (CRUD, import, reorder, push-all-to-target, clear-all), playstyles (list/delete/import/activate), settings (6 sections + reset per section), runtime control (start/pause/stop + status polling), player info, match history, login validation, bootstrap data, asset serving
- Discord bot injection via `_Suppress*` middleware classes (suppresses polling noise from werkzeug logs)
- Error handling: 400 for `KeyError`/`FileNotFoundError`/`ValueError`, 500 for unexpected
- `_start_discord_bot_thread()` — Starts Discord bot in daemon thread

### runtime.py — Runtime Manager
**Key Classes:** `RuntimeManager`, `RuntimeControl`

**RuntimeControl** — Thread-safe wrapper using `threading.Event`:
- `request_pause()` / `resume()` / `request_stop()` — event setters/clearers
- `should_stop()` / `should_pause()` — event checkers (pause defers to stop)
- `mark_running()` / `mark_paused()` — state callbacks

**RuntimeManager** — Thread lifecycle:
- States: `idle → running → pausing → paused → running` or `→ stopping → idle` or `→ error → idle`
- `_run_worker()` — Calls `iris_main(discord_bot, queue_data, runtime_control=control)`
- `start()`: If paused → resume. If idle → start new thread (with auth + queue checks)
- `pause()`: Running → pausing. Already paused → ok.
- `stop()`: Handles idle/paused/running states appropriately
- `get_status()`: Returns state, is_running, last_error. Auto-transitions to "idle" if thread died.

### services.py — WebDataService
- **Queue**: CRUD, reorder, import JSON, push-all-to-default-target (auto-fill queue from API), clear-all, sync with saved file
- **Settings**: Schema-based serialization for 6 sections + `timer_frequencies` (8th section):
  - `GENERAL_FIELDS` (12): run_for_minutes, player_tag, default_trophy_target, play_order, max_ips, used_threads, ocr_scale_down_factor, brawl_stars_package, emulator_port, trophies_multiplier, auto_load_queue_on_startup, alarm_enabled
  - `DEBUG_FIELDS` (7): verbose_debug, state_finder_debug, re_apply_movement, debug_view, debug_view_fps, advanced_debug_visuals, record_debug_preview_clips
  - `BOT_FIELDS` (14): play_again_on_win, minimum_movement_delay, unstuck_movement_delay, unstuck_movement_hold_time, perceived_tile_size, centered_wall_detection, wall_detection_confidence, entity_detection_confidence, seconds_to_hold_attack_after_reaching_max, idle_pixels_minimum, super/gadget/hypercharge_pixels_minimum, max_losses, max_consecutive_losses
  - `TIMER_FIELDS` (8): super, hypercharge, gadget, wall_detection, no_detection_proceed, state_check, idle, check_if_brawl_stars_crashed
  - `WEBHOOK_FIELDS` (10): webhook_url, discord_id, discord_bot_token, discord_guild_id, telegram_token, telegram_chat_id, ping_when_stuck, ping_when_target_is_reached, ping_every_x_match, ping_every_x_minutes
- **Playstyles**: list, activate, delete, import from uploaded `.iris`
- **Match history**: Load from CSV, aggregate stats (wins/losses per brawler, win rates)
- **Player info**: Fetch from Brawlify/BS API, cache, validate early access login
- **Auth**: `get_auth_state()` / `validate_login()` — API key validation
- **Bootstrap**: `get_bootstrap_payload()` — all data for initial page load
- **Startup**: load queue from saved file if `auto_load_queue_on_startup=True`

---

## terminal_ui.py — Terminal UI (Splash, Dashboard, Logging)

**Standalone module** — no dependencies on other project modules (only `os`, `sys`, `time`, `datetime`).

### Components

| Function | Purpose |
|----------|---------|
| `print_splash()` | Prints IrisAI ASCII logo (cyan box, white bold title, dim GitHub link) |
| `print_crash_banner()` | Prints bold red "BOT CRASHED" banner with link to logs |
| `setup_session_logging()` | Tee's `sys.stdout`/`sys.stderr` to both console and `logs/session_<timestamp>.log`. Sets up `LOG_DIR` if missing. Returns log path. |
| `build_status_line(...)` | Builds a color-formatted status string: `IPS │ Brawler │ State │ Trophies │ Playstyle │ Session Time` |
| `save_status_cursor()` | Saves cursor position with `\033[s` before main loop starts |
| `update_status(...)` | Restores to saved cursor via `\033[u`, clears to end of screen via `\033[J`, prints status. Handles terminal resize without artifacts (old `\r` approach left wrapped lines visible). |

### Style Class

ANSI escape code constants for 24-bit terminal colors:
- `CYAN`, `WHITE`, `GRAY`, `GREEN`, `RED`, `YELLOW`, `MAGENTA`, `BLUE`
- `BOLD`, `DIM`, `RESET`, `CLEAR_LINE`

### Session Logging

- All output goes to `logs/session_<timestamp>.log` (rotated per launch)
- `*.log` and `logs/` are gitignored
- Disable with `IRIS_LOG=0` env var
- Crash banner shown via `sys.excepthook` override + try/except around `app.run()`
- `KeyboardInterrupt` passes through without crash banner
