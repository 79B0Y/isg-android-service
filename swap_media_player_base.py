#!/usr/bin/env python3
"""
Replace legacy base media_player entity with the new one:
- Remove entity_id 'media_player.android_tv_box_media_player' (old unique_id)
- Rename 'media_player.android_tv_box_media_player_2' to the base name

Backs up the registry and restarts HA.
"""

import json
import os
import shutil
import subprocess
import time

HA_CONFIG_DIR = "/home/bo/.homeassistant"
REG_PATH = os.path.join(HA_CONFIG_DIR, ".storage", "core.entity_registry")


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
    if not os.path.exists(REG_PATH):
        print("Registry not found:", REG_PATH)
        return 1
    stop_ha()
    backup = REG_PATH + ".bak"
    shutil.copy2(REG_PATH, backup)
    print("Backup created:", backup)

    with open(REG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    ents = data.get("data", {}).get("entities", [])
    # Remove base if present
    new_ents = [e for e in ents if e.get("entity_id") != "media_player.android_tv_box_media_player"]
    # Rename _2 to base
    for e in new_ents:
        if e.get("entity_id") == "media_player.android_tv_box_media_player_2":
            e["entity_id"] = "media_player.android_tv_box_media_player"
            break

    if len(new_ents) != len(ents):
        data["data"]["entities"] = new_ents
        with open(REG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Swapped media_player entities: removed base and promoted _2 to base")
    else:
        print("No changes applied (entities already in desired state)")

    start_ha()
    print("✅ Home Assistant starting. Review /tmp/ha_startup.log if needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

