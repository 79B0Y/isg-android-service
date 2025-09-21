"""Switch platform for Android TV Box integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_IP_ADDRESS,
    ATTR_WIFI_SSID,
    CONF_DEVICE_NAME,
    DOMAIN,
    ENTITY_SUFFIXES,
)
from .coordinator import AndroidTVBoxUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Android TV Box switch entities from a config entry."""
    coordinator: AndroidTVBoxUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [
        AndroidTVBoxADBConnectionSwitch(coordinator, config_entry),
        AndroidTVBoxPowerSwitch(coordinator, config_entry),
        AndroidTVBoxWiFiSwitch(coordinator, config_entry),
    ]
    
    async_add_entities(entities)


class AndroidTVBoxSwitchEntity(CoordinatorEntity[AndroidTVBoxUpdateCoordinator], SwitchEntity):
    """Base class for Android TV Box switch entities."""

    def __init__(
        self,
        coordinator: AndroidTVBoxUpdateCoordinator,
        config_entry: ConfigEntry,
        entity_suffix: str,
        name_suffix: str,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        
        self._config_entry = config_entry
        self._entity_suffix = entity_suffix
        self._name_suffix = name_suffix
        
        # Entity attributes
        self._attr_has_entity_name = True
        self._attr_name = name_suffix
        
        # Unique ID
        host = config_entry.data[CONF_HOST]
        port = config_entry.data[CONF_PORT]
        self._attr_unique_id = f"{host}:{port}_{entity_suffix}"

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device info."""
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data.is_connected


class AndroidTVBoxADBConnectionSwitch(AndroidTVBoxSwitchEntity):
    """Switch to show and control ADB connection status."""

    def __init__(
        self,
        coordinator: AndroidTVBoxUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize ADB connection switch."""
        super().__init__(
            coordinator,
            config_entry,
            ENTITY_SUFFIXES["adb_connection"],
            "ADB Connection"
        )
        
        self._attr_icon = "mdi:usb-port"
        self._attr_entity_category = "diagnostic"

    @property
    def is_on(self) -> bool:
        """Return true if ADB connection is active."""
        return self.coordinator.data.is_connected

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        attrs = {}
        
        if self.coordinator.data.last_seen:
            attrs["last_seen"] = self.coordinator.data.last_seen.isoformat()
        
        if self.coordinator.data.last_error:
            attrs["last_error"] = self.coordinator.data.last_error
            
        attrs["error_count"] = self.coordinator.data.error_count
        attrs["host"] = self.coordinator.host
        attrs["port"] = self.coordinator.port
        
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on ADB connection (attempt reconnection)."""
        _LOGGER.debug("Attempting to reconnect ADB connection")
        
        try:
            # Disconnect first to ensure clean reconnection
            await self.coordinator.adb_manager.disconnect()
            
            # Attempt reconnection
            connected = await self.coordinator.adb_manager.connect()
            
            if connected:
                self.coordinator.data.update_connection_status(True)
                # Request immediate data refresh
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.warning("Failed to reconnect ADB connection")
                
        except Exception as e:
            _LOGGER.error("Error reconnecting ADB: %s", e)
            self.coordinator.data.set_error(str(e))

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off ADB connection (disconnect)."""
        _LOGGER.debug("Disconnecting ADB connection")
        
        try:
            await self.coordinator.adb_manager.disconnect()
            self.coordinator.data.update_connection_status(False)
            # Request immediate data refresh
            await self.coordinator.async_request_refresh()
            
        except Exception as e:
            _LOGGER.error("Error disconnecting ADB: %s", e)
            self.coordinator.data.set_error(str(e))


class AndroidTVBoxPowerSwitch(AndroidTVBoxSwitchEntity):
    """Switch to control device power state."""

    def __init__(
        self,
        coordinator: AndroidTVBoxUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize power switch."""
        super().__init__(
            coordinator,
            config_entry,
            ENTITY_SUFFIXES["power"],
            "Power"
        )
        
        self._attr_icon = "mdi:television-box"

    @property
    def icon(self) -> str:
        """Return icon based on power state."""
        if self.coordinator.data.power_state == "on":
            return "mdi:television-box"
        elif self.coordinator.data.power_state == "standby":
            return "mdi:television-ambient-light"
        else:
            return "mdi:television-off"

    @property
    def is_on(self) -> bool:
        """Return true if device is powered on."""
        return self.coordinator.data.power_state == "on"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        return {
            "power_state": self.coordinator.data.power_state,
            "screen_on": self.coordinator.data.screen_on,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the device."""
        _LOGGER.debug("Turning on Android TV Box")
        
        success = await self.coordinator.async_set_power_state(True)
        if not success:
            _LOGGER.warning("Failed to turn on device")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the device."""
        _LOGGER.debug("Turning off Android TV Box")
        
        success = await self.coordinator.async_set_power_state(False)
        if not success:
            _LOGGER.warning("Failed to turn off device")


class AndroidTVBoxWiFiSwitch(AndroidTVBoxSwitchEntity):
    """Switch to control WiFi state."""

    def __init__(
        self,
        coordinator: AndroidTVBoxUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize WiFi switch."""
        super().__init__(
            coordinator,
            config_entry,
            ENTITY_SUFFIXES["wifi"],
            "WiFi"
        )
        
        self._attr_icon = "mdi:wifi"

    @property
    def icon(self) -> str:
        """Return icon based on WiFi state."""
        if self.coordinator.data.wifi_enabled and self.coordinator.data.wifi_connected:
            return "mdi:wifi"
        elif self.coordinator.data.wifi_enabled:
            return "mdi:wifi-strength-1"
        else:
            return "mdi:wifi-off"

    @property
    def is_on(self) -> bool:
        """Return true if WiFi is enabled."""
        return self.coordinator.data.wifi_enabled

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        attrs = {
            "wifi_enabled": self.coordinator.data.wifi_enabled,
            "wifi_connected": self.coordinator.data.wifi_connected,
        }
        
        if self.coordinator.data.wifi_ssid:
            attrs[ATTR_WIFI_SSID] = self.coordinator.data.wifi_ssid
            
        if self.coordinator.data.ip_address:
            attrs[ATTR_IP_ADDRESS] = self.coordinator.data.ip_address
            
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable WiFi."""
        _LOGGER.debug("Enabling WiFi on Android TV Box")
        
        success = await self.coordinator.async_set_wifi_state(True)
        if not success:
            _LOGGER.warning("Failed to enable WiFi")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable WiFi."""
        _LOGGER.debug("Disabling WiFi on Android TV Box")
        
        success = await self.coordinator.async_set_wifi_state(False)
        if not success:
            _LOGGER.warning("Failed to disable WiFi")