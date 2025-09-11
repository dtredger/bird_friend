"""
Default Mode - Standard Timed Operation
=====================================

This is the standard operating mode for the crow bird.
It checks conditions every INTERVAL_MINUTES and performs
appropriate actions based on light level and battery status.

Actions:
- If light sufficient: full action sequence (eyes, servo, audio)
- If too dark: just flash eyes briefly
- If critical battery: minimal warning flash
"""

import time


def timed_actions(crow, config):
    """Check conditions and perform appropriate action"""
    print(f"\n=== Timed Action Check ===")
    print(f"Time: {time.localtime()}")
    
    # Check conditions (light level, battery)
    light_sufficient, condition = crow.check_conditions()
    
    if condition == "critical_battery":
        print("⚠️ Critical battery - performing warning flash only")
        crow.leds.flash_eyes(times=5)
    elif light_sufficient:
        print("✅ Conditions good - performing full action")
        crow.light_rotate_hoot()
    else:
        print("🌙 Too dark - just flashing eyes")
        night_flashes = config["behavior"]["night_flash_count"]
        crow.leds.flash_eyes(times=night_flashes)
        
    print("=== Check Complete ===\n")


def run(crow, config):
    """Run default mode - continuous timed operation"""
    print("🕐 Starting default mode - standard timed operation")
    
    interval_minutes = config.get("interval_minutes", 60)
    print(f"Checking every {interval_minutes} minutes")
    
    # Initial action on startup
    timed_actions(crow, config)
    
    # Main loop
    while True:
        try:
            # Sleep for the specified interval
            sleep_seconds = interval_minutes * 60
            print(f"😴 Sleeping for {interval_minutes} minutes...")
            time.sleep(sleep_seconds)
            
            # Perform timed actions
            timed_actions(crow, config)
            
        except KeyboardInterrupt:
            print("\n🛑 default mode interrupted")
            break
        except Exception as e:
            print(f"💥 Error in default mode: {e}")
            # Flash eyes to indicate error
            crow.leds.flash_eyes(times=5)
            time.sleep(5)  # Wait before retrying