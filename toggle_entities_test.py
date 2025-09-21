#!/usr/bin/env python3
"""
Toggle test for android_tv_box entities via Home Assistant REST API.

Usage:
  HA_TOKEN=your_long_lived_token \
  HA_BASE_URL=http://localhost:8123 \
  python3 toggle_entities_test.py [--entities e1 e2 ...] [--max-wait 15] [--include-power]

What it does:
- Finds the config entry for domain 'android_tv_box' in HA storage.
- Reads entity ids from the entity registry for that entry (or uses --entities).
- Calls HA REST API to toggle each switch on then off, verifying state with retry/backoff.
- Validates key attributes for each entity type (adb_connection, power, wifi).

Notes:
- Requires Home Assistant running and a long-lived token (Profile > Security).
- By default, excludes power switch from auto-discovery for safety; use --include-power to include.
"""

import argparse
import json
import os
import sys
import time
import urllib.request

HA_CONFIG_DIR = "/home/bo/.homeassistant"
ENTITY_REG = os.path.join(HA_CONFIG_DIR, ".storage", "core.entity_registry")
CONFIG_ENTRIES = os.path.join(HA_CONFIG_DIR, ".storage", "core.config_entries")


def read_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_android_tv_box_entry_id() -> str | None:
    data = read_json(CONFIG_ENTRIES)
    if not data:
        return None
    for e in data.get("data", {}).get("entries", []):
        if e.get("domain") == "android_tv_box":
            return e.get("entry_id")
    return None


def get_entities_for_entry(entry_id: str, include_power: bool = False) -> list[str]:
    data = read_json(ENTITY_REG)
    if not data:
        return []
    out: list[str] = []
    for e in data.get("data", {}).get("entities", []):
        if e.get("config_entry_id") == entry_id and e.get("platform") == "switch":
            ent_id = e.get("entity_id")
            if not include_power and ent_id.endswith("_power"):
                # Avoid turning devices on/off by default
                continue
            out.append(ent_id)
    return sorted(out)


def api_request(method: str, path: str, body: dict | None = None):
    base_url = os.environ.get("HA_BASE_URL", "http://localhost:8123")
    token = os.environ.get("HA_TOKEN")
    if not token:
        print("❌ Missing HA_TOKEN env var (long-lived access token). Aborting.")
        sys.exit(2)
    url = base_url.rstrip("/") + path
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8")) if resp.length else None


def get_state(entity_id: str) -> str | None:
    try:
        js = api_request("GET", f"/api/states/{entity_id}")
        return js.get("state") if isinstance(js, dict) else None
    except Exception:
        return None


def call_service(domain: str, service: str, entity_id: str):
    return api_request("POST", f"/api/services/{domain}/{service}", {"entity_id": entity_id})


def validate_attributes(entity_id: str) -> bool:
    try:
        state = api_request("GET", f"/api/states/{entity_id}")
    except Exception:
        print(f"⚠️  Failed to fetch state for attribute validation: {entity_id}")
        return False
    if not isinstance(state, dict):
        return False
    attrs = state.get("attributes", {})
    ok = True
    if entity_id.endswith("_adb_connection"):
        # Expected diagnostics attributes
        for key in ["error_count", "host", "port"]:
            if key not in attrs:
                print(f"⚠️  Missing attribute '{key}' on {entity_id}")
                ok = False
    elif entity_id.endswith("_power"):
        # Expected power attributes
        if attrs.get("power_state") not in {"on", "off", "standby", "unknown"}:
            print(f"⚠️  Unexpected power_state on {entity_id}: {attrs.get('power_state')}")
            ok = False
        if not isinstance(attrs.get("screen_on"), (bool, type(None))):
            print(f"⚠️  screen_on not boolean on {entity_id}")
            ok = False
    elif entity_id.endswith("_wifi"):
        # Expected wifi attributes
        for key in ["wifi_enabled", "wifi_connected"]:
            if not isinstance(attrs.get(key), (bool, type(None))):
                print(f"⚠️  {key} not boolean on {entity_id}")
                ok = False
    return ok


def toggle_and_verify(entity_id: str, max_wait: float = 15.0) -> bool:
    print(f"▶️  Testing {entity_id}")
    # Turn on
    call_service("switch", "turn_on", entity_id)
    # retry with exponential backoff
    t, step = 0.0, 0.25
    while t < max_wait:
        st = get_state(entity_id)
        if st == "on":
            break
        time.sleep(step)
        t += step
        step = min(step * 1.5, 2.0)
    if st != "on":
        print(f"❌ {entity_id} did not turn on (state={get_state(entity_id)})")
        return False
    # Turn off
    call_service("switch", "turn_off", entity_id)
    t, step = 0.0, 0.25
    while t < max_wait:
        st = get_state(entity_id)
        if st == "off":
            break
        time.sleep(step)
        t += step
        step = min(step * 1.5, 2.0)
    if st != "off":
        print(f"❌ {entity_id} did not turn off (state={get_state(entity_id)})")
        return False
    attr_ok = validate_attributes(entity_id)
    if not attr_ok:
        print(f"⚠️  Attribute validation had warnings for {entity_id}")
    print(f"✅ {entity_id} toggled on/off successfully")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Toggle android_tv_box switch entities and verify state")
    parser.add_argument("--entities", nargs="*", help="Explicit list of entity_ids to test (overrides discovery)")
    parser.add_argument("--max-wait", type=float, default=15.0, help="Max seconds to wait for state changes")
    parser.add_argument("--include-power", action="store_true", help="Include power switch when discovering entities")
    args = parser.parse_args()

    entry_id = get_android_tv_box_entry_id()
    if not entry_id:
        print("❌ No android_tv_box config entry found")
        return 1
    entities = args.entities if args.entities else get_entities_for_entry(entry_id, include_power=args.include_power)
    if not entities:
        print("❌ No switch entities found for android_tv_box entry")
        return 1
    print("Entities:")
    for e in entities:
        print(f" - {e}")
    ok = True
    for e in entities:
        ok = toggle_and_verify(e, max_wait=args.max_wait) and ok
    print("🎉 All toggles passed" if ok else "⚠️ Some toggles failed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
