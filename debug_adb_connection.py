#!/usr/bin/env python3
"""
Debug script for Android TV Box ADB connection issues.
Run this script to diagnose connection problems before setting up the integration.

Usage:
    python debug_adb_connection.py 192.168.188.221 5555
"""

import asyncio
import sys
import logging
from custom_components.android_tv_box.adb_manager import ADBManager

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    if len(sys.argv) != 3:
        print("Usage: python debug_adb_connection.py <host> <port>")
        print("Example: python debug_adb_connection.py 192.168.188.221 5555")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    
    print(f"🔍 Debugging ADB connection to {host}:{port}")
    print("=" * 60)
    
    # Create ADB manager with extended timeout
    adb_manager = ADBManager(host, port, timeout=30)
    
    try:
        print(f"📱 Testing connection to Android TV Box at {host}:{port}")
        
        # Step 1: Basic connection test
        print("\n1️⃣ Testing basic ADB connection...")
        connected = await adb_manager.connect()
        
        if connected:
            print(f"✅ Basic connection successful!")
        else:
            print(f"❌ Basic connection failed!")
            return
        
        # Step 2: Comprehensive connection test
        print("\n2️⃣ Running comprehensive connection test...")
        test_result = await adb_manager.test_adb_connection()
        
        print(f"Connection Status: {'✅ Connected' if test_result['connected'] else '❌ Failed'}")
        
        if test_result.get('error'):
            print(f"Error: {test_result['error']}")
        
        # Display connection details
        details = test_result.get('connection_details', {})
        if details:
            print(f"Connection Time: {details.get('connection_time', 'N/A')} seconds")
            print(f"Shell Test: {details.get('shell_test', 'N/A')}")
            
            if 'device_info_error' in details:
                print(f"Device Info Error: {details['device_info_error']}")
            if 'power_error' in details:
                print(f"Power Check Error: {details['power_error']}")
            if 'wifi_error' in details:
                print(f"WiFi Check Error: {details['wifi_error']}")
        
        # Step 3: Device information
        print("\n3️⃣ Device Information:")
        device_info = test_result.get('device_info', {})
        if device_info:
            print(f"Model: {device_info.get('model', 'Unknown')}")
            print(f"Brand: {device_info.get('brand', 'Unknown')}")
            print(f"Android Version: {device_info.get('android_version', 'Unknown')}")
        else:
            print("❌ No device information available")
        
        # Step 4: Status checks
        print(f"\n4️⃣ Device Status:")
        print(f"Power State: {test_result.get('power_state', 'Unknown')}")
        print(f"WiFi Enabled: {test_result.get('wifi_enabled', 'Unknown')}")
        
        # Step 5: WiFi details
        wifi_info = details.get('wifi_info', {})
        if wifi_info:
            print(f"WiFi Connected: {wifi_info.get('connected', 'Unknown')}")
            print(f"WiFi SSID: {wifi_info.get('ssid', 'N/A')}")
            print(f"IP Address: {wifi_info.get('ip_address', 'N/A')}")
        
        print(f"\n🎉 Connection test completed successfully!")
        print(f"✅ Your Android TV Box should work with Home Assistant")
        
    except Exception as e:
        print(f"\n❌ Connection test failed with error:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        
        # Provide troubleshooting suggestions
        print(f"\n🔧 Troubleshooting suggestions:")
        if "timeout" in str(e).lower():
            print("- Check if the IP address is correct")
            print("- Verify the device is powered on")
            print("- Check network connectivity")
            print("- Try connecting with system adb command first")
        elif "refused" in str(e).lower():
            print("- Enable ADB debugging in Developer Options")
            print("- Enable 'ADB over network' if available")
            print("- Check if port 5555 is open")
        else:
            print("- Check Home Assistant logs for more details")
            print("- Verify ADB dependencies are installed")
    
    finally:
        # Cleanup
        try:
            await adb_manager.disconnect()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())