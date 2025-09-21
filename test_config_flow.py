#!/usr/bin/env python3
"""
Test script to verify the config flow validation works correctly.
This simulates what happens when adding the integration in Home Assistant.
"""

import asyncio
import sys
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_config_flow_validation():
    """Test the config flow validation function directly."""
    print("🧪 Testing Config Flow Validation")
    print("=" * 60)
    
    try:
        # Import the validation function
        from custom_components.android_tv_box.config_flow import validate_input
        
        # Create a mock HomeAssistant object (minimal implementation)
        class MockHass:
            pass
        
        hass = MockHass()
        
        # Test data (same as what would come from the UI)
        test_data = {
            "host": "192.168.188.221",
            "port": 5555,
            "device_name": "Test Android TV Box"
        }
        
        print(f"📱 Testing validation with:")
        print(f"   Host: {test_data['host']}")
        print(f"   Port: {test_data['port']}")
        print(f"   Device Name: {test_data['device_name']}")
        print()
        
        # Run the validation
        print("🔍 Running config flow validation...")
        result = await validate_input(hass, test_data)
        
        print("✅ Validation successful!")
        print(f"Title: {result['title']}")
        print(f"Host: {result['host']}")
        print(f"Port: {result['port']}")
        print(f"Device Name: {result['device_name']}")
        print(f"Device Model: {result['device_model']}")
        print(f"Android Version: {result['android_version']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the config flow test."""
    print("🚀 Config Flow Validation Test")
    print("=" * 60)
    
    success = await test_config_flow_validation()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Config flow validation test passed!")
        print("The integration should work correctly in Home Assistant.")
    else:
        print("❌ Config flow validation test failed!")
        print("Please check the errors above before using in Home Assistant.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))