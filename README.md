# Iris

**See the grind. Automate it.**

Iris is a **local-first automation assistant** for Brawl Stars. It runs on your PC, connects to any Android emulator via ADB, and uses computer vision to play matches — farming trophies, gems, battle pass progress, and brawler mastery while you're AFK.

## What makes it different

- 👁️ **Pure computer vision** — YOLO/ONNX models run locally, zero cloud dependency
- 🤖 **Human-like input** — ADB touch/key events with jitter, delays, imperfect paths
- 🔒 **No injection, no modification** — reads pixels, sends taps, never touches game memory
- 📦 **Multi-account fleet** — orchestrate dozens of emulators/accounts from one dashboard
- 🌐 **Local web UI + Discord bot** — monitor, schedule, and control from anywhere
- ♻️ **Self-healing** — auto-reconnect, crash recovery, model fallback, config validation
- 📦 **One-command install** — `python install.py` detects GPU, pulls models, configures ADB

## Stack

Python · OpenCV · ONNX Runtime · Flask · discord.py · ADB (adbutils) · Nuitka (standalone builds)

## Platform

Windows · macOS (Apple Silicon & Intel) · Linux (experimental)

## Quick Start

```bash
# 1. Clone
git clone https://github.com/rarebinary/IrisAI.git
cd IrisAI

# 2. Install (auto-detects GPU, downloads models, verifies ADB)
python install.py

# 3. Configure secrets
cp .env.example .env
# edit .env with your Discord/Telegram/API tokens

# 4. Run
./run.command          # macOS double-clickable
# or
python main.py
```

Open the Web UI at `http://localhost:<port>` (shown in terminal).

## Commands

```bash
iris self-update       # git pull + pip install -e . + model update
iris update-models     # re-download ONNX models only
python build_nuitka.py # build standalone .app (macOS)
```

## Configuration

All settings via `.env` (preferred) or `cfg/*.toml`. See [CONFIG_REFERENCE.md](CONFIG_REFERENCE.md).

| Variable | Description |
|----------|-------------|
| `IRIS_DISCORD_BOT_TOKEN` | Discord bot token for slash commands |
| `IRIS_DISCORD_USER_ID` | Your Discord user ID (authorized) |
| `IRIS_DISCORD_GUILD_ID` | Guild/server ID for commands |
| `IRIS_TELEGRAM_BOT_TOKEN` | Telegram bot token (optional) |
| `IRIS_TELEGRAM_CHAT_ID` | Telegram chat ID for notifications |
| `IRIS_API_KEY` | Cloud API key (optional) |
| `IRIS_API_BASE_URL` | API base URL (optional) |

## Documentation

- [Getting Started](GETTING_STARTED.md) — 5-minute first launch guide
- [Troubleshooting](TROUBLESHOOTING.md) — Common errors & fixes
- [Config Reference](CONFIG_REFERENCE.md) — All TOML/env options explained

## Disclaimer

Iris is an automation assistant, not a cheat. It does not modify game files, inject code, or bypass server-side checks. Use responsibly. Respect Supercell's Terms of Service.

## License

MIT License — see [LICENSE](LICENSE).