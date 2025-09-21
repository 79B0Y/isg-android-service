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
    "check_adb_version": "getprop ro.adb.secure",
    "list_properties": "getprop | head -10",
    "check_network": "ping -c 1 8.8.8.8",
    "check_services": "service list | head -5",
}

# ADB Commands for device state queries
ADB_COMMANDS: Final = {
    # Connection status
    "check_connection": "echo 'connected'",
    
    # Power state commands
    "power_state": "dumpsys power | grep -E '(mWakefulness|mScreenOn)'",
    
    # Network status
    "wifi_state": "settings get global wifi_on",
    "wifi_ssid": "dumpsys wifi | grep 'SSID:' | head -1",
    "ip_address": "ip addr show wlan0 | grep 'inet '",
    
    # Device info
    "device_model": "getprop ro.product.model",
    "android_version": "getprop ro.build.version.release",
    "device_brand": "getprop ro.product.brand",
}

# ADB Control Commands
ADB_CONTROL_COMMANDS: Final = {
    # Power control
    "power_on": "input keyevent 224",  # KEYCODE_WAKEUP
    "power_off": "input keyevent 26",  # KEYCODE_POWER
    
    # WiFi control (requires root or system permissions)
    "wifi_enable": "svc wifi enable",
    "wifi_disable": "svc wifi disable",
}

# Entity unique ID suffixes
ENTITY_SUFFIXES: Final = {
    "adb_connection": "adb_connection",
    "power": "power",
    "wifi": "wifi",
}

# Button unique ID suffixes
BUTTON_SUFFIXES: Final = {
    # Navigation
    "nav_up": "btn_nav_up",
    "nav_down": "btn_nav_down",
    "nav_left": "btn_nav_left",
    "nav_right": "btn_nav_right",
    "nav_select": "btn_nav_select",
    "nav_back": "btn_nav_back",
    "nav_home": "btn_nav_home",
    "nav_menu": "btn_nav_menu",
    # Actions
    "restart_isg": "btn_restart_isg",
    "refresh_apps": "btn_refresh_apps",
    "reboot_device": "btn_reboot_device",
    "screenshot": "btn_screenshot",
}

# Android keycodes for navigation
ANDROID_KEYCODES: Final = {
    "UP": 19,
    "DOWN": 20,
    "LEFT": 21,
    "RIGHT": 22,
    "CENTER": 23,  # DPAD_CENTER (OK)
    "BACK": 4,
    "HOME": 3,
    "MENU": 82,
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

# Camera / Screenshot settings
SCREENSHOT_DIR: Final = "/home/bo/.homeassistant/www/screenshots"
SCREENSHOT_RETAIN: Final = 10  # keep last N screenshots locally

# Options keys for config entry
OPT_SCREENSHOT_DIR: Final = "screenshot_dir"
OPT_SCREENSHOT_RETAIN: Final = "screenshot_retain"
