"""Data update coordinator for Android TV Box."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .adb_manager import ADBManager
from .const import (
    ATTR_ANDROID_VERSION,
    ATTR_DEVICE_BRAND,
    ATTR_DEVICE_MODEL,
    ATTR_IP_ADDRESS,
    ATTR_WIFI_SSID,
    CONF_DEVICE_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class AndroidTVBoxData:
    """Class to hold Android TV Box data."""

    def __init__(self) -> None:
        """Initialize the data class."""
        # Connection status
        self.is_connected: bool = False
        self.last_seen: Optional[datetime] = None
        
        # Device information
        self.device_model: Optional[str] = None
        self.android_version: Optional[str] = None
        self.device_brand: Optional[str] = None
        
        # Power state
        self.power_state: str = "unknown"  # on, off, standby, unknown
        self.screen_on: bool = False
        
        # Network state
        self.wifi_enabled: bool = False
        self.wifi_connected: bool = False
        self.wifi_ssid: Optional[str] = None
        self.ip_address: Optional[str] = None
        
        # Media / volume state
        self.volume_level: int = 0
        self.volume_max: int = 15
        self.volume_percentage: float = 0.0
        self.muted: bool = False
        self.current_app_package: Optional[str] = None
        
        # Error tracking
        self.last_error: Optional[str] = None
        self.error_count: int = 0

    def update_connection_status(self, connected: bool) -> None:
        """Update connection status."""
        self.is_connected = connected
        if connected:
            self.last_seen = datetime.now()
            self.error_count = 0
            self.last_error = None
        else:
            self.error_count += 1

    def update_device_info(self, device_info: Dict[str, Any]) -> None:
        """Update device information."""
        self.device_model = device_info.get("model")
        self.android_version = device_info.get("android_version")
        self.device_brand = device_info.get("brand")

    def update_power_state(self, power_state: str, screen_on: bool) -> None:
        """Update power state."""
        self.power_state = power_state
        self.screen_on = screen_on

    def update_wifi_state(self, wifi_info: Dict[str, Any]) -> None:
        """Update WiFi state."""
        self.wifi_enabled = wifi_info.get("enabled", False)
        self.wifi_connected = wifi_info.get("connected", False)
        self.wifi_ssid = wifi_info.get("ssid")
        self.ip_address = wifi_info.get("ip_address")

    def set_error(self, error: str) -> None:
        """Set error information."""
        self.last_error = error
        self.error_count += 1

    @property
    def device_info_dict(self) -> Dict[str, Any]:
        """Return device info as dict for Home Assistant."""
        return {
            ATTR_DEVICE_MODEL: self.device_model or "Unknown",
            ATTR_ANDROID_VERSION: self.android_version or "Unknown",
            ATTR_DEVICE_BRAND: self.device_brand or "Unknown",
            ATTR_IP_ADDRESS: self.ip_address,
            ATTR_WIFI_SSID: self.wifi_ssid,
        }


class AndroidTVBoxUpdateCoordinator(DataUpdateCoordinator[AndroidTVBoxData]):
    """Class to manage fetching Android TV Box data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.config_entry = config_entry
        self.host = config_entry.data[CONF_HOST]
        self.port = config_entry.data[CONF_PORT]
        self.device_name = config_entry.data[CONF_DEVICE_NAME]
        
        # Initialize ADB manager
        self.adb_manager = ADBManager(self.host, self.port)
        
        # Update intervals
        self._last_device_info_update: Optional[datetime] = None
        self._device_info_interval = timedelta(minutes=15)
        self._connection_check_failures = 0
        self._max_failures_before_reconnect = 3

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        
        # Initialize data after super().__init__()
        # This ensures DataUpdateCoordinator doesn't override our data
        self.data = AndroidTVBoxData()

    async def async_setup(self) -> bool:
        """Set up the coordinator."""
        try:
            # Initial connection attempt
            connected = await self.adb_manager.connect()
            if connected:
                # Get initial device info
                device_info = await self.adb_manager.get_device_info()
                self.data.update_device_info(device_info)
                self.data.update_connection_status(True)
                _LOGGER.info("Android TV Box coordinator setup completed successfully")
                return True
            else:
                _LOGGER.warning("Initial ADB connection failed, will retry during updates")
                return True  # Still allow setup, will retry connections
        except Exception as e:
            _LOGGER.error("Failed to set up Android TV Box coordinator: %s", e)
            return False

    async def _async_update_data(self) -> AndroidTVBoxData:
        """Fetch data from Android TV Box."""
        try:
            # Check connection first
            if not self.adb_manager.is_connected:
                _LOGGER.debug("Attempting to reconnect to Android TV Box")
                connected = await self.adb_manager.connect()
                if not connected:
                    self._connection_check_failures += 1
                    raise UpdateFailed(f"Cannot connect to Android TV Box at {self.host}:{self.port}")
                else:
                    self._connection_check_failures = 0

            # Test connection with a simple check
            connection_active = await self.adb_manager.check_connection()
            if not connection_active:
                self._connection_check_failures += 1
                self.data.update_connection_status(False)
                
                # Try to reconnect after multiple failures
                if self._connection_check_failures >= self._max_failures_before_reconnect:
                    _LOGGER.warning("Multiple connection failures, attempting reconnect")
                    await self.adb_manager.disconnect()
                    connected = await self.adb_manager.connect()
                    if connected:
                        self._connection_check_failures = 0
                        connection_active = True
                    else:
                        raise UpdateFailed("Failed to reconnect after multiple failures")

            if connection_active:
                self.data.update_connection_status(True)
                
                # Update power state
                try:
                    power_state, screen_on = await self.adb_manager.get_power_state()
                    self.data.update_power_state(power_state, screen_on)
                except Exception as e:
                    _LOGGER.warning("Failed to get power state: %s", e)

                # Update WiFi state
                try:
                    wifi_info = await self.adb_manager.get_wifi_state()
                    self.data.update_wifi_state(wifi_info)
                except Exception as e:
                    _LOGGER.warning("Failed to get WiFi state: %s", e)

                # Update volume state
                try:
                    vol, vmax, muted = await self.adb_manager.get_volume_state()
                    self.data.volume_level = vol
                    self.data.volume_max = vmax
                    self.data.muted = muted
                    self.data.volume_percentage = (vol / vmax * 100.0) if vmax else 0.0
                except Exception as e:
                    _LOGGER.debug("Failed to get volume state: %s", e)

                # Update current app
                try:
                    pkg = await self.adb_manager.get_current_app()
                    self.data.current_app_package = pkg
                except Exception as e:
                    _LOGGER.debug("Failed to get current app: %s", e)

                # Update device info periodically
                now = datetime.now()
                if (
                    self._last_device_info_update is None
                    or now - self._last_device_info_update > self._device_info_interval
                ):
                    try:
                        device_info = await self.adb_manager.get_device_info()
                        self.data.update_device_info(device_info)
                        self._last_device_info_update = now
                    except Exception as e:
                        _LOGGER.warning("Failed to get device info: %s", e)

            return self.data

        except UpdateFailed:
            raise
        except Exception as e:
            error_msg = f"Error updating Android TV Box data: {e}"
            _LOGGER.error(error_msg)
            self.data.set_error(str(e))
            self.data.update_connection_status(False)
            raise UpdateFailed(error_msg)

    async def async_set_power_state(self, power_on: bool) -> bool:
        """Set device power state."""
        try:
            if not self.adb_manager.is_connected:
                connected = await self.adb_manager.connect()
                if not connected:
                    return False

            success = await self.adb_manager.set_power_state(power_on)
            
            if success:
                # Immediately update local state
                await asyncio.sleep(0.5)  # Brief wait for state change
                power_state, screen_on = await self.adb_manager.get_power_state()
                self.data.update_power_state(power_state, screen_on)
                
            # Request a full refresh
            await self.async_request_refresh()
            return success
            
        except Exception as e:
            _LOGGER.error("Failed to set power state: %s", e)
            return False

    async def async_set_wifi_state(self, enabled: bool) -> bool:
        """Set WiFi state."""
        try:
            if not self.adb_manager.is_connected:
                connected = await self.adb_manager.connect()
                if not connected:
                    return False

            success = await self.adb_manager.set_wifi_state(enabled)
            
            if success:
                # Immediately update local state
                await asyncio.sleep(1.0)  # Wait for WiFi state change
                wifi_info = await self.adb_manager.get_wifi_state()
                self.data.update_wifi_state(wifi_info)
                
            # Request a full refresh
            await self.async_request_refresh()
            return success
            
        except Exception as e:
            _LOGGER.error("Failed to set WiFi state: %s", e)
            return False

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self.adb_manager:
            await self.adb_manager.disconnect()

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return device info for Home Assistant device registry."""
        return {
            "identifiers": {(DOMAIN, f"{self.host}:{self.port}")},
            "name": self.device_name,
            "manufacturer": self.data.device_brand or "Android",
            "model": self.data.device_model or "TV Box",
            "sw_version": self.data.android_version,
            "configuration_url": f"http://{self.host}:{self.port}",
        } 
