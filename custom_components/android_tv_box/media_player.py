"""Media player entity for Android TV Box integration."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
)
from homeassistant.components.media_player.const import MediaPlayerState
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, OPT_APPS, OPT_WAKE_TAP_KEY, ANDROID_KEYCODES
from .coordinator import AndroidTVBoxUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AndroidTVBoxUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([AndroidTVBoxMediaPlayer(coordinator, config_entry)])


class AndroidTVBoxMediaPlayer(CoordinatorEntity[AndroidTVBoxUpdateCoordinator], MediaPlayerEntity):
    """Media player backed by ADB controls."""

    _attr_has_entity_name = True
    _attr_name = "Media Player"

    def __init__(self, coordinator: AndroidTVBoxUpdateCoordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        host = config_entry.data[CONF_HOST]
        port = config_entry.data[CONF_PORT]
        self._attr_unique_id = f"{host}:{port}_media"

        self._attr_supported_features = (
            MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_STEP
            | MediaPlayerEntityFeature.SELECT_SOURCE
            | MediaPlayerEntityFeature.PLAY
            | MediaPlayerEntityFeature.PAUSE
        )

        # Parse apps mapping from options (JSON string) if provided
        self._apps: Dict[str, str] = {}
        opt_apps = config_entry.options.get(OPT_APPS)
        if isinstance(opt_apps, str) and opt_apps.strip():
            try:
                self._apps = json.loads(opt_apps)
            except Exception as e:
                _LOGGER.warning("Failed to parse apps option: %s", e)
        if not self._apps:
            # Default minimal mapping
            self._apps = {
                "ISG": "com.linknlink.app.device.isg",
                "YouTube": "com.google.android.youtube",
                "Netflix": "com.netflix.mediaclient",
                "Spotify": "com.spotify.music",
            }

    @property
    def device_info(self) -> Dict[str, Any]:
        return self.coordinator.device_info

    @property
    def state(self) -> Optional[str]:
        # Prefer playback state if available
        if self.coordinator.data.playback_state == "playing":
            return MediaPlayerState.PLAYING
        if self.coordinator.data.playback_state == "paused":
            return MediaPlayerState.PAUSED
        # Report strictly ON/OFF for power UX
        if self.coordinator.data.screen_on:
            return MediaPlayerState.ON
        if getattr(self.coordinator.data, "power_state", "unknown") == "on":
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    @property
    def volume_level(self) -> Optional[float]:
        vmax = self.coordinator.data.volume_max or 15
        return (self.coordinator.data.volume_level / vmax) if vmax else 0.0

    async def async_set_volume_level(self, volume: float) -> None:
        # Convert to device scale and set; then immediately refresh via get_volume_state
        vmax = self.coordinator.data.volume_max or 15
        level = max(0, min(vmax, int(round(volume * vmax))))
        ok = await self.coordinator.adb_manager.set_volume(level)
        if ok:
            await asyncio.sleep(0.3)
            vol, vmax2, muted = await self.coordinator.adb_manager.get_volume_state()
            self.coordinator.data.volume_level = vol
            self.coordinator.data.volume_max = vmax2
            self.coordinator.data.muted = muted
            self.coordinator.data.volume_percentage = (vol / vmax2 * 100.0) if vmax2 else 0.0
            self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        # Low-latency path: quick command + fast polling; immediate HA state updates
        await self.coordinator.adb_manager.quick_power(True)
        tap = self._config_entry.options.get(OPT_WAKE_TAP_KEY, "CENTER")
        if tap and tap != "NONE":
            keycode = ANDROID_KEYCODES.get(tap)
            if keycode:
                await asyncio.sleep(0.1)
                await self.coordinator.adb_manager.send_key(keycode)
        for _ in range(3):
            ps, so = await self.coordinator.adb_manager.get_power_state()
            self.coordinator.data.update_power_state(ps, so)
            self.async_write_ha_state()
            if so:
                break
            await asyncio.sleep(0.1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self.coordinator.adb_manager.quick_power(False)
        for _ in range(3):
            ps, so = await self.coordinator.adb_manager.get_power_state()
            self.coordinator.data.update_power_state(ps, so)
            self.async_write_ha_state()
            if not so:
                break
            await asyncio.sleep(0.1)
        await self.coordinator.async_request_refresh()

    @property
    def source_list(self) -> list[str] | None:
        return list(self._apps.keys())

    @property
    def source(self) -> Optional[str]:
        # Map current foreground package back to a user-friendly source name
        pkg = self.coordinator.data.current_app_package
        if not pkg:
            return None
        for name, package in self._apps.items():
            if package == pkg:
                return name
        return None

    async def async_select_source(self, source: str) -> None:
        pkg = self._apps.get(source)
        if not pkg:
            return
        await self.coordinator.adb_manager.start_app(pkg)
        # Immediate app/state refresh
        await asyncio.sleep(0.3)
        cur = await self.coordinator.adb_manager.get_current_app()
        self.coordinator.data.current_app_package = cur
        # Playback state may change after switching app
        self.coordinator.data.playback_state = await self.coordinator.adb_manager.get_playback_state()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_media_play(self) -> None:
        await self.coordinator.adb_manager.media_play()
        # immediate status fetch
        st = await self.coordinator.adb_manager.get_playback_state()
        self.coordinator.data.playback_state = st
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_media_pause(self) -> None:
        await self.coordinator.adb_manager.media_pause()
        st = await self.coordinator.adb_manager.get_playback_state()
        self.coordinator.data.playback_state = st
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
