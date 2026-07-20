# Architecture

## High-Level System Design

```
┌──────────────────────────────────────────────────────────────────┐
│                        main.py (pyla_main)                       │
│                                                                  │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────┐              │
│  │ Play         │  │ Stage    │  │ Lobby        │              │
│  │ (in-game AI) │  │ Manager  │  │ Automation   │              │
│  │              │  │ (menu    │  │ (OCR brawler │              │
│  │ • Detection  │  │  FSM)    │  │  selection)  │              │
│  │ • Movement   │  │          │  │              │              │
│  │ • Combat     │  │ • start  │  │ • select_    │              │
│  │              │  │   game   │  │   brawler   │              │
│  │ • 3 ONNX     │  │ • end_   │  │ • idle      │              │
│  │   models     │  │   game   │  │   detection  │              │
│  └──────┬───────┘  └────┬─────┘  └──────┬───────┘              │
│         │               │               │                       │
│         ▼               ▼               ▼                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              WindowController (scrcpy + ADB)            │    │
│  │  • Frame capture (scrcpy, 60fps H.264)                  │    │
│  │  • Touch injection (ADB/scrcpy control socket)          │    │
│  │  • Device discovery (parallel port scan)                │    │
│  │  • Auto-reconnect (3 retries, ADB rediscovery)          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐      │
│  │ State        │  │ Time         │  │ TrophyObserver   │      │
│  │ Checker      │  │ Management   │  │ • trophy calc    │      │
│  │ Thread       │  │ (periodic    │  │ • match history  │      │
│  │ (daemon)     │  │  timers)     │  │ • CSV logging    │      │
│  └──────────────┘  └──────────────┘  └──────────────────┘      │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              DebugViewPublisher (subprocess)             │    │
│  │  • Shared memory IPC for frame + detection data          │    │
│  │  • OpenCV overlay rendering (boxes, ranges, LOS)        │    │
│  │  • MP4 clip recording on player detection                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              RuntimeManager (threading.Event)            │    │
│  │  • start/pause/stop state machine                        │    │
│  │  • Worker thread for bot loop                            │    │
│  │  • Flask ↔ Discord ↔ Main comms bridge                  │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
            │                        │
            ▼                        ▼
    ┌──────────────┐       ┌──────────────────┐
    │ Flask Web UI │       │  Discord Bot     │
    │ (port 5000+) │       │  (slash cmds)    │
    │              │       │                  │
    │ • Queue mgmt │       │ • /screenshot    │
    │ • Settings   │       │ • /stop /pause   │
    │ • Playstyles │       │ • /start /status │
    │ • Runtime    │       │ • /queue /help   │
    │ • History    │       │ • /restart_bs    │
    └──────────────┘       └──────────────────┘
```

## Threading Model

The system runs 5+ concurrent threads:

1. **Main Bot Thread** (`Main.main()`) — The core loop: grab frame → run AI → send touch. Runs at configurable IPS (iterations per second). Stop/pause signals are only honored when state is `"lobby"` (to avoid interrupting active matches). Automatic first-brawler selection runs on lobby entry.

2. **State Checker Thread** (daemon) — Continuously calls `get_state(frame)` from `state_finder.py` to detect the current game screen (lobby, match, shop, idle_disconnect, etc.). Updates shared state for the main loop. Runs at frame rate (unthrottled).

3. **Scrcpy Listener Thread** — Built into the scrcpy client. Decodes H.264 video via PyAV and dispatches frames to registered listeners. Runs at device framerate (~60fps). Supports bitrate 8Mbps and optional `max_fps` throttling.

4. **Flask Server Thread** — Serves the web UI on `127.0.0.1:<port>`. Provides REST API endpoints for queue, settings, playstyles, runtime control, login validation, and brawler asset serving. Auto-opens browser on startup.

5. **Discord Bot Thread** — Runs the discord.py client with app commands for remote control. Authorized by Discord user ID and guild ID from config. Uses `discord_guild_id` for command tree sync (preferred over global sync).

6. **DebugView Subprocess** — Separate process launched via `multiprocessing`. Reads shared memory segments to render debug overlays via OpenCV.

## Key Design Patterns

- **Config-Driven Architecture**: Almost every tunable parameter lives in TOML/JSON files under `cfg/`. No hardcoded timings, thresholds, or button coordinates.

- **Auto-First-Brawler Picker**: If the queue is empty, the bot auto-picks the first available brawler in a lobby. On failure (e.g. OCR miss), it rotates the brawler to the end of the queue and retries.

- **Playstyle Scripting System**: In-game behavior is defined in `.pyla` files — Python scripts executed via `exec()` with a sandboxed `SAFE_GLOBALS` context. The active playstyle is set in `bot_config.toml`. Each script has a JSON metadata header on line 1.

- **Unstuck Rotation System**: If movement direction hasn't changed for `unstuck_movement_delay` seconds, the vector is progressively rotated by `angle_step * π/4` (alternating sign) to escape stalemates. The rotated direction is held for `unstuck_movement_hold_time` seconds before further rotation.

- **Frame Cache & Dedup**: The main loop deduplicates frames by timestamp to avoid redundant processing. Detection data is cached and reused when frames haven't changed.

- **Graceful Degradation**: Model inference falls back from CUDA → CoreML → DirectML → CPU. Wall detection has centered-crop fallback. Scrcpy has multi-retry reconnect.

- **Nuitka Compatibility**: The project can be compiled to a standalone executable via Nuitka. Special handling is in place for `inspect.getfile` monkey-patching and frozen imports.

## Package Structure

```
IrisAI-main 2/
├── main.py                 # Entry point
├── play.py                 # In-game AI
├── detect.py               # YOLO ONNX wrapper
├── stage_manager.py        # Menu FSM
├── state_finder.py         # State detection
├── window_controller.py    # ADB + scrcpy
├── lobby_automation.py     # OCR brawler selection
├── trophy_observer.py      # Trophy tracking
├── time_management.py      # Periodic timers
├── discord_bot.py          # Discord commands
├── debug_view.py           # Debug overlay
├── utils.py                # Shared utilities
├── setup.py                # Package installer
├── api/                    # API module
│   └── api.py
├── webui/                  # Flask web dashboard
│   ├── app.py
│   ├── runtime.py
│   └── services.py
├── scrcpy/                 # Bundled scrcpy client
│   ├── core.py
│   ├── control.py
│   ├── const.py
│   └── scrcpy-server.jar
├── cfg/                    # Configuration files
│   ├── general_config.toml
│   ├── bot_config.toml
│   ├── lobby_config.toml
│   ├── buttons_config.toml
│   ├── time_tresholds.toml
│   ├── webhook_config.toml
│   ├── debug_settings.toml
│   ├── login.toml
│   ├── brawlers_info.json
│   ├── names.json
│   ├── brawlers_info.json
│   ├── names.json
│   ├── match_history.csv
│   └── latest_brawler_data.json  (auto-generated queue state)
├── models/                 # ONNX + EasyOCR models
│   ├── mainInGameModel.onnx
│   ├── tileDetector.onnx
│   ├── closeTileDetector.onnx
│   └── easyocr/
├── playstyles/             # .pyla behavior scripts
│   ├── skeleton.py                          (reference template)
│   ├── default_up.pyla
│   ├── default_right.pyla
│   ├── follower.pyla
│   ├── showdown_survivor.pyla
│   ├── team_showdown.pyla
│   ├── universal_smart_v5_Slarckvul_Eddition.pyla
│   ├── universal_smart_v5_Slarckvul_RUSH.pyla
│   └── skeleton.py                          (API-generated or uploaded .pyla files appear here)
├── images/                 # Template images
│   ├── states/
│   └── end_results/
├── static/                 # Web frontend assets
│   ├── css/
│   └── js/
├── templates/              # Flask templates
│   └── index.html
└── sounds/                 # Alarm sounds
```
