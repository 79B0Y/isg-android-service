#!/usr/bin/env python3
"""
Toggle test for android_tv_box entities via Home Assistant REST API.

Usage:
  HA_TOKEN=your_long_lived_token \
  HA_BASE_URL=http://localhost:8123 \
  python3 toggle_entities_test.py

What it does:
- Finds the config entry for domain 'android_tv_box' in HA storage.
- Reads entity ids from the entity registry for that entry.
- Calls HA REST API to toggle each switch on then off, verifying state.

Notes:
- Requires Home Assistant running and a long-lived token (Profile > Security).
- Does not alter HA configuration; only uses API calls.
"""

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


def get_entities_for_entry(entry_id: str) -> list[str]:
    data = read_json(ENTITY_REG)
    if not data:
        return []
    out: list[str] = []
    for e in data.get("data", {}).get("entities", []):
        if e.get("config_entry_id") == entry_id and e.get("platform") == "switch":
            out.append(e.get("entity_id"))
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


def toggle_and_verify(entity_id: str) -> bool:
    print(f"▶️  Testing {entity_id}")
    # Turn on
    call_service("switch", "turn_on", entity_id)
    for _ in range(10):
        st = get_state(entity_id)
        if st == "on":
            break
        time.sleep(0.5)
    else:
        print(f"❌ {entity_id} did not turn on (state={get_state(entity_id)})")
        return False
    # Turn off
    call_service("switch", "turn_off", entity_id)
    for _ in range(10):
        st = get_state(entity_id)
        if st == "off":
            break
        time.sleep(0.5)
    else:
        print(f"❌ {entity_id} did not turn off (state={get_state(entity_id)})")
        return False
    print(f"✅ {entity_id} toggled on/off successfully")
    return True


def main() -> int:
    entry_id = get_android_tv_box_entry_id()
    if not entry_id:
        print("❌ No android_tv_box config entry found")
        return 1
    entities = get_entities_for_entry(entry_id)
    if not entities:
        print("❌ No switch entities found for android_tv_box entry")
        return 1
    print("Entities:")
    for e in entities:
        print(f" - {e}")
    ok = True
    for e in entities:
        ok = toggle_and_verify(e) and ok
    print("🎉 All toggles passed" if ok else "⚠️ Some toggles failed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

