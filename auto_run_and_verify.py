#!/usr/bin/env python3
"""
Fully automate starting Home Assistant with hass and verifying that the
android_tv_box integration exposes entities.

Checks:
- Start HA via: source /home/bo/.ha-core/bin/activate && hass -c <config>
- Read HA storage to find config_entry_id for domain 'android_tv_box'
- Wait until at least one entity is registered for that config entry
"""

import json
import os
import sys
import time
import subprocess
from typing import Optional

HA_CONFIG_DIR = "/home/bo/.homeassistant"
HA_LOG = os.path.join(HA_CONFIG_DIR, "home-assistant.log")
ENTITY_REG = os.path.join(HA_CONFIG_DIR, ".storage", "core.entity_registry")
CONFIG_ENTRIES = os.path.join(HA_CONFIG_DIR, ".storage", "core.config_entries")


def stop_ha() -> None:
    subprocess.run(["pkill", "-f", "homeassistant"], check=False)
    subprocess.run(["pkill", "-f", "hass"], check=False)
    time.sleep(3)


def clear_logs() -> None:
    try:
        with open(HA_LOG, "w") as f:
            f.write("")
    except FileNotFoundError:
        os.makedirs(HA_CONFIG_DIR, exist_ok=True)


def start_ha_background() -> None:
    os.makedirs("/tmp", exist_ok=True)
    with open("/tmp/ha_startup.log", "w") as f:
        subprocess.Popen(
            [
                "/bin/bash",
                "-c",
                f"source /home/bo/.ha-core/bin/activate && hass -c {HA_CONFIG_DIR}",
            ],
            stdout=f,
            stderr=subprocess.STDOUT,
        )


def read_json(path: str) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def get_entry_id_for_domain(domain: str) -> Optional[str]:
    data = read_json(CONFIG_ENTRIES)
    if not data or "data" not in data:
        return None
    for entry in data.get("data", {}).get("entries", []):
        if entry.get("domain") == domain:
            return entry.get("entry_id")
    return None


def has_entities_for_entry(entry_id: str) -> bool:
    data = read_json(ENTITY_REG)
    if not data or "data" not in data:
        return False
    entities = data.get("data", {}).get("entities", [])
    for e in entities:
        if e.get("config_entry_id") == entry_id and e.get("disabled_by") is None:
            return True
    return False


def main() -> int:
    print("🧪 Auto run and verify integration")
    print("1) Stopping any running HA...")
    stop_ha()

    print("2) Clearing logs...")
    clear_logs()

    print("3) Starting HA with hass...")
    start_ha_background()

    print("4) Locating integration config entry...")
    # Poll for entry id to exist (HA may rewrite storage on boot)
    entry_id = None
    for _ in range(60):
        entry_id = get_entry_id_for_domain("android_tv_box")
        if entry_id:
            break
        time.sleep(1)
    if not entry_id:
        print("❌ No config entry found for domain 'android_tv_box'")
        return 1
    print(f"✅ Found config entry (entry_id={entry_id})")

    print("5) Verifying entities are registered...")
    # Wait briefly for entity registry to settle
    for _ in range(30):
        if has_entities_for_entry(entry_id):
            print("✅ Entities detected in registry for this integration")
            print("🎉 All checks passed")
            return 0
        time.sleep(1)

    print("❌ No active entities found for this integration")
    print(f"ℹ️  Check {HA_LOG} and /tmp/ha_startup.log for details")
    return 1


if __name__ == "__main__":
    sys.exit(main())
