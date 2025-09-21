#!/usr/bin/env python3
"""
Test script to verify the coordinator fix works.
"""

import asyncio
import sys
import logging
from unittest.mock import MagicMock

# Add the custom_components path
sys.path.insert(0, '/home/bo/.homeassistant/custom_components')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_coordinator_fix():
    """Test the coordinator initialization fix."""
    print("🧪 Testing Coordinator Data Initialization Fix")
    print("=" * 60)
    
    try:
        # Test imports
        print("1️⃣ Testing imports...")
        from android_tv_box.coordinator import AndroidTVBoxUpdateCoordinator, AndroidTVBoxData
        from android_tv_box.const import DOMAIN
        print(f"✅ Coordinator imported successfully")
        
        # Create mock objects
        class MockHass:
            def __init__(self):
                self.data = {}
                
        class MockConfigEntry:
            def __init__(self):
                self.data = {
                    "host": "192.168.188.221",
                    "port": 5555,
                    "device_name": "Test Android TV Box"
                }
                self.entry_id = "test_entry"
        
        hass = MockHass()
        config_entry = MockConfigEntry()
        
        print("2️⃣ Testing coordinator initialization...")
        coordinator = AndroidTVBoxUpdateCoordinator(hass, config_entry)
        
        # Check if data is properly initialized
        print(f"✅ Coordinator created")
        print(f"Data object: {type(coordinator.data)}")
        print(f"Data is not None: {coordinator.data is not None}")
        
        if coordinator.data is None:
            print("❌ Data is still None after initialization!")
            return False
        
        # Test data object methods
        print("3️⃣ Testing data object methods...")
        
        # Test update_device_info method
        test_device_info = {
            "model": "E3-DBB1",
            "android_version": "14", 
            "brand": "RockChip"
        }
        
        coordinator.data.update_device_info(test_device_info)
        print(f"✅ update_device_info method works")
        print(f"Device model: {coordinator.data.device_model}")
        
        # Test other methods
        coordinator.data.update_connection_status(True)
        print(f"✅ update_connection_status method works")
        
        wifi_info = {
            "enabled": True,
            "connected": True,
            "ssid": "Test_WiFi",
            "ip_address": "192.168.1.100"
        }
        coordinator.data.update_wifi_info(wifi_info)
        print(f"✅ update_wifi_info method works")
        
        print("4️⃣ Testing async_setup method...")
        setup_result = await coordinator.async_setup()
        print(f"✅ async_setup completed: {setup_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test."""
    print("🚀 Coordinator Fix Test Suite")
    print("=" * 60)
    
    success = await test_coordinator_fix()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Coordinator fix test passed!")
        print("The coordinator data initialization issue should be resolved.")
    else:
        print("❌ Coordinator fix test failed!")
        print("Check the errors above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))