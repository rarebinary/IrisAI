# Getting Started with IrisAI

## Quick Start (5 minutes)

### Prerequisites
- macOS (Apple Silicon or Intel)
- Python 3.11 or newer
- An Android device or emulator with Brawl Stars installed
- USB Debugging enabled on your Android device

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url> IrisAI
   cd IrisAI
   ```

2. **Run the installer**
   ```bash
   python install.py
   ```
   This will:
   - Detect your GPU and install the right dependencies
   - Download ONNX models
   - Check for ADB
   - Create a `.env` file for your tokens

3. **Connect your device**
   - Enable USB Debugging on your Android device (Settings → Developer Options)
   - Connect via USB or WiFi
   - Verify: `adb devices` should list your device

4. **Configure**
   - Edit `cfg/general_config.toml` or use the Web UI (launched automatically)
   - Set your Brawl Stars player tag
   - Configure Discord/Telegram webhooks (optional)

5. **Run**
   ```bash
   python main.py
   ```
   Or double-click `run.command`

### First Launch
- The Web UI opens at `http://127.0.0.1:5185`
- Add brawlers to the queue using the Web UI
- Click "Start" to begin botting

### Quick Troubleshooting
| Problem | Solution |
|---------|----------|
| `adb: command not found` | Install ADB: `brew install android-platform-tools` |
| No device detected | Check USB Debugging, try `adb kill-server && adb start-server` |
| Models not downloading | Run `python install.py` again, check internet connection |
| Web UI not opening | Check the terminal for the port number (usually 5185) |

## Next Steps
- Read [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Read [CONFIGURATION.md](docs/CONFIGURATION.md) for all settings
- Read [PLAYSTYLE_GUIDE.md](docs/PLAYSTYLE_SYSTEM.md) for custom playstyles
