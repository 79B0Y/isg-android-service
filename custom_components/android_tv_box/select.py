"""Select platform for Android TV Box integration (App selector)."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, OPT_APPS
from .coordinator import AndroidTVBoxUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AndroidTVBoxUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([AndroidTVBoxAppSelect(coordinator, config_entry)])


class AndroidTVBoxAppSelect(CoordinatorEntity[AndroidTVBoxUpdateCoordinator], SelectEntity):
    """Select entity listing installed third-party apps and mapped friendly names."""

    _attr_has_entity_name = True
    _attr_name = "App Selector"

    def __init__(self, coordinator: AndroidTVBoxUpdateCoordinator, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._config_entry = config_entry
        host = config_entry.data[CONF_HOST]
        port = config_entry.data[CONF_PORT]
        self._attr_unique_id = f"{host}:{port}_app_select"

        # Parse friendly mapping from options
        self._apps_map: Dict[str, str] = {}
        opt_apps = config_entry.options.get(OPT_APPS)
        if isinstance(opt_apps, str) and opt_apps.strip():
            try:
                self._apps_map = json.loads(opt_apps)
            except Exception as e:
                _LOGGER.warning("Failed to parse apps option: %s", e)

        self._update_options()

    def _update_options(self) -> None:
        pkgs = self.coordinator.data.installed_apps or []
        names = list(self._apps_map.keys()) if self._apps_map else []
        # Merge friendly names + raw packages as options (de-dup)
        merged = []
        seen = set()
        for n in names:
            if n not in seen:
                merged.append(n)
                seen.add(n)
        for p in pkgs:
            if p not in seen:
                merged.append(p)
                seen.add(p)
        self._attr_options = merged

    @property
    def current_option(self) -> Optional[str]:
        pkg = self.coordinator.data.current_app_package
        if not pkg:
            return None
        # map back to friendly name if available
        for name, package in self._apps_map.items():
            if package == pkg:
                return name
        return pkg

    async def async_select_option(self, option: str) -> None:
        # Resolve to package
        pkg = self._apps_map.get(option, option)
        await self.coordinator.adb_manager.start_app(pkg)
        # immediate reflect and refresh
        self.coordinator.data.current_app_package = await self.coordinator.adb_manager.get_current_app()
        self._update_options()
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_update(self) -> None:
        # Sync options from latest installed apps
        self._update_options()

    def _handle_coordinator_update(self) -> None:
        # Recompute options on coordinator data changes
        self._update_options()
        return super()._handle_coordinator_update()
