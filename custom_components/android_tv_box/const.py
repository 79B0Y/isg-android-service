"""Constants for the Android TV Box integration."""
from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "android_tv_box"

# Configuration
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_DEVICE_NAME: Final = "device_name"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Default values
DEFAULT_PORT: Final = 5555
DEFAULT_NAME: Final = "Android TV Box"
DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=60)
DEFAULT_TIMEOUT: Final = 15

# Debug and diagnostics
DEBUG_COMMANDS: Final = {
    "test_echo": "echo 'hello_world'",
    "check_adb_version": "shell getprop ro.adb.secure",
    "list_properties": "shell getprop | head -10",
    "check_network": "shell ping -c 1 8.8.8.8",
    "check_services": "shell service list | head -5",
}

# ADB Commands for device state queries
ADB_COMMANDS: Final = {
    # Connection status
    "check_connection": "shell echo 'connected'",
    
    # Power state commands
    "power_state": "shell dumpsys power | grep -E '(mWakefulness|mScreenOn)'",
    
    # Network status
    "wifi_state": "shell settings get global wifi_on",
    "wifi_ssid": "shell dumpsys wifi | grep 'SSID:' | head -1",
    "ip_address": "shell ip addr show wlan0 | grep 'inet '",
    
    # Device info
    "device_model": "shell getprop ro.product.model",
    "android_version": "shell getprop ro.build.version.release",
    "device_brand": "shell getprop ro.product.brand",
}

# ADB Control Commands
ADB_CONTROL_COMMANDS: Final = {
    # Power control
    "power_on": "shell input keyevent 224",  # KEYCODE_WAKEUP
    "power_off": "shell input keyevent 26",  # KEYCODE_POWER
    
    # WiFi control (requires root or system permissions)
    "wifi_enable": "shell svc wifi enable",
    "wifi_disable": "shell svc wifi disable",
}

# Entity unique ID suffixes
ENTITY_SUFFIXES: Final = {
    "adb_connection": "adb_connection",
    "power": "power",
    "wifi": "wifi",
}

# Device info attributes
ATTR_DEVICE_MODEL: Final = "device_model"
ATTR_ANDROID_VERSION: Final = "android_version"
ATTR_DEVICE_BRAND: Final = "device_brand"
ATTR_IP_ADDRESS: Final = "ip_address"
ATTR_WIFI_SSID: Final = "wifi_ssid"

# Update intervals for different data types
UPDATE_INTERVALS: Final = {
    "connection_check": timedelta(seconds=30),
    "power_state": timedelta(seconds=60),
    "device_info": timedelta(minutes=15),
    "network_info": timedelta(minutes=5),
}