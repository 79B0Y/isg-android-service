#!/usr/bin/env python3
"""
Cleanup script to remove old/duplicate android_tv_box button entities from HA registry
and restart Home Assistant to apply changes.

Removes patterns:
- button.android_tv_box_clear_isg_cache*
- button.android_tv_box_isg_health_check*
- button.android_tv_box_navigate_*

Backs up the registry file before modification.
"""

import json
import os
import re
import shutil
import time
import subprocess

HA_CONFIG_DIR = "/home/bo/.homeassistant"
REG_PATH = os.path.join(HA_CONFIG_DIR, ".storage", "core.entity_registry")

PATTERNS = [
    re.compile(r"^button\.android_tv_box_clear_isg_cache(\b|_).*"),
    re.compile(r"^button\.android_tv_box_isg_health_check(\b|_).*"),
    re.compile(r"^button\.android_tv_box_navigate_.*"),
]


def stop_ha():
    subprocess.run(["pkill", "-f", "homeassistant"], check=False)
    subprocess.run(["pkill", "-f", "hass"], check=False)
    time.sleep(2)


def start_ha():
    with open("/tmp/ha_startup.log", "w") as f:
        subprocess.Popen([
            "/bin/bash", "-c",
            f"source /home/bo/.ha-core/bin/activate && hass -c {HA_CONFIG_DIR}"
        ], stdout=f, stderr=subprocess.STDOUT)


def main() -> int:
    print("🧹 Cleaning old android_tv_box button entities...")
    if not os.path.exists(REG_PATH):
        print("Registry not found:", REG_PATH)
        return 1

    stop_ha()

    # Backup
    backup = REG_PATH + ".bak"
    shutil.copy2(REG_PATH, backup)
    print("Backup created:", backup)

    with open(REG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    entities = data.get("data", {}).get("entities", [])
    kept = []
    removed = []
    for e in entities:
        eid = e.get("entity_id", "")
        if any(p.match(eid) for p in PATTERNS):
            removed.append(eid)
        else:
            kept.append(e)

    if removed:
        data["data"]["entities"] = kept
        with open(REG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Removed entities:")
        for r in removed:
            print(" -", r)
    else:
        print("No matching old entities found.")

    start_ha()
    print("✅ Home Assistant starting. Review /tmp/ha_startup.log if needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

