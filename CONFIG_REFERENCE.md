# Configuration Reference

## File: cfg/general_config.toml

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `cpu_or_gpu` | string | `"auto"` | Compute device: `cpu`, `cuda`, `coreml`, `directml`, `auto` |
| `max_ips` | int/string | `"auto"` | Max iterations per second. `"auto"` = unlimited |
| `trophies_multiplier` | float | `1.0` | Multiply trophy gains/losses |
| `run_for_minutes` | int | `60` | Auto-stop after N minutes. `0` = no limit |
| `emulator_port` | int | `5555` | Android emulator ADB port |
| `player_tag` | string | `""` | Brawl Stars player tag (with #) |
| `play_order` | string | `"in_order"` | Queue order: `in_order`, `lowest_to_highest`, `highest_to_lowest` |

## File: cfg/bot_config.toml

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `current_playstyle` | string | `"default_up.iris"` | Active playstyle script |
| `play_again_on_win` | bool | `true` | Auto-click "Play Again" after victory |
| `minimum_movement_delay` | float | `0.05` | Minimum seconds between movement updates |
| `unstuck_movement_delay` | int | `20` | Seconds before stuck rotation triggers |
| `entity_detection_confidence` | float | `0.5` | YOLO entity detection threshold |
| `wall_detection_confidence` | float | `0.5` | YOLO wall detection threshold |
| `max_losses` | int | `5` | Max losses before switching brawler |
| `max_consecutive_losses` | int | `3` | Max consecutive losses before switching |

## File: cfg/webhook_config.toml

| Key | Type | Description |
|-----|------|-------------|
| `webhook_url` | string | Discord webhook URL for notifications |
| `discord_id` | string | Authorized Discord user ID |
| `discord_bot_token` | string | Discord bot token for slash commands |
| `discord_guild_id` | string | Discord guild ID for command sync |
| `telegram_token` | string | Telegram bot token |
| `telegram_chat_id` | string | Telegram chat ID |
| `ping_when_stuck` | bool | Notify when bot gets stuck |
| `ping_when_target_is_reached` | bool | Notify when brawler reaches target |

## Environment Variables (.env)
All webhook settings can be set via environment variables with `PYLA_` prefix.
See `.env.example` for the full list.
