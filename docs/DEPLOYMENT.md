# Deployment

## Requirements

**Python:** 3.11+ (tested on 3.12)  
**OS:** macOS only (Apple Silicon preferred; Intel supported with CPU inference)
**Device:** Android device or emulator with Brawl Stars installed  

### Python Dependencies

From `requirements.txt`:
```
opencv-python          # Computer vision
numpy                  # Numerical computing
onnxruntime            # ONNX model inference
onnxruntime-silicon    # Apple Silicon acceleration
discord.py             # Discord bot
flask                  # Web UI
toml                   # TOML config parsing
pandas                 # Match history CSV
pyav                   # H.264 video decoding (scrcpy)
adbutils               # Android Debug Bridge
easyocr                # OCR for brawler names
requests               # HTTP/API calls
Pillow                 # Image processing
```

## Installation

### 1. Clone & Setup
```bash
git clone <repo> IrisAI
cd IrisAI
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. ADB Setup
```bash
brew install android-platform-tools

# Verify device
adb devices
```

### 3. Enable USB Debugging on Android
- Settings → Developer Options → USB Debugging → ON
- For WiFi: `adb connect <device_ip>:5555`

### 4. Configure
Edit `cfg/general_config.toml`:
- Set `cpu_or_gpu` to your hardware
- Set `player_tag` to your Brawl Stars tag
- Set `emulator_port` if using an emulator

### 5. Run
```bash
python main.py
```

For troubleshooting, use the detailed terminal mode:

```bash
python main.py --debug
```

To record a shareable diagnostic session without showing technical output in the
terminal, use:

```bash
python main.py --log
```

Normal mode keeps the terminal as a calm dashboard with **SYSTEM**, **CURRENT
RUN**, **LAST MATCHES**, and **RECENT EVENTS**. It does not create a diagnostic
log unless `--log` is provided. `--debug` includes `--log` behavior and also
mirrors technical output to the terminal for live troubleshooting.

While recording, both the terminal Dashboard and Web UI display the absolute log
path. Pressing `Ctrl+C`, closing normally, receiving `SIGTERM`/`SIGHUP`, or
exiting after an exception finalizes the file before the process ends. The
terminal then prints **Session log saved** and the exact file to share.

Each diagnostic log contains environment metadata, captured stdout/stderr, the
exit reason, elapsed time, current-run data, session totals, recent events, and
the latest ten matches. A fallback `atexit` handler closes the file if normal
shutdown code cannot finish; `SIGKILL` and machine power loss cannot be captured.

### Dry Run

Use this before a real install when you want to see what IrisAI would do without installing dependencies or downloading models:

```bash
python install.py --dry-run --no-adb --cpu
```

The dry run prints the dependency plan, checks existing models, skips downloads, and runs the health check.

## Build (Nuitka)

The project can be compiled to a standalone macOS app:

```bash
pip install nuitka
python build_nuitka.py
```

Nuitka compatibility notes:
- `main.py` monkey-patches `inspect.getfile` to prevent crashes
- `debug_view.py` handles `__compiled__` detection
- `utils.py` has frozen/bundled path resolution for `easyocr` models
- macOS builds must include `native/macos_vision_ocr.swift`; Iris compiles this
  helper into the runtime directory on first use. Xcode Command Line Tools are
  recommended. If `swiftc` is unavailable, selection falls back to EasyOCR.

### macOS FFmpeg Wheel Warning

On macOS, importing both `opencv-python` (`cv2`) and `av` can load duplicate FFmpeg/AVFoundation symbols when the installed wheels bundle different FFmpeg versions. A smoke import may print warnings about `AVFFrameReceiver` or `AVFAudioReceiver` being implemented twice. Treat that as a packaging stability risk: pin compatible `opencv-python` and `av` versions per release profile, and validate the environment in `install.py` before telling users the install is healthy.

## Configuration Checks

Before first run:
1. Verify ADB device is connected: `adb devices`
2. Verify Brawl Stars is installed and logged in
3. Configure Discord webhook in `cfg/webhook_config.toml` (optional)
4. Set `run_for_minutes` if you want auto-stop
5. Add brawlers to queue via Web UI

The same checks are also available through `health.py` and the Web UI bootstrap:
- macOS host and native Vision compiler availability
- Runtime data directory writable
- TOML files readable
- Inference mode limited to `auto`, `coreml`, or `cpu`
- ONNX models present and matching manifest hashes when hashes exist
- EasyOCR model files present
- Optional Python modules and ADB availability

## Runtime Data

Generated runtime files are stored under `.iris_runtime/` by default and ignored by Git:
- `latest_brawler_data.json`
- `match_history.csv`
- `logs/iris-session_<date>_<pid>.log` (only with `--log` or `--debug`)
- `debug_frames/`

Set `IRIS_RUNTIME_DIR=/path/to/data` to move those files elsewhere for packaged builds or user-specific installs. IrisAI still reads old legacy files from the project root or `cfg/` when no runtime copy exists, so existing local data is not stranded.

The terminal dashboard's runtime view is in-memory and resets when IrisAI exits;
use the session logs and match-history CSV for persistent diagnostics and records.

## Project Installation (pip)

```bash
pip install -e .  # development install
# or
python setup.py install
```

## Containers

Containers are intentionally unsupported. IrisAI depends on native macOS Vision/CoreML services and direct ADB access, so the supported release format is the macOS `.app` bundle.

## Release Readiness Checklist

Before packaging or pushing a release:
1. Run `python3 -m compileall -q .` with bytecode output disabled or clean generated `__pycache__` afterward.
2. Verify Web UI imports and config payloads without an emulator attached.
3. Run an ADB/scrcpy smoke test on the target macOS architecture.
4. Verify `models/manifest.json` hashes and EasyOCR model presence.
5. Confirm generated runtime files (`latest_brawler_data.json`, logs, debug frames) are not accidentally committed unless intentionally included.
