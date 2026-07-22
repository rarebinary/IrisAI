# Discord Bot

**File:** `discord_bot.py`  
**Class:** `DiscordBot`

## Overview

Provides remote control of the bot via Discord slash commands. Runs in its own thread alongside the main loop.

## Authentication & Authorization

- Restricted to a specific guild (`discord_guild_id` in `webhook_config.toml`) for command tree sync
- Restricted to a specific user (`discord_id` in `webhook_config.toml`)
- All commands check authorization via `require_authorized_user()` decorator (checks both user ID and guild membership)
- Sync behavior: prefers guild-specific sync (instant), falls back to global sync (slower propagation)

## Commands

| Command | Description |
|---------|-------------|
| `/screenshot` | Takes a screenshot and uploads it |
| `/stop` | Stops the bot |
| `/pause` | Pauses the bot |
| `/start` | Starts/resumes the bot |
| `/status` | Shows current bot status |
| `/restart_brawl_stars` | Restarts the game app |
| `/view_queue` | Shows the current brawler queue with trophies and targets |
| `/help` | Shows the available commands |

## Early Access Commands

Additional commands from the optional `early_access` plugin module (loaded via try/except):

- Registered via `register_early_access_commands()`
- Extended analytics and control features

## Lifecycle

1. Bot token and IDs loaded from `cfg/webhook_config.toml` (reads `discord_guild_id`, `discord_id`, `bot_token`)
2. Discord client initialized with `discord.Intents.default()` + `message_content`, `messages`, `guilds` intents
3. Commands registered via `discord.app_commands.CommandTree`
4. `set_window_controller(wc)` called when window controller is available
5. Bot runs in a thread — `run_bot()` uses `bot.start()` with async event loop (only runs once)
6. `sync_commands()` syncs command tree to guild (preferred) or globally
7. Commands use authorization decorator `require_authorized_user()` checking both user_id and guild

## Integration Points

- Receives the active `WindowController` instance via `set_window_controller()` for screenshots
- Receives `RuntimeManager` and `WebDataService` references at init
- Commands interact with the same `RuntimeControl` shared state used by Flask
- `_extract_discord_id()` utility parses Discord IDs from strings
- Early access commands registered via `register_early_access_commands()` if available
