# Architecture

## High-Level System Design

```
┌──────────────────────────────────────────────────────────────────┐
│                        main.py (iris_main)                       │
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
│  │              RuntimeTelemetry (in-memory)                │    │
│  │  • readable state, brawler, session and match events     │    │
│  │  • one shared snapshot for terminal and Web UI           │    │
│  │  • bounded to 300 events and 10 recent matches           │    │
│  └─────────────────────────────────────────────────────────┘    │
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

1. **Main Bot Thread** (`Main.main()`) — The core loop: grab frame → run AI → send touch. Runs at configurable IPS. Stop is honored immediately; pause waits for the lobby so a match is not left half-finished.

2. **State Checker Thread** (daemon) — Continuously calls `get_state(frame)` from `state_finder.py`. Updates shared `current_state`. Runs at frame rate.

3. **Scrcpy Listener Thread** — Built into the scrcpy client. Decodes H.264 video via PyAV and dispatches frames to registered listeners. Runs at ~60fps.

4. **Flask Server Thread** — Serves the web UI on `127.0.0.1:<port>`. REST API for queue, settings, playstyles, runtime control, etc.

5. **Discord Bot Thread** — Runs the discord.py client with slash commands for remote control.

6. **DebugView Subprocess** — Separate process via `multiprocessing`. Reads shared memory segments to render OpenCV debug overlays.

7. **RuntimeTelemetry** — A lock-protected in-memory event model shared by the
   bot loop, `RuntimeManager`, trophy observer, terminal dashboard, and Web UI.
   It holds the current run fields, session totals, readable recent events, and
   the ten newest match results. It does not write persistent history itself:
   `TrophyObserver` remains responsible for the CSV record.

## Key Design Patterns

- **Config-Driven**: Almost every tunable parameter lives in TOML/JSON under `cfg/`.
- **Auto-First-Brawler Picker**: Auto-selects first available brawler; rotates on OCR failure.
- **Playstyle Scripting System**: `.iris` files executed via `exec()` with sandboxed `SAFE_GLOBALS`.
- **Unstuck Rotation System**: Progressive angle rotation (π/4 increments, alternating sign) when stuck.
- **Frame Cache & Dedup**: Timestamp-based frame deduplication (currently dead code — frame_time always 0).
- **Graceful Degradation**: CoreML → CPU provider fallback on macOS.
- **Nuitka Compatibility**: `inspect.getfile` monkey-patch for compiled executables.
- **Defensive Runtime Edges**: Queue normalization, safe config defaults, guarded template matching, and append-only match history are used to keep the Web UI and bot thread alive through malformed local state.
- **Runtime Data Boundary**: Mutable queue state, history, logs, and debug frames live under `.iris_runtime/` by default and can be moved with `IRIS_RUNTIME_DIR`.
- **Shared Runtime Telemetry**: `runtime_events.py` turns lifecycle and match
  changes into bounded, readable events. The terminal and `/api/runtime/status`
  consume the same snapshot, so normal operation is not driven by scrolling
  debug output. It also exposes whether a diagnostic session is recording and
  the absolute output path.
- **Finalized Diagnostic Logs**: `terminal_ui.SessionLogCapture` captures
  technical stdout/stderr only when `--log` or `--debug` is active. Shutdown
  appends a JSON session snapshot and exit reason, restores the original streams,
  closes the file, and prints the saved path. An `atexit` close is the fallback.
- **Joined Runtime Shutdown**: Process shutdown requests an immediate bot stop
  and joins the runtime worker before Python tears down the inference executor.
  This prevents late `cannot schedule new futures after shutdown` errors.

## Package Structure

```
IrisAI/
├── main.py                 # Entry point
├── play.py                 # In-game AI (830 lines)
├── detect.py               # YOLO ONNX wrapper
├── stage_manager.py        # Menu FSM
├── state_finder.py         # State detection via template matching
├── window_controller.py    # ADB + scrcpy controller
├── lobby_automation.py     # Text-based brawler selection via Vision/EasyOCR
├── native/                 # Native macOS helpers (Vision OCR)
├── trophy_observer.py      # Trophy tracking & match history
├── time_management.py      # Periodic timer scheduler
├── discord_bot.py          # Discord slash commands
├── debug_view.py           # Debug overlay subprocess
├── utils.py                # Shared utilities
├── config_loader.py        # Config defaults env override
├── network.py              # HTTP client with retry/backoff
├── terminal_ui.py          # Quiet terminal dashboard and crash banner
├── runtime_events.py       # Shared current-run telemetry and event model
├── threading_utils.py      # Thread utilities
├── runtime_paths.py        # Runtime data path helpers
├── health.py               # Install/runtime health checks
├── build_nuitka.py         # Nuitka build script
├── setup.py                # Package installer
├── install.py              # First-run model downloader
├── api/assets/              # Local brawler icon catalog
├── webui/
│   ├── __init__.py
│   ├── app.py              # Flask routes
│   ├── runtime.py          # RuntimeManager (thread lifecycle)
│   └── services.py         # WebDataService (data layer)
├── scrcpy/                 # Bundled scrcpy client
│   ├── core.py             # Client (deploy, stream)
│   ├── control.py          # ControlSender (touch, keycode, swipe)
│   ├── const.py            # Android keycodes
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
│   ├── match_history.csv
│   └── latest_brawler_data.json  (auto-generated queue state)
├── models/                 # ONNX + EasyOCR models
│   ├── mainInGameModel.onnx
│   ├── tileDetector.onnx
│   ├── closeTileDetector.onnx
│   ├── manifest.json
│   └── easyocr/ (craft_mlt_25k.pth, english_g2.pth)
├── playstyles/             # .iris behavior scripts
│   ├── skeleton.py         (reference template)
│   ├── aggressive_universal.iris
│   ├── aggressive_rush.iris
│   ├── aggressive_balanced.iris
│   ├── knockout.iris
│   ├── lane_up.iris
│   ├── lane_right.iris
│   ├── showdown_survival.iris
│   ├── showdown_team.iris
│   └── team_follow.iris
├── images/
│   ├── states/ (14 template PNGs)
│   ├── end_results/ (8 result images)
│   └── star_drop_types/ (4 star drop images)
├── static/
│   ├── css/tailwind.css
│   └── js/app.js
├── templates/
│   └── index.html
└── sounds/
    └── u_inx5oo5fv3-alarm-327234.mp3
```

Runtime-generated files are not part of the package tree:

```
.iris_runtime/
├── latest_brawler_data.json
├── match_history.csv
├── logs/
└── debug_frames/
```

Diagnostic images and preview clips share a bounded retention policy (100 files
and 500 MB by default). Oldest files are removed first. Training datasets live
outside `debug_frames/` and are not affected.
