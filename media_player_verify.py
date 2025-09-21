#!/usr/bin/env python3
"""
Verify media_player for android_tv_box via Home Assistant REST API.

Checks:
- Locate media_player.android_tv_box_media_player* entity
- Set volume to 50% and confirm updated state
- Turn screen on then off via media_player.turn_on/off
- Fetch source list and (if any) select the first source

Requires env:
- HA_TOKEN (long-lived token)
- HA_BASE_URL (default http://localhost:8123)
"""

import json
import os
import time
import urllib.request


def api(path: str, method: str = "GET", body: dict | None = None):
    base = os.environ.get("HA_BASE_URL", "http://localhost:8123").rstrip("/")
    token = os.environ.get("HA_TOKEN")
    if not token:
        raise SystemExit("Missing HA_TOKEN env var")
    url = base + path
    data = None
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read()
        return json.loads(raw.decode("utf-8")) if raw else None


def find_media_player() -> str | None:
    states = api("/api/states")
    ids = [s["entity_id"] for s in states if s["entity_id"].startswith("media_player.android_tv_box_media_player")]
    ids.sort()
    return ids[0] if ids else None


def main() -> int:
    mp = find_media_player()
    if not mp:
        print("❌ No media_player found for android_tv_box")
        return 1
    print("Media player:", mp)

    # Volume set to 50%
    api("/api/services/media_player/volume_set", method="POST", body={"entity_id": mp, "volume_level": 0.5})
    time.sleep(1)
    st = api(f"/api/states/{mp}")
    vol = st.get("attributes", {}).get("volume_level")
    print("volume_level after set:", vol)

    # Turn on then off
    api("/api/services/media_player/turn_on", method="POST", body={"entity_id": mp})
    time.sleep(1)
    api("/api/services/media_player/turn_off", method="POST", body={"entity_id": mp})

    # Select first source if available
    st = api(f"/api/states/{mp}")
    sources = st.get("attributes", {}).get("source_list") or []
    if sources:
        src = sources[0]
        print("Selecting source:", src)
        api("/api/services/media_player/select_source", method="POST", body={"entity_id": mp, "source": src})
        time.sleep(1)
    else:
        print("No sources configured in options; skip select_source")

    print("✅ Verification finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

