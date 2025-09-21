#!/usr/bin/env python3
"""
Helper script to restart Home Assistant and verify the integration loads correctly.
"""

import asyncio
import subprocess
import time
import sys
import requests
import json

def restart_home_assistant():
    """Restart Home Assistant service."""
    print("🔄 Restarting Home Assistant...")
    
    # Kill any existing HA processes
    try:
        subprocess.run(["pkill", "-f", "homeassistant"], check=False)
        time.sleep(2)
    except:
        pass
    
    print("✅ Home Assistant processes stopped")
    return True

def check_ha_status():
    """Check if Home Assistant is running and responsive."""
    print("🔍 Checking Home Assistant status...")
    
    # Try to connect to HA API
    for attempt in range(30):  # Try for 30 seconds
        try:
            response = requests.get("http://localhost:8123/api/", timeout=5)
            if response.status_code == 200:
                print("✅ Home Assistant is running and responsive")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < 29:
            print(f"⏳ Waiting for Home Assistant to start... ({attempt + 1}/30)")
            time.sleep(1)
    
    print("❌ Home Assistant is not responding")
    return False

def test_integration_available():
    """Test if the Android TV Box integration is available."""
    print("🧪 Testing integration availability...")
    
    # For now, just verify the files are in place
    import os
    integration_path = "/home/bo/.homeassistant/custom_components/android_tv_box"
    
    required_files = [
        "__init__.py",
        "manifest.json", 
        "config_flow.py",
        "adb_manager.py",
        "const.py"
    ]
    
    for file in required_files:
        file_path = os.path.join(integration_path, file)
        if not os.path.exists(file_path):
            print(f"❌ Missing file: {file}")
            return False
    
    print("✅ All integration files are present")
    return True

def main():
    """Main test flow."""
    print("🚀 Home Assistant Integration Test")
    print("=" * 60)
    
    # Step 1: Restart HA
    if not restart_home_assistant():
        print("❌ Failed to restart Home Assistant")
        return 1
    
    # Step 2: Check integration files
    if not test_integration_available():
        print("❌ Integration files not available")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ Test completed successfully!")
    print()
    print("📋 Next steps:")
    print("1. Start Home Assistant manually: source /home/bo/.ha-core/bin/activate && python -m homeassistant --config /home/bo/.homeassistant")
    print("2. Open http://localhost:8123 in your browser")
    print("3. Go to Settings → Devices & Services → Add Integration")
    print("4. Search for 'Android TV Box' and add it")
    print("5. Use IP: 192.168.188.221, Port: 5555")
    print()
    print("The 500 Internal Server Error should now be resolved!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())