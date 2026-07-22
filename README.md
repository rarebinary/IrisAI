# IrisAI

<p align="center">
  <img src="images/irisai-runbook.svg" alt="IrisAI runbook logo" width="144">
</p>

<p align="center"><strong>See the grind. Automate it.</strong></p>

IrisAI is a local-first Brawl Stars automation bot built exclusively for macOS. It reads the game through computer vision, controls an Android emulator or device through ADB, and runs configurable `.iris` playstyles during matches.

The bot does not inject code into the game or modify game files. Frames, detections, match history, and diagnostic captures stay on the Mac unless an optional remote integration is configured.

## What It Does

- Runs matches with local YOLO/ONNX computer vision and ADB input.
- Selects queued brawlers by reading their names from the game UI.
- Tracks trophies, wins, losses, win streaks, and recent matches.
- Shows a quiet local dashboard with runtime state, the current run, recent matches, and recent events.
- Recovers from known idle-disconnect and reconnect dialogs.
- Supports editable playstyles for movement, targeting, attacks, supers, gadgets, and hypercharges.
- Saves a complete session log with `--log` for later debugging.
- Uses CoreML on Apple Silicon when available, with a CPU fallback.

IrisAI currently controls one connected Android target per running process. Multi-device orchestration is not implemented.

## Platform

| Mac | Status | Inference |
|---|---|---|
| Apple Silicon | Primary target | CoreML or CPU |
| Intel | Supported | CPU |

Other operating systems are intentionally unsupported. IrisAI expects macOS and an Android emulator or device with a working ADB connection.

## Quick Start

### Requirements

- macOS
- Python 3.11 or newer
- Git
- An Android emulator or device with ADB enabled
- Brawl Stars installed on that Android target

### Install

```bash
git clone https://github.com/rarebinary/IrisAI.git
cd IrisAI
python3 install.py
```

The installer selects a suitable inference runtime, downloads models from GitHub Releases, checks ADB, and creates a local `.env` template. It does not configure an emulator for you.

### Run

```bash
python3 main.py
```

The terminal shows the Web UI address after startup. You can also double-click `run.command` from Finder.

For a diagnostic session:

```bash
python3 main.py --log
```

The dashboard displays the log path. On a normal stop or `Ctrl+C`, IrisAI closes the file and prints its location so it can be attached to a bug report.

## Commands

| Command | Description |
|---|---|
| `python3 main.py` | Start IrisAI and its local Web UI |
| `python3 main.py --log` | Start and save a detailed session log |
| `python3 main.py --debug` | Show detailed terminal output and stack traces |
| `./run.command` | Launch from macOS Finder or Terminal |
| `iris self-update` | Pull the current Git branch and refresh Python dependencies |
| `iris update-models` | Download and verify the configured ONNX models |
| `python3 install.py --cpu` | Force the CPU runtime |
| `python3 install.py --coreml` | Request CoreML on Apple Silicon |
| `python3 install.py --dry-run --no-adb --cpu` | Preview installation and run local checks |
| `python3 build_nuitka.py` | Build `dist/IrisAI.app` |

The `iris` command becomes available after an editable package install, including `python3 install.py --dev`.

## Runtime Data

Generated data is kept outside the source tree under `.iris_runtime/`:

- `logs/` contains opt-in session logs.
- `debug_frames/` contains recent diagnostic captures.
- `training/` contains captures intentionally collected for model training.
- Queue and match-history files preserve local runtime state.

Diagnostic captures are automatically limited by file count and disk usage. Training captures and session logs are not removed by that cleanup. Set `IRIS_RUNTIME_DIR` to move all runtime data elsewhere.

## Configuration

Configuration precedence is `.env`, then `cfg/*.toml`, then code defaults. See [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md) and [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

Important files:

| File | Purpose |
|---|---|
| `cfg/general_config.toml` | ADB target, inference, OCR, scheduling, and runtime behavior |
| `cfg/bot_config.toml` | Active playstyle, movement, combat, and detection thresholds |
| `cfg/time_tresholds.toml` | State and recovery timers |
| `cfg/buttons_config.toml` | Reference-screen input coordinates |
| `cfg/debug_settings.toml` | Debug display and diagnostic capture retention |
| `cfg/webhook_config.toml` | Optional Discord and Telegram settings |

Secrets belong in `.env`, not in tracked TOML files. Discord control is optional; the local bot and Web UI do not require Discord credentials.

## Playstyles

The active playstyle is selected in `cfg/bot_config.toml`:

```toml
current_playstyle = "aggressive_universal.iris"
```

Included playstyles:

| File | General intent |
|---|---|
| `aggressive_balanced.iris` | Balanced aggressive movement and combat |
| `aggressive_rush.iris` | Direct pressure and close engagement |
| `aggressive_universal.iris` | General-purpose aggressive behavior |
| `knockout.iris` | Knockout-oriented positioning |
| `lane_right.iris` | Favors the right lane |
| `lane_up.iris` | Favors forward movement |
| `showdown_survival.iris` | Survival-oriented Showdown behavior |
| `showdown_team.iris` | Team Showdown behavior |
| `team_follow.iris` | Follows the nearest teammate |
| `skeleton.py` | Reference context and playstyle template |

Playstyles receive detected entities, walls and bushes, readiness flags, movement history, geometry helpers, and action functions. The exact supported context is documented in [docs/PLAYSTYLE_SYSTEM.md](docs/PLAYSTYLE_SYSTEM.md) and `playstyles/skeleton.py`.

## Web UI

The local Web UI provides:

- A light or dark dashboard with bot, emulator, state, and playstyle status.
- Current brawler, trophies, win streak, session totals, and last result.
- The ten most recent matches and a short recent-event list.
- Queue creation, ordering, import, export, and trophy targets.
- Playstyle import, selection, and deletion.
- Match history and per-brawler statistics.
- Validated editors for the supported TOML settings.
- Normal and debug log views.

See [docs/WEBUI.md](docs/WEBUI.md) for the API and runtime details.

## Optional Discord Control

When Discord credentials are configured, these slash commands are registered:

| Command | Description |
|---|---|
| `/screenshot` | Upload the current emulator frame |
| `/start` | Start or resume the runtime |
| `/pause` | Request a pause |
| `/stop` | Stop the runtime gracefully |
| `/status` | Show the current runtime status |
| `/restart_brawl_stars` | Restart the game application |
| `/view_queue` | Show the current brawler queue |
| `/help` | Show available commands |

## Architecture

```text
Android emulator/device
        | ADB + scrcpy frames
        v
WindowController -> StateFinder / Detect -> StageManager / Play
        ^                                      |
        | ADB touch input                      v
        +------------------------------- .iris playstyle

RuntimeEvents -> terminal dashboard + local Flask Web UI
```

Core modules:

- `main.py`: CLI, lifecycle, and runtime orchestration.
- `window_controller.py`: macOS ADB connection, frames, and input.
- `state_finder.py`: screen-state and reconnect-dialog detection.
- `detect.py`: ONNX entity and map inference.
- `stage_manager.py`: lobby-to-match state machine.
- `lobby_automation.py`: OCR-based brawler selection and lobby actions.
- `play.py`: in-match detection, playstyle execution, and movement.
- `runtime_events.py`: shared status, recent events, and match telemetry.
- `webui/`: local Flask API and dashboard.

More detail is available in [docs/README.md](docs/README.md).

## Build

```bash
python3 -m pip install nuitka
python3 build_nuitka.py
```

The output is `dist/IrisAI.app`. Build and distribution notes are in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Troubleshooting

| Problem | First check |
|---|---|
| ADB is unavailable | Install `android-platform-tools` with Homebrew and verify `adb devices` |
| Models are missing or corrupt | Run `iris update-models` |
| CoreML fails to initialize | Set `cpu_or_gpu = "cpu"` in `cfg/general_config.toml` |
| Inputs are offset | Start the emulator before IrisAI so its resolution can be detected |
| Discord commands do not appear | Verify the optional bot token, guild ID, user ID, and application command scope |
| A session fails unexpectedly | Re-run with `python3 main.py --log` and attach the saved log |

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for known issues and fixes.

## Development

Run the automated checks before opening a pull request:

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q -x '(^|/)(\.git|\.iris_runtime|venv|dist|build)/' .
```

Keep runtime files out of commits, update the relevant file under `docs/` after behavior changes, and add focused tests for bug fixes.

## License and Game Policy

IrisAI is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International license](LICENSE).

This is an unofficial educational project and is not affiliated with or endorsed by Supercell. Automation may violate the game provider's terms and may put an account at risk. Use it only where you have permission and accept that risk.

## Maintainer

- [@rarebinary](https://github.com/rarebinary)

Built with ONNX Runtime, OpenCV, scrcpy, adbutils, Flask, discord.py, Nuitka, and EasyOCR.
