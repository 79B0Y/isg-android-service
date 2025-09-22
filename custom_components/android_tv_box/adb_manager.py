"""ADB Manager for Android TV Box integration."""
from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any, Dict, Optional, Tuple

try:
    from adb_shell.adb_device import AdbDeviceTcp
    from adb_shell.exceptions import TcpTimeoutException
except ImportError as e:
    raise ImportError(
        f"Required ADB library not found: {e}. "
        "Please install with: pip install adb-shell>=0.4.4"
    ) from e

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
            _LOGGER.info("Attempting to connect to Android TV Box at %s:%s", self.host, self.port)
            
            # Clean up any existing connection
            if self._device:
                try:
                    await self._device.close()
                except Exception:
                    pass
            
            # Create new ADB TCP device
            self._device = AdbDeviceTcp(self.host, self.port, default_transport_timeout_s=self.timeout)
            
            # Establish the TCP connection first
            _LOGGER.debug("Establishing TCP connection...")
            await asyncio.get_event_loop().run_in_executor(
                None, self._device.connect, None, self.timeout
            )
            
            # Test with a simple echo command
            _LOGGER.debug("Testing connection with echo command...")
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._device.shell, "echo 'connection_test'"
            )
            
            if result and "connection_test" in result:
                self._connected = True
                _LOGGER.info("Successfully connected to Android TV Box at %s:%s", self.host, self.port)
                return True
            else:
                _LOGGER.error("Connection test failed - no response from device")
                self._connected = False
                return False
            
        except asyncio.TimeoutError:
            _LOGGER.error("Connection timeout to %s:%s after %s seconds", self.host, self.port, self.timeout)
            self._connected = False
            return False
        except ConnectionRefusedError:
            _LOGGER.error("Connection refused by %s:%s - check if ADB is enabled", self.host, self.port)
            self._connected = False
            return False
        except Exception as e:
            _LOGGER.error("Failed to connect to %s:%s: %s (Type: %s)", self.host, self.port, str(e), type(e).__name__)
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from the Android device."""
        if self._device:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._device.close
                )
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
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._device.shell, command
            )
            
            # ADB shell returns string directly
            stdout = result.strip() if result else ""
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
            _LOGGER.debug("No ADB device instance available")
            return False
            
        try:
            # Use a simple echo test instead of checking for "connected"
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._device.shell, "echo 'connection_check'"
            )
            
            if result and "connection_check" in result:
                self._connected = True
                _LOGGER.debug("Connection check successful")
                return True
            else:
                _LOGGER.debug("Connection check failed - no response")
                self._connected = False
                return False
                
        except asyncio.TimeoutError:
            _LOGGER.debug("Connection check timeout")
            self._connected = False
            return False
        except Exception as e:
            _LOGGER.debug("Connection check failed: %s", e)
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

            wakefulness = "unknown"
            screen_on = None

            for line in stdout.split('\n'):
                line = line.strip()
                if 'mWakefulness=' in line:
                    if 'Awake' in line:
                        wakefulness = "on"
                    elif 'Asleep' in line:
                        wakefulness = "off"
                    elif 'Dreaming' in line or 'Dozing' in line:
                        wakefulness = "standby"
                # Legacy field
                if 'mScreenOn=' in line:
                    screen_on = 'true' in line.lower()
                # Newer formats: Display Power: state=ON/OFF
                m = re.search(r"state=([A-Z]+)", line)
                if m and 'Display' in line:
                    state = m.group(1)
                    if state == 'ON':
                        screen_on = True
                        if wakefulness == 'unknown':
                            wakefulness = 'on'
                    elif state in ('OFF', 'DOZE'):
                        screen_on = False
                        if wakefulness == 'unknown':
                            wakefulness = 'off'

            # Fallback to dumpsys display if screen_on is still unknown
            if screen_on is None:
                disp, _ = await self._execute_command("dumpsys display | grep -i 'mScreenState\|state=' | head -n 5")
                if re.search(r"(mScreenState=ON|state=ON|Display 0 state=ON)", disp or '', re.I):
                    screen_on = True
                    if wakefulness == 'unknown':
                        wakefulness = 'on'
                elif re.search(r"(mScreenState=OFF|state=OFF|Display 0 state=OFF)", disp or '', re.I):
                    screen_on = False
                    if wakefulness == 'unknown':
                        wakefulness = 'off'

            return wakefulness, bool(screen_on) if screen_on is not None else False
        
        except Exception as e:
            _LOGGER.error("Failed to get power state: %s", e)
            return "unknown", False

    async def set_power_state(self, power_on: bool) -> bool:
        """Ensure screen power state matches desired value (robust)."""
        try:
            current, _screen = await self.get_power_state()
            target = "on" if power_on else "off"
            if current == target:
                return True

            # First attempt
            primary = ADB_CONTROL_COMMANDS["power_on" if power_on else "power_off"]
            await self._execute_command(primary)
            await asyncio.sleep(0.8)
            new_state, _ = await self.get_power_state()
            if new_state == target:
                return True

            # Fallback: toggle power key
            await self._execute_command("input keyevent 26")
            await asyncio.sleep(0.8)
            new_state, _ = await self.get_power_state()
            if new_state == target:
                return True

            # Final retry once more
            await asyncio.sleep(0.6)
            await self._execute_command("input keyevent 26")
            await asyncio.sleep(0.8)
            new_state, _ = await self.get_power_state()
            return new_state == target

        except Exception as e:
            _LOGGER.error("Failed to set power state to %s: %s", power_on, e)
            return False

    async def quick_power(self, power_on: bool) -> None:
        """Fire-and-forget style power command with minimal delay.

        Used for immediate UI feedback; robustness handled elsewhere.
        """
        try:
            cmd = ADB_CONTROL_COMMANDS["power_on" if power_on else "power_off"]
            await self._execute_command(cmd)
        except Exception as e:
            _LOGGER.debug("quick_power failed: %s", e)

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

    # ===== Media / Volume helpers =====

    async def get_volume_state(self) -> Tuple[int, int, bool]:
        """Get (current_volume, max_volume, muted) for media stream 3.

        Uses: cmd media_session volume --stream 3 --get
        Example output: "volume is 8 in range [0..15]"
        """
        try:
            stdout, _ = await self._execute_command("cmd media_session volume --stream 3 --get")
            import re
            m = re.search(r"volume is\s+(\d+)\s+in range\s+\[0\.\.(\d+)\]", stdout or "")
            if m:
                current = int(m.group(1))
                max_vol = int(m.group(2))
                return current, max_vol, current == 0
        except Exception as e:
            _LOGGER.warning("get_volume_state failed: %s", e)
        return 0, 15, False

    async def set_volume(self, level: int) -> bool:
        """Set media volume level (0..max). Uses service call audio."""
        try:
            await self._execute_command(f"service call audio 12 i32 3 i32 {level} i32 0")
            await asyncio.sleep(0.3)
            return True
        except Exception as e:
            _LOGGER.warning("set_volume failed: %s", e)
            return False

    async def start_app(self, target: str) -> bool:
        """Start an app by package or component.

        - If `target` contains '/', treat as component for am start -n
        - Else resolve launcher activity or use monkey
        """
        if not target:
            return False
        try:
            if "/" in target:
                # Component specified
                await self._execute_command(f"am start -n {target}")
                await asyncio.sleep(0.8)
                return True

            package = target
            # Try to resolve launcher activity
            comp_out, _ = await self._execute_command(
                f"cmd package resolve-activity --brief {package} | tail -n 1"
            )
            comp_out = (comp_out or "").strip()
            if comp_out and "/" in comp_out:
                await self._execute_command(f"am start -n {comp_out}")
                await asyncio.sleep(0.8)
                return True

            # Fallback to main launcher intent
            await self._execute_command(
                f"am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER {package}"
            )
            await asyncio.sleep(0.8)
            return True
        except Exception as e:
            _LOGGER.warning("start_app failed for %s: %s", target, e)
            # Final fallback to monkey
            try:
                await self._execute_command(f"monkey -p {target} -c android.intent.category.LAUNCHER 1")
                await asyncio.sleep(0.8)
                return True
            except Exception as e2:
                _LOGGER.warning("monkey fallback failed for %s: %s", target, e2)
                return False

    async def get_current_app(self) -> Optional[str]:
        """Return current foreground app package if detectable."""
        try:
            # Try activity stack first (Android 10+ may use 'topResumedActivity')
            out, _ = await self._execute_command("dumpsys activity activities | grep -m 1 -E 'mResumedActivity|topResumedActivity'")
            m = re.search(r" ([a-zA-Z0-9_\.]+)/(?:[A-Za-z0-9_\./]+)", out or "")
            if m:
                return m.group(1)
            # Fallback: dumpsys activity top
            out_top, _ = await self._execute_command("dumpsys activity top | head -n 20")
            m_top = re.search(r"ACTIVITY\s+([a-zA-Z0-9_\.]+)/", out_top or "")
            if m_top:
                return m_top.group(1)
            # Fallback to window focus
            out2, _ = await self._execute_command("dumpsys window windows | grep -m 1 mCurrentFocus")
            m2 = re.search(r" ([a-zA-Z0-9_\.]+)/", out2 or "")
            if m2:
                return m2.group(1)
        except Exception as e:
            _LOGGER.debug("get_current_app failed: %s", e)
        return None

    # ===== High-level helpers for buttons =====

    async def send_key(self, keycode: int) -> bool:
        """Send an Android keyevent."""
        if not self.is_connected:
            return False
        try:
            await self._execute_command(f"input keyevent {keycode}")
            return True
        except Exception as e:
            _LOGGER.warning("send_key failed: %s", e)
            return False

    async def restart_isg(self) -> bool:
        """Force-stop and restart the ISG app."""
        if not self.is_connected:
            return False
        try:
            # Stop then start the ISG main activity
            await self._execute_command("am force-stop com.linknlink.app.device.isg")
            await asyncio.sleep(1.5)
            await self._execute_command("am start -n com.linknlink.app.device.isg/.MainActivity")
            return True
        except Exception as e:
            _LOGGER.warning("restart_isg failed: %s", e)
            return False

    async def refresh_apps(self) -> bool:
        """Refresh installed user apps list (pm list packages -3)."""
        if not self.is_connected:
            return False
        try:
            stdout, _ = await self._execute_command("pm list packages -3")
            _LOGGER.debug("Installed apps sample: %s", (stdout or "").splitlines()[:10])
            return True
        except Exception as e:
            _LOGGER.warning("refresh_apps failed: %s", e)
            return False

    async def reboot_device(self) -> bool:
        """Reboot the device."""
        if not self.is_connected:
            return False
        try:
            await self._execute_command("svc power reboot || reboot")
            return True
        except Exception as e:
            _LOGGER.warning("reboot_device failed: %s", e)
            return False

    async def take_screenshot(self) -> Optional[str]:
        """Take a screenshot on device and save to /sdcard/Download/.

        Returns the device file path if successful.
        """
        if not self.is_connected:
            return None
        try:
            # Milliseconds timestamp-based name
            ts = int(asyncio.get_event_loop().time() * 1000)
            device_path = f"/sdcard/Download/android_tv_box_{ts}.png"
            await self._execute_command(f"screencap -p {device_path}")
            # Verify file exists
            stdout, _ = await self._execute_command(f"ls {device_path}")
            if device_path in (stdout or ""):
                return device_path
            return None
        except Exception as e:
            _LOGGER.warning("take_screenshot failed: %s", e)
            return None

    async def pull_file(self, device_path: str, local_path: str) -> bool:
        """Pull a file from device to host using adb-shell file sync.

        local_path should be an absolute path on the host.
        """
        if not self.is_connected or not self._device:
            return False
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            loop = asyncio.get_event_loop()
            # Use the device's pull method in executor
            await loop.run_in_executor(None, self._device.pull, device_path, local_path)
            return os.path.exists(local_path) and os.path.getsize(local_path) > 0
        except Exception as e:
            _LOGGER.warning("pull_file failed: %s", e)
            return False

    async def test_adb_connection(self) -> Dict[str, Any]:
        """Test ADB connection and return connection details."""
        result = {
            "connected": False,
            "error": None,
            "device_info": {},
            "power_state": "unknown",
            "wifi_enabled": False,
            "connection_details": {},
        }
        
        try:
            _LOGGER.info("Starting ADB connection test for %s:%s", self.host, self.port)
            
            # Test basic connection with detailed error reporting
            connection_start_time = asyncio.get_event_loop().time()
            
            # First try to connect
            connected = await self.connect()
            connection_time = asyncio.get_event_loop().time() - connection_start_time
            
            result["connection_details"]["connection_time"] = round(connection_time, 2)
            result["connected"] = connected
            
            if connected:
                _LOGGER.info("Basic connection successful in %.2f seconds", connection_time)
                
                # Test basic command execution
                try:
                    _LOGGER.debug("Testing basic shell command...")
                    test_result = await self._execute_command("echo 'test_command'")
                    result["connection_details"]["shell_test"] = "success" if test_result[0] else "failed"
                except Exception as shell_error:
                    _LOGGER.warning("Shell command test failed: %s", shell_error)
                    result["connection_details"]["shell_test"] = f"failed: {shell_error}"
                
                # Get device info with timeout
                try:
                    _LOGGER.debug("Getting device information...")
                    result["device_info"] = await asyncio.wait_for(
                        self.get_device_info(), 
                        timeout=10
                    )
                    _LOGGER.info("Device info retrieved: %s", result["device_info"])
                except asyncio.TimeoutError:
                    _LOGGER.warning("Device info timeout")
                    result["connection_details"]["device_info_error"] = "timeout"
                except Exception as device_error:
                    _LOGGER.warning("Device info failed: %s", device_error)
                    result["connection_details"]["device_info_error"] = str(device_error)
                
                # Test power state
                try:
                    power_state, screen_on = await asyncio.wait_for(
                        self.get_power_state(), 
                        timeout=5
                    )
                    result["power_state"] = power_state
                    result["connection_details"]["screen_on"] = screen_on
                except Exception as power_error:
                    _LOGGER.warning("Power state check failed: %s", power_error)
                    result["connection_details"]["power_error"] = str(power_error)
                
                # Test WiFi state
                try:
                    wifi_info = await asyncio.wait_for(
                        self.get_wifi_state(), 
                        timeout=5
                    )
                    result["wifi_enabled"] = wifi_info["enabled"]
                    result["connection_details"]["wifi_info"] = wifi_info
                except Exception as wifi_error:
                    _LOGGER.warning("WiFi state check failed: %s", wifi_error)
                    result["connection_details"]["wifi_error"] = str(wifi_error)
                    
            else:
                _LOGGER.error("Initial connection failed after %.2f seconds", connection_time)
                result["error"] = "Failed to establish initial ADB connection"
                
        except Exception as e:
            error_msg = f"Connection test failed: {str(e)} (Type: {type(e).__name__})"
            result["error"] = error_msg
            _LOGGER.error(error_msg)
            
        _LOGGER.info("ADB connection test completed. Connected: %s", result["connected"])
        return result
