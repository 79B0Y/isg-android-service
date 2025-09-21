#!/usr/bin/env python3
"""
Simple test to verify AndroidTVBoxData class works correctly.
"""

import sys

# Add the custom_components path
sys.path.insert(0, '/home/bo/.homeassistant/custom_components')

def test_data_class():
    """Test the AndroidTVBoxData class."""
    print("🧪 Testing AndroidTVBoxData Class")
    print("=" * 60)
    
    try:
        # Test imports
        print("1️⃣ Testing import...")
        from android_tv_box.coordinator import AndroidTVBoxData
        print("✅ AndroidTVBoxData imported successfully")
        
        # Test data class initialization
        print("2️⃣ Testing data class initialization...")
        data = AndroidTVBoxData()
        print(f"✅ Data object created: {type(data)}")
        
        # Test methods exist and work
        print("3️⃣ Testing data class methods...")
        
        # Test update_device_info
        device_info = {
            "model": "E3-DBB1",
            "android_version": "14",
            "brand": "RockChip"
        }
        data.update_device_info(device_info)
        print(f"✅ update_device_info works - Model: {data.device_model}")
        
        # Test update_connection_status
        data.update_connection_status(True)
        print(f"✅ update_connection_status works - Connected: {data.is_connected}")
        
        # Test update_wifi_state
        wifi_info = {
            "enabled": True,
            "connected": True,
            "ssid": "Test_WiFi",
            "ip_address": "192.168.1.100"
        }
        data.update_wifi_state(wifi_info)
        print(f"✅ update_wifi_state works - SSID: {data.wifi_ssid}")
        
        # Test property
        device_dict = data.device_info_dict
        print(f"✅ device_info_dict property works - Keys: {list(device_dict.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    print("🚀 AndroidTVBoxData Class Test")
    print("=" * 60)
    
    success = test_data_class()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Data class test passed!")
        print("The AndroidTVBoxData class is working correctly.")
        print("The coordinator should now be able to use this data object.")
    else:
        print("❌ Data class test failed!")
        print("Check the errors above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())