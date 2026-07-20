# Deployment

## Requirements

**Python:** 3.11+ (tested on 3.12)  
**OS:** macOS, Windows, Linux  
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
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. ADB Setup
```bash
# macOS
brew install android-platform-tools

# Windows
# Download from: https://developer.android.com/studio/releases/platform-tools

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

## Build (Nuitka)

The project can be compiled to a standalone executable:

```bash
pip install nuitka
python setup.py build_exe
```

Nuitka compatibility notes:
- `main.py` monkey-patches `inspect.getfile` to prevent crashes
- `debug_view.py` handles `__compiled__` detection
- `utils.py` has frozen/bundled path resolution for `easyocr` models

## Configuration Checks

Before first run:
1. Verify ADB device is connected: `adb devices`
2. Verify Brawl Stars is installed and logged in
3. Configure Discord webhook in `cfg/webhook_config.toml` (optional)
4. Set `run_for_minutes` if you want auto-stop
5. Add brawlers to queue via Web UI

## Project Installation (pip)

```bash
pip install -e .  # development install
# or
python setup.py install
```

## Docker

A Docker setup would require:
- Android emulator (or ADB bridge to host)
- GPU passthrough for CUDA/CoreML (optional)
- X11/VNC for debug view (optional)

No Dockerfile is currently included.
