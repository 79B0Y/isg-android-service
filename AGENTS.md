# Repository Guidelines

## Project Structure & Module Organization
- Source: `custom_components/android_tv_box/`
  - `__init__.py`: entry setup/unload, platform wiring.
  - `config_flow.py`: UI configuration and validation.
  - `coordinator.py`: data fetch/commands via ADB.
  - `adb_manager.py`: low‑level ADB interactions.
  - `switch.py`: exposed entities (e.g., power/Wi‑Fi switches).
  - `const.py`, `manifest.json`: constants and integration metadata.
  - Assets: `icons/`, `translations/`.
- Docs/scripts at repo root: `README.md`, `README_INSTALLATION.md`, `debug_adb_connection.py`, `test_*.py`.

## Build, Test, and Development Commands
- Start local HA: `source /home/bo/.ha-core/bin/activate && hass -c /home/bo/.homeassistant`
- Auto‑run + verify integration: `python3 auto_run_and_verify.py` (starts HA, waits for config entry to load, checks entity registry)
- Smoke test with log monitor: `python3 restart_and_test.py`
- Config‑flow validation: `python3 test_config_flow.py`
- Coordinator sanity: `python3 test_coordinator_fix.py`
- Debug ADB: `python3 debug_adb_connection.py <host> [port]`
- Install into HA: copy `custom_components/android_tv_box` into your HA `custom_components/` and restart (see `README_INSTALLATION.md`).

## Verification & Toggle Tests
- Auto-verify entities: `python3 auto_run_and_verify.py` (starts hass, confirms config entry + entities)
- Smoke log monitor: `python3 restart_and_test.py` (60s watch for errors)
- Toggle entities via REST: `python3 toggle_entities_test.py [--entities e1 e2 ...] [--include-power]`
  - Requires env: `HA_TOKEN` (long-lived token), optional `HA_BASE_URL` (default `http://localhost:8123`).
  - By default, excludes the power switch; pass `--include-power` to include it.

## Camera & Screenshots
- Entity: `camera.android_tv_box_screen` (captures current screen via ADB)
- Fetch image: `GET /api/camera_proxy/camera.android_tv_box_screen` (requires `HA_TOKEN`)
- Screenshot storage: default `~/.homeassistant/www/screenshots` (served under `/local/screenshots/`)
- Options (Settings → Devices & Services → Integration → Options):
  - `screenshot_dir`: override target folder
  - `screenshot_retain`: keep last N images (default 10)

## Coding Style & Naming Conventions
- Python 3.11+, follow PEP8 (4‑space indents, 100‑120 col soft limit).
- Names: modules `snake_case.py`, classes `CamelCase`, functions/vars `snake_case`, constants `UPPER_SNAKE`.
- Logging: use module‑level `_LOGGER = logging.getLogger(__name__)`; prefer `.debug()` for verbose internals.
- Type hints required in public functions; prefer `from __future__ import annotations`.

## Testing Guidelines
- Prefer fast local scripts in root (`test_*.py`) for iterative checks.
- For HA runtime testing, start Home Assistant and add the integration via UI; verify coordinator logs and entity state updates.
- Add new lightweight tests alongside scripts (e.g., `test_new_feature.py`) mirroring existing patterns.
- Keep tests deterministic; mock ADB where external state would fluctuate.

## Commit & Pull Request Guidelines
- Commits: concise, imperative mood. Example: `fix(coordinator): handle reconnect after 3 failures`.
- Include context in body (why + approach) when non‑trivial.
- PRs must include: clear description, linked issue (if any), steps to reproduce/verify, and screenshots/log snippets when UI or logs change.
- Touching behavior? Note breaking changes in PR description and bump `manifest.json` `version`.

## Security & Configuration Tips
- Do not commit real device IPs, credentials, or HA paths.
- Avoid logging sensitive values; sanitize host/SSID where possible.
- Keep `requirements` minimal; pin only what’s needed in `manifest.json`.
