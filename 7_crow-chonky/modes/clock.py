"""
Simplified Clock Mode - For Debugging
====================================

This is a minimal version to help debug the "function doesn't take keyword arguments" error.
Save this as: 7_crow-chonky/modes/clock.py

Once this works, we can add back the full functionality.
"""

import time


class ClockMode:
    """Simplified clock functionality for debugging"""
    
    def __init__(self, crow, config):
        """Initialize clock mode"""
        self.crow = crow
        self.config = config
        self.current_hour = 12  # Default to 12 o'clock
        
        print(f"🕐 Clock mode initialized - hour set to {self.current_hour}")

    def handle_button_press(self):
        """Handle short button press - advance hour by 1"""
        self.current_hour += 1
        if self.current_hour > 12:
            self.current_hour = 1
            
        print(f"🕐 Hour advanced to {self.current_hour}")
        
        # Flash eyes to show current hour
        self.flash_hour_confirmation()

    def flash_hour_confirmation(self):
        """Flash eyes the number of times corresponding to current hour"""
        print(f"💡 Flashing {self.current_hour} times for hour {self.current_hour}")
        
        for i in range(self.current_hour):
            self.crow.leds.turn_on()
            time.sleep(0.3)
            self.crow.leds.turn_off()
            time.sleep(0.3)
            print(f"  Flash {i+1}/{self.current_hour}")

    def should_chime_now(self):
        """Simple test - chime every 30 seconds for testing"""
        current_time = time.monotonic()
        return int(current_time) % 30 == 0  # Every 30 seconds

    def perform_hourly_chime(self):
        """Perform the hourly chime sequence"""
        print(f"🕐 CHIMING HOUR {self.current_hour}")
        
        # Check conditions first
        light_sufficient, condition = self.crow.check_conditions()
        
        if condition == "critical_battery":
            print("⚠️ Critical battery - performing minimal chime")
            self.crow.leds.flash_eyes(times=3)
            return
            
        if not light_sufficient:
            print("🌙 Too dark - performing quiet chime")
            # Just audio caws
            for i in range(self.current_hour):
                print(f"  Quiet caw {i+1}/{self.current_hour}")
                self.crow.amplifier.play_wav()
                time.sleep(0.8)
            return
        
        # Full chime sequence
        print("🎭 Performing full chime sequence")
        
        # Light up eyes
        self.crow.leds.fade_in()
        
        # Perform the hour caws with movement
        for i in range(self.current_hour):
            print(f"  Caw {i+1}/{self.current_hour}")
            
            # Alternate servo positions
            if i % 2 == 0:
                self.crow.servo.to_top()
            else:
                self.crow.servo.to_bottom()
                
            # Play caw sound
            self.crow.amplifier.play_wav()
            time.sleep(0.8)
        
        # Return to center and fade out
        self.crow.servo.to_midpoint()
        time.sleep(0.5)
        self.crow.leds.fade_out()
        
        print(f"✅ Chimed {self.current_hour} times")


def run(crow, config):
    """Run clock mode - simplified version for debugging"""
    print("🕐 Starting simplified clock mode")
    print("📋 This is a debug version - should work without errors")
    
    try:
        # Create clock instance
        clock = ClockMode(crow, config)
        
        # Store clock instance so main system can call handle_button_press
        crow.mode_handler = clock
        
        # Show initial hour setting
        print(f"\n🕐 Initial hour setting: {clock.current_hour}")
        clock.flash_hour_confirmation()
        
        # Simple main loop for testing
        print("\n🔄 Starting simple test loop...")
        print("Press button to advance hour, wait for test chimes")
        
        last_check = time.monotonic()
        test_counter = 0
        
        while True:
            current_time = time.monotonic()
            
            # Test chime every 10 seconds for debugging
            if current_time - last_check >= 10.0:
                last_check = current_time
                test_counter += 1
                
                print(f"\n--- Test {test_counter} ---")
                if test_counter % 3 == 0:  # Every 30 seconds do a chime test
                    print("🔔 Testing chime sequence...")
                    clock.perform_hourly_chime()
                else:
                    print("⏰ Waiting... (press button to test hour advancement)")
                
            # Small delay to prevent excessive CPU usage
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n🛑 Clock mode interrupted")
    except Exception as e:
        print(f"💥 Error in clock mode: {e}")
        # Show the full error for debugging
        import traceback
        traceback.print_exc()
        
        # Flash error pattern
        try:
            for _ in range(5):
                crow.leds.turn_on()
                time.sleep(0.1)
                crow.leds.turn_off()
                time.sleep(0.1)
        except:
            pass


# Test function that can be called directly
def test_clock_basic():
    """Basic test function"""
    print("🧪 Basic clock test - this should not cause keyword argument errors")
    return True


if __name__ == "__main__":
    print("Clock mode debug version loaded")
    test_clock_basic()