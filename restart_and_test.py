#!/usr/bin/env python3
"""
Script to restart Home Assistant and monitor for coordinator errors.
"""

import subprocess
import time
import sys

def stop_ha():
    """Stop Home Assistant processes."""
    print("🛑 Stopping Home Assistant...")
    try:
        subprocess.run(["pkill", "-f", "homeassistant"], check=False)
        time.sleep(3)
        print("✅ Home Assistant stopped")
        return True
    except Exception as e:
        print(f"⚠️ Error stopping HA: {e}")
        return False

def clear_logs():
    """Clear the HA log file to start fresh."""
    print("🧹 Clearing logs...")
    try:
        with open("/home/bo/.homeassistant/home-assistant.log", "w") as f:
            f.write("")
        print("✅ Logs cleared")
        return True
    except Exception as e:
        print(f"⚠️ Error clearing logs: {e}")
        return False

def start_ha_background():
    """Start Home Assistant in background."""
    print("🚀 Starting Home Assistant in background...")
    try:
        # Start HA in background and redirect output to a file
        with open("/tmp/ha_startup.log", "w") as f:
            subprocess.Popen([
                "/bin/bash", "-c",
                "source /home/bo/.ha-core/bin/activate && hass -c /home/bo/.homeassistant"
            ], stdout=f, stderr=subprocess.STDOUT)
        
        print("✅ Home Assistant starting in background...")
        return True
    except Exception as e:
        print(f"❌ Error starting HA: {e}")
        return False

def monitor_logs():
    """Monitor HA logs for coordinator errors."""
    print("👀 Monitoring logs for coordinator errors...")
    print("Looking for 'android_tv_box' related messages...")
    print("Press Ctrl+C to stop monitoring")
    print("-" * 60)
    
    try:
        # Monitor the log file for 60 seconds
        start_time = time.time()
        last_position = 0
        
        while time.time() - start_time < 60:
            try:
                with open("/home/bo/.homeassistant/home-assistant.log", "r") as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    last_position = f.tell()
                    
                    for line in new_lines:
                        line = line.strip()
                        if "android_tv_box" in line.lower():
                            # Color code the output
                            if "error" in line.lower():
                                print(f"🔴 {line}")
                            elif "warning" in line.lower():
                                print(f"🟡 {line}")
                            elif "info" in line.lower():
                                print(f"🟢 {line}")
                            else:
                                print(f"ℹ️  {line}")
                
                time.sleep(1)
                
            except FileNotFoundError:
                time.sleep(1)
                continue
        
        print("\n" + "-" * 60)
        print("⏰ Monitoring completed (60 seconds)")
        
    except KeyboardInterrupt:
        print("\n" + "-" * 60)
        print("⏹️ Monitoring stopped by user")

def main():
    """Main function."""
    print("🧪 Home Assistant Coordinator Fix Test")
    print("=" * 60)
    
    # Step 1: Stop HA
    if not stop_ha():
        return 1
    
    # Step 2: Clear logs  
    if not clear_logs():
        return 1
    
    # Step 3: Start HA in background
    if not start_ha_background():
        return 1
    
    # Step 4: Wait a bit for startup
    print("⏳ Waiting 10 seconds for initial startup...")
    time.sleep(10)
    
    # Step 5: Monitor logs
    monitor_logs()
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print()
    print("📋 What to look for:")
    print("- 🟢 INFO messages about coordinator setup")
    print("- 🔴 No ERROR messages about 'NoneType' or 'update_device_info'")
    print("- 🟢 Successful integration loading")
    print()
    print("If you see coordinator setup success, the fix worked!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
