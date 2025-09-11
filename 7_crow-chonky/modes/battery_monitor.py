"""
Battery Monitor Mode - Ultra Low Power Monitoring
================================================

This mode demonstrates ultra-low power operation using deep sleep.
It wakes up periodically to check and log battery status, then
goes back to deep sleep without performing any intensive actions.

Perfect for long-term battery monitoring or when you want to
minimize power consumption while still tracking system health.

Actions:
- Check battery status
- Log to file
- Flash LED briefly to indicate operation
- Enter deep sleep for extended period
"""

import time
# Import the default mode to access core functionality if needed
import modes.default as default_mode


def log_battery_status(crow, config):
    """Check and log battery status with minimal power usage"""
    print("🔋 Checking battery status...")
    
    if crow.battery:
        status = crow.battery.get_status()
        
        # Log to file
        crow.battery.log_status()
        
        # Print status
        print(f"Battery: {status['voltage']}V ({status['percentage']}%) - {status['level']}")
        
        # Brief LED flash to indicate operation
        crow.leds.set_brightness(0.1)  # Very dim to save power
        time.sleep(0.2)
        crow.leds.turn_off()
        
        # Check for critical battery
        if status['level'] == 'critical':
            print("⚠️ CRITICAL BATTERY!")
            # Flash warning pattern
            for _ in range(5):
                crow.leds.set_brightness(0.3)
                time.sleep(0.1)
                crow.leds.turn_off()
                time.sleep(0.1)
        
        return status
    else:
        print("❌ Battery monitoring not available")
        # Brief flash to show we're alive
        crow.leds.set_brightness(0.1)
        time.sleep(0.1)
        crow.leds.turn_off()
        return None


def run(crow, config):
    """Run battery monitor mode - ultra low power monitoring"""
    print("🔋 Starting battery monitor mode - ultra low power operation")
    
    # Battery monitor specific settings
    monitor_interval = config.get("battery_monitor_interval_minutes", 30)  # Default 30 minutes
    force_deep_sleep = config.get("battery_monitor_force_deep_sleep", True)
    
    print(f"Battery check interval: {monitor_interval} minutes")
    print(f"Deep sleep: {'forced on' if force_deep_sleep else 'use config setting'}")
    
    # Check if we woke up from an alarm
    try:
        import alarm
        if alarm.wake_alarm:
            print("🔄 Woke up from deep sleep alarm")
        else:
            print("🚀 Cold boot - first startup")
    except ImportError:
        print("⚠️ alarm module not available")
        force_deep_sleep = False
    
    # Perform battery check
    battery_status = log_battery_status(crow, config)
    
    # Use deep sleep for maximum power savings
    use_deep_sleep = force_deep_sleep or config.get("use_deep_sleep", True)
    
    if use_deep_sleep:
        try:
            import alarm
            
            # Clean up resources before sleeping
            print("🧹 Cleaning up before deep sleep...")
            crow.cleanup()
            
            # Calculate sleep time
            sleep_seconds = monitor_interval * 60
            print(f"😴 Entering deep sleep for {monitor_interval} minutes...")
            
            # Create time alarm
            time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_seconds)
            
            # Enter deep sleep (this will reset the microcontroller)
            alarm.exit_and_deep_sleep_until_alarms(time_alarm)
            
        except Exception as e:
            print(f"💥 Deep sleep error: {e}")
            print("Falling back to regular sleep")
            use_deep_sleep = False
    
    if not use_deep_sleep:
        # Fallback to regular sleep
        print("🔄 Using regular sleep mode")
        
        while True:
            try:
                sleep_seconds = monitor_interval * 60
                print(f"😴 Regular sleep for {monitor_interval} minutes...")
                time.sleep(sleep_seconds)
                
                # Check battery again
                log_battery_status(crow, config)
                
            except KeyboardInterrupt:
                print("\n🛑 Battery monitor mode interrupted")
                break
            except Exception as e:
                print(f"💥 Error in battery monitor mode: {e}")
                time.sleep(30)  # Wait before retrying
