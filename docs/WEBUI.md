# Web UI

**Base directory:** `webui/`  
**Tech stack:** Flask, Jinja2, vanilla JS (app.js), vanilla CSS (tailwind.css)

## File Structure

```
webui/
├── __init__.py     # Blueprint registration
├── app.py          # Flask routes & app factory
├── runtime.py      # RuntimeManager (thread lifecycle)
└── services.py     # WebDataService (data layer)
```

## app.py — Flask Application

### create_app()
WSGI factory function. Creates Flask app, registers blueprints, configures logging.

### Routes

| Method | Route | Handler | Description |
|--------|-------|---------|-------------|
| GET | `/` | — | Serve index.html |
| GET | `/api/settings` | WebDataService | All settings sections |
| GET | `/api/settings/<section>` | WebDataService | Single setting section |
| PUT | `/api/settings/<section>` | WebDataService | Update single section |
| POST | `/api/settings/<section>/reset` | WebDataService | Reset section to defaults |
| GET | `/api/queue` | WebDataService | Get queue |
| POST | `/api/queue` | WebDataService | Add/update queue item |
| PUT | `/api/queue/<brawler_name>` | WebDataService | Update specific brawler |
| POST | `/api/queue/import` | WebDataService | Import queue from JSON |
| POST | `/api/queue/reorder` | WebDataService | Reorder queue |
| POST | `/api/queue/push-all-to-target` | WebDataService | Auto-fill queue from API |
| DELETE | `/api/queue/<brawler_name>` | WebDataService | Remove queue item |
| DELETE | `/api/queue` | WebDataService | Clear all queue |
| GET | `/api/playstyles` | WebDataService | List playstyles |
| PUT | `/api/playstyles/active` | WebDataService | Activate playstyle |
| DELETE | `/api/playstyles/<filename>` | WebDataService | Delete playstyle |
| POST | `/api/playstyles/import` | WebDataService | Import .pyla file |
| GET | `/api/runtime/status` | RuntimeManager | Get bot status |
| POST | `/api/runtime/start` | RuntimeManager | Start bot |
| POST | `/api/runtime/pause` | RuntimeManager | Pause bot |
| POST | `/api/runtime/stop` | RuntimeManager | Stop bot |
| GET | `/api/player-info` | WebDataService | Player info from API |
| GET | `/api/history` | WebDataService | Match history |
| GET | `/api/bootstrap` | WebDataService | Initial load data (all state) |
| GET | `/api/login/validate` | WebDataService | Validate API key |
| GET | `/api/assets/brawlers/<name>` | — | Brawler icon asset |
| GET | `/api/assets/support/<filename>` | — | Support image |

### Request Suppression

`_Suppress*` classes prevent the Discord bot thread from receiving certain polling requests (asset loading, queue polling, runtime status, history). These are Flask `before_request` hooks.

## runtime.py — Runtime Manager

### RuntimeControl
Thread-safe wrapper for shared bot state using `threading.Event`:
- `request_pause()` / `resume()` / `request_stop()` — event setters/clearers
- `should_stop()` / `should_pause()` — event checkers (pause defers to stop)
- `mark_running()` / `mark_paused()` — state callbacks to RuntimeManager
- Internal events: `_stop_event`, `_pause_requested`

### RuntimeManager
Manages bot lifecycle with a worker thread:
- `start()` → if paused: resume. If idle: launch worker thread calling `pyla_main()` (with auth + queue checks)
- `pause()` → running → pausing (already paused is OK)
- `stop()` → handles idle (join thread), paused (join thread), running (set stop event)
- `get_status()` → returns state, is_running, last_error. Auto-idles if thread died.
- `_run_worker()` → wraps `pyla_main()` with try/except, handles `SystemExit` and generic errors

### States
```
idle → running → pausing → paused → running ...
                → stopping → idle
                → error → idle
```

Note: Stop/pause signals are only honored when the main thread's state is `"lobby"` (to avoid interrupting active matches).

## services.py — WebDataService

Data access layer for the web UI.

### Queue Management
- CRUD operations, reorder, import/export CSV
- Auto-sync saved queue file
- `sorted_play_order_enabled()` — toggle for auto-sort by trophies
- `load_startup_queue_if_enabled()` — restore queue from file on boot

### Settings Management
Schema-based serialization for 6 config sections:
- `general`, `bot`, `lobby`, `buttons`, `webhook`, `debug`
- Each section has typed fields with defaults
- `serialize()` / `deserialize()` for JSON ↔ TOML conversion
- `reset_settings()` per section

### Playstyle Management
- List playstyles from `playstyles/` directory
- Activate playstyle (writes to `bot_config.toml`)
- Delete playstyle (removes file)
- Import playstyle from uploaded `.pyla` file

### Match History
- Load from `cfg/match_history.csv`
- Aggregate stats (wins/losses per brawler, win rates)
- Build response payload for charts

### Player Info
- Fetch from Brawlify API / BS API
- Cache player data
- Validate early access login

### Bootstrap
`get_bootstrap_payload()` — returns all data needed for initial page load:
- All settings
- Queue list
- Playstyles list
- Player info
- Brawler catalog
- Runtime status

## Frontend

### templates/index.html
Single-page application with sections:
- Dashboard / Status
- Queue management (table with drag reorder)
- Settings (6 config sections with forms)
- Playstyles (grid of available scripts)
- Match history (table + charts)
- Bot control (start/pause/stop buttons)

### static/js/app.js
Vanilla JavaScript:
- Fetch-based API calls
- DOM manipulation for all views
- Chart rendering (Chart.js via CDN)
- Real-time status polling
- Queue item CRUD
- Playstyle import/upload

### static/css/tailwind.css
Pre-built Tailwind CSS (compiled). Custom styles for the dashboard layout.

## Error Handling
- `KeyError`, `FileNotFoundError`, `ValueError` → returns 400
- All other exceptions → returns 500 with error details

## Running the Web UI

The Flask server is started from `if __name__ == "__main__"` in `main.py`:
```python
port = find_open_port(start_port=5185)  # tries up to 50 ports
app = create_app(pyla_main, start_discord_bot=True)
app.run(host='127.0.0.1', port=port, debug=False)
```

The browser is opened automatically after 1.5s delay via `open_browser_later()` in a daemon thread.
