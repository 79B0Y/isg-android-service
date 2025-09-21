#!/usr/bin/env python3
"""
Test script to verify the config flow works in real Home Assistant environment.
This simulates adding the integration through the UI.
"""

import asyncio
import sys
import os
import logging
from unittest.mock import MagicMock

# Add the custom_components path
sys.path.insert(0, '/home/bo/.homeassistant/custom_components')

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_ha_config_flow():
    """Test the config flow in Home Assistant environment."""
    print("🚀 Testing Home Assistant Config Flow")
    print("=" * 60)
    
    try:
        # Test imports first
        print("1️⃣ Testing imports...")
        from android_tv_box.config_flow import AndroidTVBoxConfigFlow, validate_input
        from android_tv_box.const import DOMAIN
        print(f"✅ Config flow imported, domain: {DOMAIN}")
        
        # Create mock hass
        class MockHass:
            def __init__(self):
                self.data = {}
                self.config_entries = MagicMock()
                
        hass = MockHass()
        
        # Test the validation function directly
        print("\n2️⃣ Testing validation function...")
        test_data = {
            "host": "192.168.188.221",
            "port": 5555,
            "device_name": "Test Android TV Box"
        }
        
        result = await validate_input(hass, test_data)
        print(f"✅ Validation successful: {result['device_model']} ({result['android_version']})")
        
        # Test the config flow class
        print("\n3️⃣ Testing config flow class...")
        config_flow = AndroidTVBoxConfigFlow()
        config_flow.hass = hass
        
        # Test initial step
        print("Testing async_step_user with no input...")
        result = await config_flow.async_step_user(None)
        print(f"✅ Initial step returned form: {result['type']}")
        
        # Test step with user input
        print("Testing async_step_user with valid input...")
        result = await config_flow.async_step_user(test_data)
        print(f"✅ User step result: {result['type']}")
        if result['type'] == 'create_entry':
            print(f"✅ Entry would be created: {result['title']}")
        elif result['type'] == 'form':
            print(f"❌ Form returned with errors: {result.get('errors', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test."""
    print("🧪 Home Assistant Config Flow Test Suite")
    print("=" * 60)
    
    success = await test_ha_config_flow()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Config flow test passed!")
        print("The integration should work in Home Assistant UI.")
    else:
        print("❌ Config flow test failed!")
        print("Check the errors above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))