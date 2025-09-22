#!/usr/bin/env python3
"""
Set the apps option for the android_tv_box config entry in HA storage and restart HA.

This updates the 'apps' option (JSON string) so media_player source_list is populated.
"""

import json
import os
import shutil
import subprocess
import time

HA_CONFIG_DIR = "/home/bo/.homeassistant"
ENTRIES = os.path.join(HA_CONFIG_DIR, ".storage", "core.config_entries")

DEFAULT_APPS = {
    "ISG": "com.linknlink.app.device.isg",
    "YouTube": "com.google.android.youtube",
    "Netflix": "com.netflix.mediaclient",
    "Spotify": "com.spotify.music",
}


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
    if not os.path.exists(ENTRIES):
        print("core.config_entries not found:", ENTRIES)
        return 1
    stop_ha()
    backup = ENTRIES + ".bak"
    shutil.copy2(ENTRIES, backup)
    print("Backup created:", backup)

    with open(ENTRIES, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = 0
    for e in data.get("data", {}).get("entries", []):
        if e.get("domain") == "android_tv_box":
            opts = e.get("options") or {}
            if opts.get("apps") != json.dumps(DEFAULT_APPS, ensure_ascii=False):
                opts["apps"] = json.dumps(DEFAULT_APPS, ensure_ascii=False)
                e["options"] = opts
                changed += 1

    if changed:
        with open(ENTRIES, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Updated apps option for {changed} entries.")
    else:
        print("No changes needed (apps option already set).")

    start_ha()
    print("✅ Home Assistant starting. Review /tmp/ha_startup.log if needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

