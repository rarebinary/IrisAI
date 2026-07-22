# Troubleshooting Guide

## Common Issues

### ADB Not Found
**Error:** `adb: command not found` or `No ADB devices`

**Solution:**
```bash
# macOS
brew install android-platform-tools

# Then verify
adb devices
```

### No Device Detected
1. Enable USB Debugging on your Android device
2. Check connection: `adb devices`
3. If using an emulator, note the port number and set it in config
4. Try: `adb kill-server && adb start-server && adb devices`

### Model Files Missing
**Error:** `ONNX model not found` or `Failed to load ONNX model`

**Solution:**
- Run `python install.py` to download models
- Or manually download from the project's GitHub Releases
- Place `.onnx` files in the `models/` directory

### EasyOCR Fails to Initialize
**Error:** `EasyOCR initialization failed`

**Solutions:**
1. Check internet connection (models need to download on first use)
2. SSL errors: see Discord support thread
3. Manual: download `craft_mlt_25k.pth` and `english_g2.pth` to `models/easyocr/`

### Port Already in Use
**Error:** `Address already in use` or Web UI won't start

**Solution:**
- The bot tries ports starting at 5185
- Check what's using the port: `lsof -i :5185`
- Kill the process or wait for the bot to find a free port

### Brawl Stars Not Starting
**Error:** Bot can't find or start Brawl Stars

**Solutions:**
1. Make sure Brawl Stars is installed on your device
2. Check the package name in config: `bs_package_name` in `general_config.toml`
3. The bot auto-detects the package on first successful check

### Low IPS / Performance
**Warning:** `Low iteration rate (< 15 IPS)`

**Solutions:**
1. Reduce `max_ips` in config
2. Set `cpu_or_gpu = "cpu"` to test
3. Close other applications
4. Reduce `ocr_scale_down_factor` (e.g., 0.5)

### Bot Gets Stuck
**Symptoms:** Bot stops moving, same state for minutes

**Solutions:**
1. The auto-unstuck system should trigger after 20 seconds
2. Check debug view for what the bot sees
3. Restart Brawl Stars from the Web UI
4. Check `unstuck_movement_delay` in config

## Getting Help
- Open a report at https://github.com/rarebinary/IrisAI/issues with a `--log` session file
- Search for your error in the Discord support channel
- Report bugs on GitHub Issues
