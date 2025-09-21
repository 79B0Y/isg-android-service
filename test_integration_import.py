#!/usr/bin/env python3
"""
Test script to verify the Android TV Box integration can be imported correctly.
This helps diagnose 500 errors during config flow loading.
"""

import sys
import traceback

def test_imports():
    """Test all integration imports."""
    print("🔍 Testing Android TV Box integration imports...")
    print("=" * 60)
    
    try:
        print("1️⃣ Testing basic imports...")
        import asyncio
        import logging
        from typing import Any, Dict, Optional
        print("✅ Basic Python imports successful")
        
        print("\n2️⃣ Testing ADB library imports...")
        try:
            from adb_shell.adb_device import AdbDeviceTcp
            from adb_shell.exceptions import TcpTimeoutException
            print("✅ ADB library imports successful")
        except ImportError as e:
            print(f"❌ ADB library import failed: {e}")
            print("Please install: pip install adb-shell>=0.4.4")
            return False
        
        print("\n3️⃣ Testing integration constants...")
        from custom_components.android_tv_box.const import (
            DOMAIN, DEFAULT_PORT, DEFAULT_NAME, ADB_COMMANDS
        )
        print(f"✅ Constants loaded - Domain: {DOMAIN}")
        
        print("\n4️⃣ Testing ADB manager...")
        from custom_components.android_tv_box.adb_manager import ADBManager
        print("✅ ADB manager import successful")
        
        print("\n5️⃣ Testing coordinator...")
        from custom_components.android_tv_box.coordinator import AndroidTVBoxUpdateCoordinator
        print("✅ Coordinator import successful")
        
        print("\n6️⃣ Testing config flow...")
        from custom_components.android_tv_box.config_flow import (
            AndroidTVBoxConfigFlow, validate_input
        )
        print("✅ Config flow import successful")
        
        print("\n7️⃣ Testing switch platform...")
        from custom_components.android_tv_box.switch import (
            AndroidTVBoxADBConnectionSwitch,
            AndroidTVBoxPowerSwitch,
            AndroidTVBoxWiFiSwitch
        )
        print("✅ Switch platform import successful")
        
        print("\n8️⃣ Testing main init module...")
        from custom_components.android_tv_box import (
            async_setup_entry, async_unload_entry
        )
        print("✅ Main init module import successful")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic functionality without actual connections."""
    print("\n🧪 Testing basic functionality...")
    print("=" * 60)
    
    try:
        from custom_components.android_tv_box.adb_manager import ADBManager
        
        # Test manager creation
        manager = ADBManager("192.168.1.100", 5555)
        print(f"✅ ADB manager created for {manager.device_id}")
        
        from custom_components.android_tv_box.const import ADB_COMMANDS
        print(f"✅ Found {len(ADB_COMMANDS)} ADB commands")
        
        print("✅ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Android TV Box Integration Test Suite")
    print("=" * 60)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test basic functionality if imports work
    if success:
        if not test_basic_functionality():
            success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed! Integration should load correctly in Home Assistant.")
        print("If you still get 500 errors, check Home Assistant logs for more details.")
    else:
        print("❌ Tests failed! Please fix the issues above before using in Home Assistant.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())