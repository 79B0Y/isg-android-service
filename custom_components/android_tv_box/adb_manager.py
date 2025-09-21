"""ADB Manager for Android TV Box integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional, Tuple

from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.exceptions import TcpTimeoutException

from .const import ADB_COMMANDS, ADB_CONTROL_COMMANDS, DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class ADBManager:
    """Manages ADB connection and commands for Android TV Box."""

    def __init__(self, host: str, port: int, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Initialize ADB manager."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self.device_id = f"{host}:{port}"
        self._device: Optional[AdbDeviceTcp] = None
        self._connected = False
        self._device_info: Dict[str, Any] = {}

    async def connect(self) -> bool:
        """Connect to the Android device via ADB."""
        try:
            _LOGGER.debug("Attempting to connect to %s:%s", self.host, self.port)
            
            if self._device is None:
                self._device = AdbDeviceTcp(self.host, self.port, default_timeout_s=self.timeout)
            
            # Test connection with a simple command
            await self._execute_command("shell echo 'test'")
            self._connected = True
            _LOGGER.info("Successfully connected to Android TV Box at %s:%s", self.host, self.port)
            return True
            
        except Exception as e:
            _LOGGER.error("Failed to connect to %s:%s: %s", self.host, self.port, e)
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from the Android device."""
        if self._device:
            try:
                await self._device.close()
                _LOGGER.info("Disconnected from Android TV Box")
            except Exception as e:
                _LOGGER.error("Error disconnecting: %s", e)
            finally:
                self._device = None
                self._connected = False

    @property
    def is_connected(self) -> bool:
        """Return connection status."""
        return self._connected and self._device is not None

    async def _execute_command(self, command: str) -> Tuple[str, str]:
        """Execute ADB command and return stdout, stderr."""
        if not self._device:
            raise ConnectionError("ADB device not connected")

        try:
            _LOGGER.debug("Executing ADB command: %s", command)
            result = await asyncio.wait_for(
                self._device.shell(command),
                timeout=self.timeout
            )
            
            # ADB shell returns bytes, convert to string
            stdout = result.decode('utf-8').strip() if result else ""
            stderr = ""
            
            _LOGGER.debug("Command result: %s", stdout[:200])  # Log first 200 chars
            return stdout, stderr
            
        except TcpTimeoutException:
            _LOGGER.error("Command timeout: %s", command)
            raise asyncio.TimeoutError(f"Command timeout: {command}")
        except Exception as e:
            _LOGGER.error("Command failed: %s - %s", command, e)
            raise

    async def check_connection(self) -> bool:
        """Check if ADB connection is active."""
        if not self._device:
            return False
            
        try:
            stdout, _ = await self._execute_command(ADB_COMMANDS["check_connection"])
            connected = "connected" in stdout.lower()
            self._connected = connected
            return connected
        except Exception:
            self._connected = False
            return False

    async def get_power_state(self) -> Tuple[str, bool]:
        """Get device power state.
        
        Returns:
            Tuple of (power_state, screen_on)
            power_state: "on", "off", "standby", "unknown"
            screen_on: True if screen is on, False otherwise
        """
        try:
            stdout, _ = await self._execute_command(ADB_COMMANDS["power_state"])
            
            # Parse dumpsys power output
            wakefulness = "unknown"
            screen_on = False
            
            for line in stdout.split('\n'):
                line = line.strip()
                if 'mWakefulness=' in line:
                    if 'Awake' in line:
                        wakefulness = "on"
                    elif 'Asleep' in line:
                        wakefulness = "off"
                    elif 'Dreaming' in line:
                        wakefulness = "standby"
                elif 'mScreenOn=' in line:
                    screen_on = 'true' in line.lower()
            
            return wakefulness, screen_on
            
        except Exception as e:
            _LOGGER.error("Failed to get power state: %s", e)
            return "unknown", False

    async def set_power_state(self, power_on: bool) -> bool:
        """Set device power state."""
        try:
            command = ADB_CONTROL_COMMANDS["power_on" if power_on else "power_off"]
            await self._execute_command(command)
            
            # Wait a moment for the command to take effect
            await asyncio.sleep(1.0)
            
            # Verify the state change
            new_state, _ = await self.get_power_state()
            expected_state = "on" if power_on else "off"
            
            return new_state == expected_state
            
        except Exception as e:
            _LOGGER.error("Failed to set power state to %s: %s", power_on, e)
            return False

    async def get_wifi_state(self) -> Dict[str, Any]:
        """Get WiFi connection state and information."""
        wifi_info = {
            "enabled": False,
            "connected": False,
            "ssid": None,
            "ip_address": None,
        }
        
        try:
            # Check if WiFi is enabled
            stdout, _ = await self._execute_command(ADB_COMMANDS["wifi_state"])
            wifi_info["enabled"] = stdout.strip() == "1"
            
            if wifi_info["enabled"]:
                # Get SSID
                try:
                    stdout, _ = await self._execute_command(ADB_COMMANDS["wifi_ssid"])
                    if "SSID:" in stdout:
                        ssid_line = stdout.strip()
                        # Extract SSID from format: SSID: "NetworkName"
                        if '"' in ssid_line:
                            wifi_info["ssid"] = ssid_line.split('"')[1]
                            wifi_info["connected"] = True
                except Exception:
                    pass
                
                # Get IP address
                try:
                    stdout, _ = await self._execute_command(ADB_COMMANDS["ip_address"])
                    for line in stdout.split('\n'):
                        if 'inet ' in line and not line.strip().startswith('inet 127.'):
                            # Extract IP from format: inet 192.168.1.100/24
                            ip_part = line.split('inet ')[1].split('/')[0].strip()
                            wifi_info["ip_address"] = ip_part
                            break
                except Exception:
                    pass
            
        except Exception as e:
            _LOGGER.error("Failed to get WiFi state: %s", e)
        
        return wifi_info

    async def set_wifi_state(self, enabled: bool) -> bool:
        """Enable or disable WiFi."""
        try:
            command = ADB_CONTROL_COMMANDS["wifi_enable" if enabled else "wifi_disable"]
            await self._execute_command(command)
            
            # Wait for WiFi state to change
            await asyncio.sleep(3.0)
            
            # Verify the state change
            wifi_info = await self.get_wifi_state()
            return wifi_info["enabled"] == enabled
            
        except Exception as e:
            _LOGGER.error("Failed to set WiFi state to %s: %s", enabled, e)
            return False

    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information."""
        if self._device_info:
            return self._device_info
            
        device_info = {}
        
        try:
            # Get device model
            stdout, _ = await self._execute_command(ADB_COMMANDS["device_model"])
            device_info["model"] = stdout.strip() if stdout else "Unknown"
            
            # Get Android version
            stdout, _ = await self._execute_command(ADB_COMMANDS["android_version"])
            device_info["android_version"] = stdout.strip() if stdout else "Unknown"
            
            # Get device brand
            stdout, _ = await self._execute_command(ADB_COMMANDS["device_brand"])
            device_info["brand"] = stdout.strip() if stdout else "Unknown"
            
            self._device_info = device_info
            
        except Exception as e:
            _LOGGER.error("Failed to get device info: %s", e)
            
        return device_info

    async def test_adb_connection(self) -> Dict[str, Any]:
        """Test ADB connection and return connection details."""
        result = {
            "connected": False,
            "error": None,
            "device_info": {},
            "power_state": "unknown",
            "wifi_enabled": False,
        }
        
        try:
            # Test basic connection
            result["connected"] = await self.check_connection()
            
            if result["connected"]:
                # Get device info
                result["device_info"] = await self.get_device_info()
                
                # Get power state
                power_state, _ = await self.get_power_state()
                result["power_state"] = power_state
                
                # Get WiFi state
                wifi_info = await self.get_wifi_state()
                result["wifi_enabled"] = wifi_info["enabled"]
                
        except Exception as e:
            result["error"] = str(e)
            _LOGGER.error("ADB connection test failed: %s", e)
            
        return result