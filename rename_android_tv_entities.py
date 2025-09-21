#!/usr/bin/env python3
"""
Rename android_tv_box entities in HA entity registry to remove numeric suffixes
like _2, _3, etc. Safely updates only if the target name is not taken.

Steps:
- Stop HA
- Backup registry
- Rename switch.* and button.* entities matching android_tv_box_*_N
- Start HA

Note: This edits the HA storage directly. Use with care.
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
    print("🔤 Renaming android_tv_box entities (remove numeric suffixes)...")
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

    ents = data.get("data", {}).get("entities", [])
    existing_ids = {e.get("entity_id") for e in ents}

    changed = 0
    for e in ents:
        eid = e.get("entity_id", "")
        m = SUFFIX_RE.match(eid)
        if not m:
            continue
        target = m.group("prefix")
        if target in existing_ids:
            # Skip if target already exists to avoid collision
            continue
        print(f" - {eid} -> {target}")
        e["entity_id"] = target
        existing_ids.discard(eid)
        existing_ids.add(target)
        changed += 1

    if changed:
        with open(REG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Renamed {changed} entities.")
    else:
        print("No entities needed renaming.")

    start_ha()
    print("🚀 Home Assistant starting. Review /tmp/ha_startup.log if needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
