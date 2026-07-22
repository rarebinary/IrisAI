# Codebase Audit

## Scope

This audit covers IrisAI's macOS-native ADB/scrcpy control, Flask Web UI, configuration safety, queue handling, state detection, match-history persistence, and distribution readiness. The supported product is intentionally Mac-only and routes inference through CoreML with a CPU fallback.

## Bugs Fixed In This Pass

| Area | File | Fix |
|------|------|-----|
| Web UI auth fallback | `webui/services.py` | Imported the `network` module used by `check_user_exists()` so legacy API-key validation no longer raises `NameError`. |
| Config defaults | `config_loader.py` | Added the missing `brawl_stars_package` default so a missing TOML key still starts the real package name. |
| Queue import/startup | `utils.py` | Hardened `clean_queue()` against malformed queue entries, missing `wins`/`trophies`/`push_until`, and non-dict JSON items. |
| Match history | `trophy_observer.py` | Initialized the append cursor to the loaded CSV length so existing history is not appended again after the next match. |
| State detection | `state_finder.py` | Guarded template matching against empty crops and templates larger than their region, preventing OpenCV assertion crashes. |
| OCR brawler selection | `lobby_automation.py` | Missing aliases in `cfg/names.json` now fall back safely instead of raising `KeyError`. |
| Event popup clicks | `stage_manager.py` | Fixed Nano Noodles click offsets on non-1920x1080 resolutions by avoiding double scaling. |
| Template loading | `stage_manager.py` | Missing popup template now raises a clear `FileNotFoundError` instead of crashing on `image.shape`. |
| Runtime data | `runtime_paths.py`, `utils.py`, `trophy_observer.py`, `terminal_ui.py`, `play.py`, `state_finder.py` | Queue state, match history, logs, and debug frames now go to `.iris_runtime/` by default, with legacy read fallback. |
| Health checks | `health.py`, `webui/app.py`, `webui/services.py`, `static/js/app.js` | Added a health payload and dashboard summary for config, models, runtime storage, dependencies, and ADB. |
| Installer safety | `install.py` | Added `--dry-run` and post-install health reporting. |
| Regression coverage | `tests/test_core_safety.py` | Added unit tests for queue cleanup, template-region guards, match-history append behavior, and health report shape. |

## Remaining Risks

| Risk | Impact | Recommended Next Step |
|------|--------|-----------------------|
| `cv2` and `av` can load different FFmpeg dylibs on macOS | Native crashes outside Python exception handling | Pin compatible OpenCV/PyAV wheels per platform and add an installer check that warns when duplicate `libavdevice` classes are detected. |
| Several direct TOML lookups remain in `play.py`, `state_finder.py`, and utility code | Partial config files can still crash at import/startup | Continue migrating hot paths to `get_config()` and provide a config validation command. |
| Remote brawler metadata can become unavailable | Queue enrichment may lose fresh names or icons | Keep all remote calls behind `network.py` and use the tracked local catalog when requests fail. |
| Models and EasyOCR assets are large and platform-sensitive | Clone/install size and first-run failure rate stay high | Keep ONNX/EasyOCR out of git, download via `models/manifest.json`, and verify SHA256 before use. |
| Limited automated tests cover only core safety helpers | Runtime regressions can still appear with a real emulator | Extend tests with Web UI route tests and emulator-backed smoke tests. |
| Real-emulator behavior has limited automated coverage | UI changes in Brawl Stars can still break state recognition | Keep emulator-backed smoke recordings and add regression templates from real screenshots. |
| Diagnostic captures can grow during long runs | Runtime storage can fill the disk | Iris now verifies the state before no-player captures and retains at most 100 diagnostics or 500 MB. |

## Stability Improvements

1. Extend `health.py` with value-range checks for TOML numbers and coordinates.
2. Add an emulator-backed startup health check for scrcpy frame freshness and package name detection.
3. Add backoff limits to brawler selection retry loops so a bad OCR/alias state cannot spin through the queue indefinitely.
4. Add Web UI route tests for `/api/bootstrap`, `/api/health`, queue import, and settings updates.
5. For packaged builds, set `IRIS_RUNTIME_DIR` to a user data directory outside the app bundle.

## Repository Hygiene

- Runtime queue data, match history, logs, screenshots, and clips live under
  `.iris_runtime/` and are excluded from Git.
- Local agent skills, generated code graphs, editor state, and session notes are
  excluded from the product repository.
- The unused icon downloader and duplicate `brawler_icons2` catalog were
  removed; the normalized primary catalog covers every configured brawler.
- Diagnostic retention never touches `.iris_runtime/training/`; captured
  training datasets remain under explicit user control.

## Distribution Improvements

1. Move packaging metadata to `pyproject.toml` and keep `setup.py` minimal or remove it once entry points are migrated.
2. Make `python install.py` the single supported first-run path: platform detection, dependency profile, ADB check, model download, `.env` creation, and config validation.
3. Keep two inference profiles only: CoreML-first for Apple Silicon and CPU for compatibility/debugging.
4. Add a macOS `.app` build profile that bundles the correct Python, scrcpy server, models manifest, and icons while storing mutable files outside the app bundle.
5. Add macOS CI jobs for `compileall`, unit tests, packaging smoke tests, and `python install.py --dry-run`.
