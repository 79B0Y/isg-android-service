#!/usr/bin/env python3
"""
Purge duplicate suffixed android_tv_box entities from HA entity registry.

Removes entries like *_2, *_3 only if a base entity without suffix exists.

Actions:
- Stop HA, backup registry, delete suffixed duplicates, restart HA.
"""

import json
import os
import re
import shutil
import subprocess
import time

HA_CONFIG_DIR = "/home/bo/.homeassistant"
REG_PATH = os.path.join(HA_CONFIG_DIR, ".storage", "core.entity_registry")

SUFFIX_RE = re.compile(r"^(?P<prefix>(switch|button|media_player)\.android_tv_box_[a-z0-9_]+?)(?:_(?P<num>\d+))$")


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
    print("🧽 Purging suffixed android_tv_box entities where base exists...")
    if not os.path.exists(REG_PATH):
        print("Registry not found:", REG_PATH)
        return 1

    stop_ha()

    # Backup registry
    backup = REG_PATH + ".bak"
    shutil.copy2(REG_PATH, backup)
    print("Backup created:", backup)

    with open(REG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    entities = data.get("data", {}).get("entities", [])
    existing = {e.get("entity_id") for e in entities}

    keep = []
    removed = []
    for e in entities:
        eid = e.get("entity_id", "")
        m = SUFFIX_RE.match(eid)
        if not m:
            keep.append(e)
            continue
        base = m.group("prefix")
        if base in existing:
            # base exists: purge the suffixed duplicate
            removed.append(eid)
        else:
            # base missing: keep the suffixed one
            keep.append(e)

    if removed:
        data["data"]["entities"] = keep
        with open(REG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Removed entities:")
        for r in sorted(removed):
            print(" -", r)
    else:
        print("No suffixed duplicates found.")

    start_ha()
    print("✅ Home Assistant starting. Review /tmp/ha_startup.log if needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
