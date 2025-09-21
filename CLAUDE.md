# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains documentation for an Android TV Box Home Assistant integration project. Currently, it only contains a comprehensive Chinese design document (`android_tv_integration_doc.md`) that outlines the complete architecture and implementation details for a Home Assistant Custom Component (HACS integration).

## Project Structure

The repository currently contains:
- `android_tv_integration_doc.md` - Comprehensive design document in Chinese that details:
  - Android TV Box integration architecture
  - ADB command mappings for media control, power management, navigation
  - Entity definitions (media player, switches, sensors, buttons, etc.)
  - ISG application monitoring module
  - Performance optimization strategies for Termux/Ubuntu environments
  - Configuration and deployment instructions
  - Troubleshooting guides

## Development Context

This appears to be a documentation-only repository for planning/designing an Android TV Box integration that would:

1. **Connect to Android TV devices via ADB** (Android Debug Bridge)
2. **Provide Home Assistant entities** for controlling:
   - Media playback (play/pause/volume/cast)
   - Power management (on/off/sleep)
   - Navigation (directional keys, home, back)
   - System monitoring (CPU, memory, network)
3. **Special ISG application monitoring** - monitors `com.linknlink.app.device.isg` application
4. **Performance optimizations** for low-resource environments like Termux/Ubuntu

## Implementation Status

This repository now contains a working implementation of the first phase of the Android TV Box integration:

### Completed Components

- **HACS Integration Structure** - Full `custom_components/android_tv_box/` directory
- **ADB Manager** (`adb_manager.py`) - Handles device connection and command execution
- **Update Coordinator** (`coordinator.py`) - Manages data updates and state synchronization
- **Config Flow** (`config_flow.py`) - Device setup and configuration UI
- **Switch Entities** (`switch.py`) - ADB connection, power, and WiFi controls
- **Localization** - English and Chinese translations

### Current Features

1. **ADB Connection Switch** - Monitor and control ADB connection status
2. **Power Switch** - Turn Android TV Box on/off via ADB keyevents
3. **WiFi Switch** - Enable/disable WiFi (requires appropriate permissions)
4. **Device Information** - Automatic detection of device model, Android version, brand
5. **Status Monitoring** - Real-time connection status and error tracking

### Integration Structure

```
custom_components/android_tv_box/
├── __init__.py              # Integration setup and platform loading
├── manifest.json            # HACS integration metadata
├── config_flow.py           # Device discovery and configuration
├── const.py                 # Constants and ADB command definitions
├── coordinator.py           # Data update coordinator
├── adb_manager.py           # ADB connection and command handling
├── switch.py                # Switch entities (ADB, power, WiFi)
├── strings.json             # UI strings
└── translations/            # Localization
    ├── en.json              # English translations
    └── zh.json              # Chinese translations
```

### Installation and Setup

1. Copy the `custom_components/android_tv_box/` directory to your Home Assistant config
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "Android TV Box" and configure with your device's IP and ADB port (usually 5555)
5. Ensure ADB debugging is enabled on your Android TV Box

### Next Steps for Full Implementation

1. Add media player entity for playback control
2. Implement camera entity for screenshots
3. Add sensor entities for system monitoring
4. Implement button entities for navigation
5. Add ISG application monitoring module
6. Implement number entity for brightness control
7. Add select entity for application switching

## Current Limitations

- Requires ADB debugging enabled on target device
- WiFi control may require root permissions on some devices
- Only basic switch controls implemented (first phase)
- No ISG monitoring yet (planned for next phase)