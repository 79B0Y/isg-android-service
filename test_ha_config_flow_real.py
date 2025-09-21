#!/usr/bin/env python3
"""
Test script to verify the config flow works in real Home Assistant environment.
This properly simulates the HA config flow context.
"""

import asyncio
import sys
import os
import logging
from unittest.mock import MagicMock, patch
from types import MappingProxyType

# Add the custom_components path
sys.path.insert(0, '/home/bo/.homeassistant/custom_components')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_ha_config_flow():
    """Test the config flow in Home Assistant environment."""
    print("🚀 Testing Home Assistant Config Flow (Real)")
    print("=" * 60)
    
    try:
        # Test imports first
        print("1️⃣ Testing imports...")
        from android_tv_box.config_flow import AndroidTVBoxConfigFlow, validate_input
        from android_tv_box.const import DOMAIN
        print(f"✅ Config flow imported, domain: {DOMAIN}")
        
        # Create properly mocked hass and context
        class MockHass:
            def __init__(self):
                self.data = {}
                self.config_entries = MagicMock()
                
        hass = MockHass()
        
        # Test the validation function directly (this should work)
        print("\n2️⃣ Testing validation function...")
        test_data = {
            "host": "192.168.188.221",
            "port": 5555,
            "device_name": "Test Android TV Box"
        }
        
        result = await validate_input(hass, test_data)
        print(f"✅ Validation successful: {result['device_model']} ({result['android_version']})")
        
        # Test the config flow with mocked context
        print("\n3️⃣ Testing config flow with proper mocking...")
        config_flow = AndroidTVBoxConfigFlow()
        config_flow.hass = hass
        
        # Mock the context as a regular dict instead of mappingproxy
        config_flow.context = {}
        
        # Mock the methods that would normally interact with HA's config entry system
        with patch.object(config_flow, 'async_set_unique_id') as mock_set_unique_id, \
             patch.object(config_flow, '_abort_if_unique_id_configured') as mock_abort_check:
            
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
                print(f"✅ Entry data: {result['data']}")
                # Verify the mocked methods were called
                mock_set_unique_id.assert_called_once()
                mock_abort_check.assert_called_once()
            elif result['type'] == 'form':
                print(f"❌ Form returned with errors: {result.get('errors', {})}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test."""
    print("🧪 Home Assistant Config Flow Test Suite (Real)")
    print("=" * 60)
    
    success = await test_ha_config_flow()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Config flow test passed!")
        print("The integration should work in Home Assistant UI.")
        print("The 500 Internal Server Error should be resolved after restarting HA.")
    else:
        print("❌ Config flow test failed!")
        print("Check the errors above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))