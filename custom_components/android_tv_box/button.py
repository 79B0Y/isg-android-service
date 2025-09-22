"""Button platform for Android TV Box integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BUTTON_SUFFIXES, ANDROID_KEYCODES, DOMAIN
from .coordinator import AndroidTVBoxUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Android TV Box button entities from a config entry."""
    coordinator: AndroidTVBoxUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities: list[ButtonEntity] = []

    # Navigation buttons
    entities.extend(
        [
            AndroidTVBoxKeyButton(coordinator, config_entry, BUTTON_SUFFIXES["nav_up"], "Nav Up", ANDROID_KEYCODES["UP"]),
            AndroidTVBoxKeyButton(coordinator, config_entry, BUTTON_SUFFIXES["nav_down"], "Nav Down", ANDROID_KEYCODES["DOWN"]),
            AndroidTVBoxKeyButton(coordinator, config_entry, BUTTON_SUFFIXES["nav_left"], "Nav Left", ANDROID_KEYCODES["LEFT"]),
            AndroidTVBoxKeyButton(coordinator, config_entry, BUTTON_SUFFIXES["nav_right"], "Nav Right", ANDROID_KEYCODES["RIGHT"]),
            AndroidTVBoxKeyButton(coordinator, config_entry, BUTTON_SUFFIXES["nav_select"], "Select", ANDROID_KEYCODES["CENTER"]),
            AndroidTVBoxKeyButton(coordinator, config_entry, BUTTON_SUFFIXES["nav_back"], "Back", ANDROID_KEYCODES["BACK"]),
            AndroidTVBoxKeyButton(coordinator, config_entry, BUTTON_SUFFIXES["nav_home"], "Home", ANDROID_KEYCODES["HOME"]),
            AndroidTVBoxKeyButton(coordinator, config_entry, BUTTON_SUFFIXES["nav_menu"], "Menu", ANDROID_KEYCODES["MENU"]),
        ]
    )

    # Action buttons
    entities.extend(
        [
            AndroidTVBoxRestartISGButton(coordinator, config_entry),
            AndroidTVBoxRefreshAppsButton(coordinator, config_entry),
            AndroidTVBoxRebootDeviceButton(coordinator, config_entry),
            AndroidTVBoxScreenshotButton(coordinator, config_entry),
        ]
    )

    async_add_entities(entities)


class AndroidTVBoxButtonBase(CoordinatorEntity[AndroidTVBoxUpdateCoordinator], ButtonEntity):
    """Base class for Android TV Box button entities."""

    def __init__(self, coordinator: AndroidTVBoxUpdateCoordinator, config_entry: ConfigEntry, unique_suffix: str, name: str) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_has_entity_name = True
        self._attr_name = name

        # Unique ID based on host:port and suffix
        host = config_entry.data[CONF_HOST]
        port = config_entry.data[CONF_PORT]
        self._attr_unique_id = f"{host}:{port}_{unique_suffix}"

    @property
    def device_info(self) -> Dict[str, Any]:
        return self.coordinator.device_info


class AndroidTVBoxKeyButton(AndroidTVBoxButtonBase):
    """Button to send a keyevent."""

    def __init__(self, coordinator: AndroidTVBoxUpdateCoordinator, config_entry: ConfigEntry, unique_suffix: str, name: str, keycode: int) -> None:
        super().__init__(coordinator, config_entry, unique_suffix, name)
        self._keycode = keycode
        self._attr_icon = "mdi:remote"

    async def async_press(self) -> None:
        try:
            await self.coordinator.adb_manager.send_key(self._keycode)
            await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.warning("Key press failed: %s", e)


class AndroidTVBoxRestartISGButton(AndroidTVBoxButtonBase):
    def __init__(self, coordinator: AndroidTVBoxUpdateCoordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, BUTTON_SUFFIXES["restart_isg"], "Restart ISG")
        self._attr_icon = "mdi:reload"

    async def async_press(self) -> None:
        try:
            ok = await self.coordinator.adb_manager.restart_isg()
            if ok:
                await asyncio.sleep(3.0)
            await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.warning("Restart ISG failed: %s", e)


class AndroidTVBoxRefreshAppsButton(AndroidTVBoxButtonBase):
    def __init__(self, coordinator: AndroidTVBoxUpdateCoordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, BUTTON_SUFFIXES["refresh_apps"], "Refresh Apps")
        self._attr_icon = "mdi:application"

    async def async_press(self) -> None:
        try:
            # Immediate refresh of installed apps and notify select entities
            updated = await self.coordinator.async_refresh_installed_apps()
            if not updated:
                # fallback to generic refresh
                await self.coordinator.adb_manager.refresh_apps()
                await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.warning("Refresh apps failed: %s", e)


class AndroidTVBoxRebootDeviceButton(AndroidTVBoxButtonBase):
    def __init__(self, coordinator: AndroidTVBoxUpdateCoordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, BUTTON_SUFFIXES["reboot_device"], "Reboot Device")
        self._attr_icon = "mdi:restart"

    async def async_press(self) -> None:
        try:
            await self.coordinator.adb_manager.reboot_device()
        except Exception as e:
            _LOGGER.warning("Reboot device failed: %s", e)


class AndroidTVBoxScreenshotButton(AndroidTVBoxButtonBase):
    def __init__(self, coordinator: AndroidTVBoxUpdateCoordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator, config_entry, BUTTON_SUFFIXES["screenshot"], "Screenshot")
        self._attr_icon = "mdi:camera"

    async def async_press(self) -> None:
        try:
            device_path = await self.coordinator.adb_manager.take_screenshot()
            if device_path:
                _LOGGER.info("Screenshot saved on device: %s", device_path)
                # Also pull to HA www directory for easy viewing
                local_dir = "/home/bo/.homeassistant/www/screenshots"
                ts = int(asyncio.get_event_loop().time() * 1000)
                local_path = f"{local_dir}/android_tv_box_{ts}.png"
                ok = await self.coordinator.adb_manager.pull_file(device_path, local_path)
                if ok:
                    _LOGGER.info("Screenshot copied to: %s", local_path)
            await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.warning("Screenshot failed: %s", e)
