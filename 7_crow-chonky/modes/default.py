"""
Default Mode - Standard Timed Operation
=====================================

This is the standard operating mode for the crow bird.
It checks conditions every INTERVAL_MINUTES and performs
appropriate actions based on light level and battery status.

This mode also contains the core light_rotate_hoot function
that other modes can import and use.

Actions:
- If light sufficient: full action sequence (eyes, servo, audio)
- If too dark: just flash eyes briefly
- If critical battery: minimal warning flash
"""

import time


def light_rotate_hoot(crow):
    """Main bird action sequence - light eyes, rotate head, make sounds
    
    This is the core bird action that can be used by any mode.
    
    Args:
        crow: CrowBird instance with all hardware components
    """
    print("🐦 Performing bird action sequence...")
    
    # Check battery level before intensive actions
    if crow.battery and crow.battery.is_critical_battery():
        print("⚠️ Critical battery - skipping action to preserve power")
        crow.leds.flash_eyes(times=5)
        return
    
    # Light up eyes
    crow.leds.fade_in()
    
    # Move to top and play sound
    crow.servo.to_top()
    crow.amplifier.play_wav()
    
    time.sleep(0.5)
    
    # Move to bottom and play sound
    crow.servo.to_bottom() 
    crow.amplifier.play_wav()
    
    time.sleep(0.5)
    
    # Return to center and fade out eyes
    crow.servo.to_midpoint()
    crow.leds.fade_out()
    
    print("Action sequence complete!")


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
        light_rotate_hoot(crow)
    else:
        print("🌙 Too dark - just flashing eyes")
        night_flashes = config["behavior"]["night_flash_count"]
        crow.leds.flash_eyes(times=night_flashes)
        
    print("=== Check Complete ===\n")


def run(crow, config):
    """Run default mode - continuous timed operation with low-power sleep"""
    print("🕐 Starting default mode - standard timed operation")
    
    interval_minutes = config.get("interval_minutes", 60)
    use_deep_sleep = config.get("use_deep_sleep", False)
    
    print(f"Checking every {interval_minutes} minutes")
    print(f"Deep sleep mode: {'enabled' if use_deep_sleep else 'disabled'}")
    
    # Check if we woke up from an alarm
    try:
        import alarm
        if alarm.wake_alarm:
            print("🔄 Woke up from deep sleep alarm")
        else:
            print("🚀 Cold boot - first startup")
    except ImportError:
        print("⚠️ alarm module not available - using regular sleep")
        use_deep_sleep = False
    
    # Perform timed actions (initial on startup, or after wake from sleep)
    timed_actions(crow, config)
    
    if use_deep_sleep:
        # Use deep sleep for maximum power savings
        try:
            import alarm
            
            # Clean up resources before sleeping
            print("🧹 Cleaning up before deep sleep...")
            crow.cleanup()
            
            # Calculate sleep time
            sleep_seconds = interval_minutes * 60
            print(f"😴 Entering deep sleep for {interval_minutes} minutes...")
            
            # Create time alarm
            time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_seconds)
            
            # Enter deep sleep (this will reset the microcontroller)
            alarm.exit_and_deep_sleep_until_alarms(time_alarm)
            
        except Exception as e:
            print(f"💥 Deep sleep error: {e}")
            print("Falling back to regular sleep")
            use_deep_sleep = False
    
    if not use_deep_sleep:
        # Fallback to regular sleep loop for compatibility
        print("🔄 Using regular sleep mode")
        
        # Main loop with regular sleep
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