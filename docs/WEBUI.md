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
| POST | `/api/playstyles/import` | WebDataService | Import .iris file |
| GET | `/api/runtime/status` | RuntimeManager | Get bot status |
| POST | `/api/runtime/start` | RuntimeManager | Start bot |
| POST | `/api/runtime/pause` | RuntimeManager | Pause bot |
| POST | `/api/runtime/stop` | RuntimeManager | Stop bot |
| GET | `/api/player-info` | WebDataService | Player info from API |
| GET | `/api/history` | WebDataService | Match history |
| GET | `/api/bootstrap` | WebDataService | Initial load data (all state) |
| GET | `/api/health` | WebDataService | Health check payload |
| POST | `/api/login/validate` | WebDataService | Validate API key |
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
- `start()` → if paused: resume. If idle: launch worker thread calling `iris_main()` (with auth + queue checks)
- `pause()` → running → pausing (already paused is OK)
- `stop()` → handles idle (join thread), paused (join thread), running (set stop event)
- `get_status()` → returns state, is_running, last_error. Auto-idles if thread died.
- `_run_worker()` → wraps `iris_main()` with try/except, handles `SystemExit` and generic errors

`get_status()` also includes the shared telemetry snapshot. This keeps the Web UI
and terminal dashboard on the same view of the active run instead of making the
browser infer status from raw log lines.

### States
```
idle → running → pausing → paused → running ...
                → stopping → idle
                → error → idle
```

Stop requests are asynchronous and are checked immediately by the main loop.
Pause requests wait for the lobby so Iris does not leave a match half-finished.

## services.py — WebDataService

Data access layer for the web UI.

### Queue Management
- CRUD operations, reorder, import/export CSV
- Auto-sync saved queue file
- `sorted_play_order_enabled()` — toggle for auto-sort by trophies
- `load_startup_queue_if_enabled()` — restore queue from file on boot

### Settings Management
Schema-based serialization for 5 exposed config sections:
- `general`, `bot`, `timers`, `webhook`, `debug`
- Each section has typed fields with defaults
- `serialize()` / `deserialize()` for JSON ↔ TOML conversion
- `reset_settings()` per section
- Queue imports go through the same normalization as runtime startup, so malformed JSON items are ignored instead of crashing the request.

### Playstyle Management
- List playstyles from `playstyles/` directory
- Activate playstyle (writes to `bot_config.toml`)
- Delete playstyle (removes file)
- Import playstyle from uploaded `.iris` file

### Match History
- Load from `.iris_runtime/match_history.csv`, with one-time compatibility for
  the former `cfg/match_history.csv` location
- Aggregate stats (wins/losses per brawler, win rates)
- Build response payload for charts and a cross-brawler `recent_matches` list
  limited to the newest 10 entries
- Return an empty history payload on a fresh install instead of failing bootstrap

Masked webhook credentials are display-only placeholders. The service ignores
those placeholder values during autosave so changing another setting cannot
replace an existing token or URL.

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
- Health check summary

### Health Check

The bootstrap and `/api/health` response include the health summary from
`health.py`. It checks config readability, runtime directory writability, model
presence/hash status, EasyOCR model presence, optional Python dependencies, and
ADB availability. Blocking issues should be fixed before pressing Start;
warnings usually mean an optional feature or packaging dependency needs
attention.

## Frontend

### templates/index.html
Single-page application with sections:
- Runbook dashboard with a status strip, Current Run, Recent Activity, and Last
  10 Matches
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

#### Dashboard behavior

The Dashboard is an operational overview rather than a live debug console:

- **Status strip**: bot status, emulator status, game state, and active
  playstyle.
- **Current Run**: brawler, trophies, win streak, last result, and session
  totals.
- **Recent Activity**: the latest ten readable events. The separate **Debug
  logs** tab exposes their technical details only when needed.
- **Last 10 Matches**: compact result rows with brawler, mode (when known),
  and trophy change. Victory uses the success color; Defeat uses the danger
  color.
- **Session log notice**: when IrisAI starts with `--log` or `--debug`, a green
  notice confirms recording and shows the absolute file path. This makes the
  diagnostic file easy to locate after the session.

The theme control stores the selected `light` or `dark` theme in browser local
storage. Light is the default. Both themes use the CSS tokens defined at the top
of `static/css/tailwind.css`; components must use semantic tokens rather than
hardcoded colors.

Tooltips are rendered as plain text. Match labels from history never pass
through an HTML sink.

The old queue dock is intentionally limited to the Brawlers view so it cannot
compete with the Dashboard's three operational areas.

### static/css/tailwind.css
Project CSS for the application shell and components. The top-level tokens define
surfaces, text, borders, accent, success, danger, and warning for both themes.

## Shared Runtime Telemetry

`runtime_events.py` owns a bounded, thread-safe in-memory telemetry snapshot.
It is updated by `main.py`, `webui/runtime.py`, and `trophy_observer.py` and is
returned in `/api/runtime/status`.

Supported event kinds are `state_changed`, `brawler_selected`, `match_started`,
`match_finished`, `warning`, and `error` (plus `system` for lifecycle messages).
Each event has a short user-facing message and optional technical details. The
store keeps the latest 300 events and ten matches; it is intentionally a live
session view, not a replacement for CSV match history or session log files.
The same snapshot includes a `logging` object with `enabled`, `status`, and
`path`, which drives the Dashboard recording notice.

## Error Handling
- `KeyError`, `FileNotFoundError`, `ValueError` → returns 400
- All other exceptions → returns 500 with error details
- Legacy API-key checks use the shared `network.py` timeout/retry client.

## Running the Web UI

The Flask server is started from `if __name__ == "__main__"` in `main.py`:
```python
port = find_open_port(start_port=5185)  # tries up to 50 ports
app = create_app(iris_main, start_discord_bot=True)
app.run(host='127.0.0.1', port=port, debug=False)
```

The browser is opened automatically after 1.5s delay via `open_browser_later()` in a daemon thread.
