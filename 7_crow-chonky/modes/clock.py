"""
Clock Mode - Hourly Chime with Button Control
=============================================

This mode provides clock functionality with hourly chiming.
The bird chimes 1-12 times based on the current hour setting.

Button Controls:
- Short press: Advance hour by 1 (cycles 1-12)
- Long press: Cycle to next mode (handled by main system)

Features:
- Manual hour setting via button
- Hourly chime sequence with movement and sound
- Quiet hours support (reduced volume/movement)
- Light-sensitive operation
- Battery-aware operation
"""

import time


# Global state for clock mode
clock_state = {
    "current_hour": 12,
    "last_chime_time": 0,
    "initialized": False
}


def init(crow, config):
    """Initialize clock mode"""
    global clock_state
    
    print("🕐 Clock mode initializing...")
    
    # Reset state
    clock_state["current_hour"] = 12
    clock_state["last_chime_time"] = 0
    clock_state["initialized"] = True
    
    # Flash LEDs to show current hour
    flash_hour_confirmation(crow, clock_state["current_hour"])
    
    print(f"✅ Clock mode ready - hour set to {clock_state['current_hour']}")


def run(crow, config):
    """Run clock mode - wait for chime times and handle timing"""
    global clock_state
    
    print("🕐 Starting clock mode - hourly chime operation")
    
    # Make sure we're initialized
    if not clock_state["initialized"]:
        init(crow, config)
    
    # Get configuration
    chime_interval = config.get("clock_chime_interval_minutes", 60)  # Default hourly
    test_mode = config.get("debug", False)
    test_interval = 30 if test_mode else (chime_interval * 60)  # 30 seconds for testing
    
    if test_mode:
        print(f"🧪 DEBUG MODE: Chiming every {test_interval} seconds instead of {chime_interval} minutes")
    else:
        print(f"🕐 Chiming every {chime_interval} minutes")
    
    print(f"Current hour setting: {clock_state['current_hour']}")
    print("Press button to advance hour manually")
    print("=" * 50)
    
    try:
        start_time = time.monotonic()
        last_status_time = 0
        
        while True:
            current_time = time.monotonic()
            
            # Check if it's time to chime
            time_since_last_chime = current_time - clock_state["last_chime_time"]
            
            if time_since_last_chime >= test_interval:
                print(f"\n🔔 Chime time! ({test_interval} seconds elapsed)")
                perform_hourly_chime(crow, config)
                clock_state["last_chime_time"] = current_time
            
            # Status update every 10 seconds
            if current_time - last_status_time >= 10:
                time_until_chime = test_interval - time_since_last_chime
                print(f"🕐 Hour: {clock_state['current_hour']}, Next chime in: {time_until_chime:.0f}s")
                last_status_time = current_time
            
            # Small delay for responsiveness
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n🛑 Clock mode interrupted")
    except Exception as e:
        print(f"💥 Error in clock mode: {e}")
        # Flash error pattern
        try:
            crow.leds.flash_eyes(times=10)
        except:
            pass


def button_pressed(crow, config):
    """Handle short button press - advance hour by 1"""
    global clock_state
    
    clock_state["current_hour"] += 1
    if clock_state["current_hour"] > 12:
        clock_state["current_hour"] = 1
        
    print(f"🕐 Hour advanced to {clock_state['current_hour']}")
    
    # Flash eyes to show current hour
    flash_hour_confirmation(crow, clock_state["current_hour"])
    
    # Optional: Also chime the new hour immediately
    immediate_chime = config.get("clock_button_immediate_chime", False)
    if immediate_chime:
        print("🔔 Chiming new hour immediately...")
        perform_hourly_chime(crow, config)


def flash_hour_confirmation(crow, hour):
    """Flash eyes the number of times corresponding to hour"""
    print(f"💡 Flashing {hour} times for hour {hour}")
    
    for i in range(hour):
        crow.leds.set_brightness(0.6)
        time.sleep(0.25)
        crow.leds.turn_off()
        time.sleep(0.25)
        
    print(f"✅ Hour {hour} confirmed")


def is_quiet_hours(config):
    """Check if we're in quiet hours based on configuration"""
    quiet_start = config.get("clock", {}).get("quiet_hours_start", 23)
    quiet_end = config.get("clock", {}).get("quiet_hours_end", 7)
    
    # For now, return False since we don't have real time
    # In a real implementation, you'd check the actual time
    return False


def perform_hourly_chime(crow, config):
    """Perform the hourly chime sequence"""
    global clock_state
    
    hour = clock_state["current_hour"]
    print(f"🕐 CHIMING HOUR {hour}")
    
    # Check conditions first
    light_sufficient, condition = crow.check_conditions()
    chime_volume = config.get("clock", {}).get("chime_volume", 0.7)
    quiet_hours = is_quiet_hours(config)
    
    if condition == "critical_battery":
        print("⚠️ Critical battery - performing minimal chime")
        crow.leds.flash_eyes(times=3)
        return
    
    if quiet_hours:
        print("🌙 Quiet hours - reduced chime")
        chime_volume *= 0.5  # Reduce volume
        
        # Just audio caws with dimmed LEDs
        crow.leds.set_brightness(0.2)
        for i in range(hour):
            print(f"  Quiet caw {i+1}/{hour}")
            crow.amplifier.set_volume(chime_volume)
            crow.amplifier.play_wav()
            time.sleep(0.6)
        crow.leds.turn_off()
        return
        
    if not light_sufficient:
        print("🌙 Too dark - performing quiet chime")
        # Just audio caws
        for i in range(hour):
            print(f"  Dark caw {i+1}/{hour}")
            crow.amplifier.set_volume(chime_volume)
            crow.amplifier.play_wav()
            time.sleep(0.8)
        return
    
    # Full chime sequence
    print("🎭 Performing full chime sequence")
    
    # Set chime volume
    crow.amplifier.set_volume(chime_volume)
    
    # Light up eyes
    crow.leds.fade_in()
    
    # Perform the hour caws with movement
    for i in range(hour):
        print(f"  Caw {i+1}/{hour}")
        
        # Alternate servo positions for visual interest
        if i % 2 == 0:
            crow.servo.to_top()
        else:
            crow.servo.to_bottom()
            
        # Play caw sound
        crow.amplifier.play_wav()
        time.sleep(0.8)
    
    # Return to center and fade out
    crow.servo.to_midpoint()
    time.sleep(0.5)
    crow.leds.fade_out()
    
    print(f"✅ Chimed {hour} times")
    
    # Reset volume to normal
    crow.amplifier.set_volume(config["audio"]["volume"])


def cleanup(crow, config):
    """Clean up when leaving clock mode"""
    global clock_state
    
    print("🧹 Clock mode cleaning up...")
    
    # Turn off LEDs
    crow.leds.turn_off()
    
    # Stop any audio
    crow.amplifier.stop()
    
    # Return servo to center
    crow.servo.to_midpoint()
    
    # Reset volume
    crow.amplifier.set_volume(config["audio"]["volume"])
    
    print("✅ Clock mode cleanup complete")


# Utility functions for clock mode
def set_hour(hour):
    """Manually set the hour (1-12)"""
    global clock_state
    
    if 1 <= hour <= 12:
        clock_state["current_hour"] = hour
        print(f"🕐 Hour set to {hour}")
        return True
    else:
        print(f"❌ Invalid hour: {hour} (must be 1-12)")
        return False


def get_current_hour():
    """Get the current hour setting"""
    return clock_state["current_hour"]


def force_chime(crow, config):
    """Force an immediate chime (useful for testing)"""
    print("🔔 Forcing immediate chime...")
    perform_hourly_chime(crow, config)


if __name__ == "__main__":
    print("Clock mode loaded successfully")
    print(f"Current hour: {get_current_hour()}")