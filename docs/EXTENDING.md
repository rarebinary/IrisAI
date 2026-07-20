# Extending IrisAI

## Adding a New Brawler

1. **Brawler data:** Add entry to `cfg/brawlers_info.json` with stats
2. **Aliases:** Add OCR aliases to `cfg/names.json`
3. **Icon:** Add icon PNG to `api/assets/brawler_icons/`
4. **Brawler info:** Run `update_brawlers_info()` or manually update JSON

## Adding a New Playstyle

1. Copy `playstyles/skeleton.py` as reference
2. Create `playstyles/my_style.pyla`
3. Add JSON metadata on line 1: `# {"name": "...", "description": "...", "brawlers": [...], "gamemodes": [...]}`
4. Write Python code that computes `movement = (x, y)`
5. Set `current_playstyle = "my_style"` in `bot_config.toml`
6. Or activate via Web UI → Playstyles

## Adding a New State

1. **Template image:** Add `.png` to `images/states/`
2. **Detection:** Add function in `state_finder.py` (e.g., `is_in_new_state()`)
3. **State handler:** Add method in `stage_manager.py`
4. **State mapping:** Add entry in `StageManager.states` dict
5. **Config region:** Add detection region in `lobby_config.toml` → `template_matching` section
6. **State priority:** Add check in `get_in_game_state()` before the default `"match"` fallthrough

### Example: Adding "Daily Rewards" state
```python
# state_finder.py
def is_in_daily_rewards(image):
    return is_template_in_region(image, "daily_rewards.png", region_config, threshold=0.7)

# get_in_game_state() — add check before default "match"
if is_in_daily_rewards(screenshot):
    return "daily_rewards"

# stage_manager.py — add handler
def collect_daily_rewards(self):
    self.window_controller.click(960, 540)  # click claim button
    time.sleep(1)

# StageManager.states — add mapping
"daily_rewards": self.collect_daily_rewards
```

## Adding a New Web UI Feature

1. **Backend:** Add route in `webui/app.py` and handler in `webui/services.py`
2. **Settings schema:** Add section and fields to `WebDataService.settings_schema`
3. **Frontend:** Add HTML section in `templates/index.html` and JS in `static/js/app.js`

## Adding a New Discord Command

```python
# discord_bot.py — inside DiscordBot.register_commands()
@self.tree.command(name="my_command", description="Does something")
async def my_command(self, interaction: discord.Interaction):
    self.require_authorized_user(interaction)
    # ... command logic
    await interaction.response.send_message("Done!")
```

## Modifying Detection

- **Model replacement:** Replace ONNX files in `models/` (keep same class names)
- **Confidence tuning:** Adjust `detection_confidence` in `bot_config.toml`
- **New model classes:** Add class names to `wall_model_classes` in `detect.py`

## Adding a New Timer

Two timer systems:
1. **TimeManagement** (wall-clock based): For periodic checks like state detection, idle detection.
2. **timer_frequencies** (frame-count based in Play): For per-frame interval checks like ability readiness, wall detection.

### TimeManagement timer
```python
# time_management.py — add to TimeManagement
def custom_check(self):
    return self.check_time('custom')

# time_tresholds.toml — add threshold
custom = 10

# main.py — call in main loop manage_time_tasks()
if self.time_management.custom_check():
    # do something
```

### Frame-count timer (in Play)
```python
# play.py __init__ — add timer
self.custom_frequency = load_toml_as_dict("time_tresholds").get("timer_frequencies", {}).get("custom", 10)
self.custom_timer = 0

# play.py main() — check in loop
self.custom_timer += 1
if self.custom_timer >= self.custom_frequency:
    self.custom_timer = 0
    # do something every N frames

# time_tresholds.toml
[timer_frequencies]
custom = 10
```

## Adding New Configuration

1. Add TOML file to `cfg/` or extend existing one
2. Add schema entry in `WebDataService.settings_schema` for Web UI
3. Load via `load_toml_as_dict('your_config')` in utils.py

## Early Access / Plugin System

The project supports an optional `early_access` plugin module:

```python
try:
    from early_access import EarlyAccessPlugin
    plugin = EarlyAccessPlugin()
except ImportError:
    plugin = None
```

The plugin can extend:
- API features (advanced stats, cloud sync)
- Discord commands (`register_early_access_commands()`)
- Advanced visuals in debug view
- Premium playstyles
- Additional detection capabilities

## API (api/api.py)

Provides endpoints for uploading match results and fetching player data. Extend for custom analytics:
- POST `/api/results` — receive match results
- POST `/api/matches` — batch match submission
- GET `/get_brawler_list` — fetch all brawlers
- GET `/get_brawler_info` — fetch brawler details
- GET `/check_version` — version check
- `/check` endpoint — health check
- Player info retrieval from Brawlify API
- Brawler catalog and icon download
