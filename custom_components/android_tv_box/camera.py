"""Camera platform for Android TV Box integration."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Optional

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SCREENSHOT_DIR, SCREENSHOT_RETAIN
from .coordinator import AndroidTVBoxUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Android TV Box camera from config entry."""
    coordinator: AndroidTVBoxUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([AndroidTVBoxCamera(coordinator, config_entry)])


class AndroidTVBoxCamera(CoordinatorEntity[AndroidTVBoxUpdateCoordinator], Camera):
    """A camera entity that captures device screenshots via ADB."""

    def __init__(self, coordinator: AndroidTVBoxUpdateCoordinator, config_entry: ConfigEntry) -> None:
        Camera.__init__(self)
        CoordinatorEntity.__init__(self, coordinator)

        self._config_entry = config_entry
        self._attr_has_entity_name = True
        self._attr_name = "Screen"

        host = config_entry.data[CONF_HOST]
        port = config_entry.data[CONF_PORT]
        self._attr_unique_id = f"{host}:{port}_camera"

        # ensure local screenshot dir exists
        try:
            os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        except Exception as e:
            _LOGGER.debug("Failed to ensure screenshot dir: %s", e)

    @property
    def device_info(self) -> Dict[str, Any]:
        return self.coordinator.device_info

    async def async_camera_image(self, width: int | None = None, height: int | None = None) -> bytes | None:
        """Return a still image from the camera.

        Strategy: take a screenshot on device, pull to local www/screenshots, enforce retention, return bytes.
        """
        try:
            device_path = await self.coordinator.adb_manager.take_screenshot()
            if not device_path:
                return None

            ts = int(asyncio.get_event_loop().time() * 1000)
            local_path = os.path.join(SCREENSHOT_DIR, f"android_tv_box_{ts}.png")
            ok = await self.coordinator.adb_manager.pull_file(device_path, local_path)
            if not ok:
                return None

            # retention cleanup
            try:
                files = sorted(
                    (os.path.join(SCREENSHOT_DIR, f) for f in os.listdir(SCREENSHOT_DIR) if f.endswith(".png")),
                    key=os.path.getmtime,
                )
                if len(files) > SCREENSHOT_RETAIN:
                    for f in files[:-SCREENSHOT_RETAIN]:
                        try:
                            os.remove(f)
                        except Exception:
                            pass
            except Exception as e:
                _LOGGER.debug("Retention cleanup failed: %s", e)

            # read bytes
            with open(local_path, "rb") as f:
                return f.read()
        except Exception as e:
            _LOGGER.warning("Failed to capture camera image: %s", e)
            return None

