# IrisAI Documentation

**Version:** 0.0.1 | **Purpose:** macOS Brawl Stars automation bot | **License:** CC BY-NC 4.0

## Overview

IrisAI is a computer-vision-based game automation bot for Brawl Stars. It uses ADB + scrcpy for screen mirroring and touch injection, YOLO ONNX models for real-time object detection, macOS Vision with an EasyOCR fallback for text recognition, and a custom Python scripting system (`.iris` files) for in-game behavior.

## Quick Reference

| File | Purpose |
|------|---------|
| `main.py` | Entry point — orchestrates all systems |
| `play.py` | In-game AI engine (detection + movement) |
| `stage_manager.py` | Menu state machine (lobby, shop, results) |
| `state_finder.py` | Game screen state detection via template matching |
| `window_controller.py` | ADB + scrcpy device control |
| `detect.py` | YOLO ONNX model inference wrapper |
| `lobby_automation.py` | Text-based brawler selection via macOS Vision/EasyOCR |
| `trophy_observer.py` | Trophy/win tracking & match history |
| `runtime_events.py` | Shared current-run telemetry for the terminal and Web UI |
| `time_management.py` | Periodic task scheduler |
| `discord_bot.py` | Discord remote control commands |
| `debug_view.py` | Real-time debug visualization overlay |
| `utils.py` | Shared utilities (config, OCR, helpers) |
| `webui/` | Flask web dashboard (queue, settings, control) |
| `scrcpy/` | Bundled Python scrcpy client |
| `playstyles/` | `.iris` behavior scripts |
| `cfg/` | TOML/JSON configuration files |

## Doc Index

- [ARCHITECTURE.md](ARCHITECTURE.md) — High-level system design & threading model
- [COMPONENTS.md](COMPONENTS.md) — Detailed component breakdown
- [DATA_FLOW.md](DATA_FLOW.md) — Data flows & communication patterns
- [CONFIGURATION.md](CONFIGURATION.md) — Configuration system reference
- [PLAYSTYLE_SYSTEM.md](PLAYSTYLE_SYSTEM.md) — `.iris` script system
- [STATE_MACHINE.md](STATE_MACHINE.md) — Game state machine
- [DETECTION_MODELS.md](DETECTION_MODELS.md) — YOLO models & computer vision
- [DISCORD_BOT.md](DISCORD_BOT.md) — Discord remote control
- [WEBUI.md](WEBUI.md) — Flask web UI
- [DEPLOYMENT.md](DEPLOYMENT.md) — Setup, build, and deployment
- [EXTENDING.md](EXTENDING.md) — How to extend the bot
- [DESIGN.md](DESIGN.md) — Product interface design system
- [PRODUCT.md](PRODUCT.md) — Product audience, purpose, and principles
- [CODEBASE_AUDIT.md](CODEBASE_AUDIT.md) — Latest bug audit, fixes, and stability/distribution recommendations
