# Android TV Box Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

**This component will set up the following platforms.**

Platform | Description
-- | --
`switch` | Control ADB connection, power state, and WiFi.

## Features

- **ADB Connection Control**: Monitor and manage ADB connection status
- **Power Management**: Turn Android TV Box on/off using ADB commands
- **WiFi Control**: Enable/disable WiFi (requires appropriate permissions)
- **Device Information**: Automatic detection of device model, Android version, brand
- **Real-time Status**: Live monitoring of connection and device states
- **Bilingual Support**: English and Chinese localization

## Requirements

- Android TV Box with ADB debugging enabled
- Network connectivity between Home Assistant and the Android device
- ADB port accessible (default: 5555)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the "+" button
4. Search for "Android TV Box"
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/android_tv_box` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "Android TV Box"

## Configuration

1. Go to Settings → Devices & Services → Add Integration
2. Search for "Android TV Box" and select it
3. Enter your Android TV Box details:
   - **IP Address**: The IP address of your Android TV Box
   - **ADB Port**: Usually 5555 (default)
   - **Device Name**: A friendly name for your device

## Setup ADB on Android TV Box

1. Enable Developer Options:
   - Go to Settings → About → Build number (tap 7 times)
2. Enable ADB Debugging:
   - Go to Settings → Developer Options → USB/ADB Debugging
3. Enable ADB over Network (if supported):
   - Go to Settings → Developer Options → ADB over Network
4. Note the IP address shown in network settings

## Entities

Once configured, the following entities will be available:

### Switch Entities

- `switch.{device_name}_adb_connection` - ADB connection status and control
- `switch.{device_name}_power` - Device power control
- `switch.{device_name}_wifi` - WiFi enable/disable control

Each switch provides additional attributes with detailed status information.

## Supported ADB Commands

The integration uses the following ADB commands:

- **Power Control**: `input keyevent 224` (wake), `input keyevent 26` (sleep)
- **WiFi Control**: `svc wifi enable/disable`
- **Status Queries**: `dumpsys power`, `dumpsys wifi`, `getprop`

## Troubleshooting

### Connection Issues

1. **ADB Connection Failed**:
   - Ensure ADB debugging is enabled
   - Check if the IP address and port are correct
   - Verify network connectivity
   - Try connecting manually: `adb connect <ip>:5555`

2. **Permission Denied**:
   - Some commands may require root access
   - WiFi control might not work on all devices

3. **Timeout Errors**:
   - Check network stability
   - Increase timeout in integration options
   - Verify ADB service is running on the device

### Logs

Enable debug logging for troubleshooting:

```yaml
logger:
  logs:
    custom_components.android_tv_box: debug
```

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Credits

This project was inspired by the comprehensive Android TV Box integration design document and follows Home Assistant best practices for custom integrations.

***

[android_tv_box]: https://github.com/bo/isg-android-service
[buymecoffee]: https://www.buymeacoffee.com/bo
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/bo/isg-android-service.svg?style=for-the-badge
[commits]: https://github.com/bo/isg-android-service/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/bo/isg-android-service.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40bo-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/bo/isg-android-service.svg?style=for-the-badge
[releases]: https://github.com/bo/isg-android-service/releases