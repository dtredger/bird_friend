"""
Clock Mode - Hourly Chime (Simplified with BaseMode)
====================================================

This mode inherits from BaseMode and overrides just what it needs
for clock functionality. Gets all the button handling and infrastructure for free.

Button Controls:
- Short press: Advance hour by 1 (cycles 1-12)
- Long press: Cycle to next mode (handled globally)
"""

import time
from base_mode import BaseMode


class ClockMode(BaseMode):
    """Clock mode with hourly chiming - inherits default bird behavior"""
    
    def __init__(self):
        super().__init__()
        self.current_hour = 12
        self.last_chime_time = 0
        self.chime_interval = 60  # Will be set from config
        
    def mode_init(self, crow, config):
        """Initialize clock-specific settings"""
        print("🕐 Clock mode initializing...")
        
        # Clock-specific state
        self.current_hour = 12
        self.last_chime_time = 0
        
        # Get chime interval from config
        chime_interval_minutes = config.get("clock_chime_interval_minutes", 60)
        test_mode = config.get("debug", False)
        self.chime_interval = 30 if test_mode else (chime_interval_minutes * 60)
        
        # Flash LEDs to show current hour
        self.flash_hour_confirmation(crow, self.current_hour)
        
        print(f"✅ Clock mode ready - hour set to {self.current_hour}")
    
    def run(self, crow, config):
        """
        Override the default run method for clock-specific behavior.
        
        Instead of the default timed actions, we do hourly chiming.
        But we still get all the button handling automatically from BaseMode.
        """
        print(f"🕐 Starting clock mode - hourly chime operation")
        
        # Initialize if not already done (inherited from BaseMode)
        if not self.is_running:
            try:
                self.init(crow, config)
                self.is_running = True
            except Exception as e:
                print(f"💥 Failed to initialize {self.mode_name}: {e}")
                return
        
        # Display startup info (can use inherited method or override)
        self.show_mode_info(crow, config)
        
        # Clock-specific main loop
        try:
            while True:
                current_time = time.monotonic()
                
                # **INHERITED AUTOMATIC BUTTON HANDLING** - No need to add this!
                if crow.button:
                    crow.button.update()
                
                # Check if it's time to chime
                time_since_last_chime = current_time - self.last_chime_time
                
                if time_since_last_chime >= self.chime_interval:
                    print(f"\n🔔 Chime time! ({self.chime_interval} seconds elapsed)")
                    self.perform_hourly_chime(crow, config)
                    self.last_chime_time = current_time
                
                # Use inherited mode_update for status (or override it)
                try:
                    should_continue = self.mode_update(crow, config)
                    if should_continue is False:
                        break
                except Exception as e:
                    print(f"💥 Error in mode_update: {e}")
                    time.sleep(1)
                
                # Inherited update interval and timing
                self.last_update_time = current_time
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Clock mode interrupted")
        except Exception as e:
            print(f"💥 Error in clock mode: {e}")
            try:
                crow.leds.flash_eyes(times=10)
            except:
                pass
        finally:
            # Use inherited cleanup (or override for custom cleanup)
            try:
                self.cleanup(crow, config)
            except Exception as e:
                print(f"⚠️ Cleanup error: {e}")
    
    def mode_update(self, crow, config):
        """Override to provide clock-specific status updates"""
        current_time = time.monotonic()
        
        # Status update every 10 seconds for clock mode
        if int(current_time) % 10 == 0 and int(current_time) != int(self.last_update_time):
            time_since_last_chime = current_time - self.last_chime_time
            time_until_chime = self.chime_interval - time_since_last_chime
            print(f"🕐 Hour: {self.current_hour}, Next chime in: {time_until_chime:.0f}s")
        
        return True  # Continue running
    
    def on_button_press(self, crow, config):
        """Override to handle hour advancement instead of default action"""
        self.current_hour += 1
        if self.current_hour > 12:
            self.current_hour = 1
            
        print(f"🕐 Hour advanced to {self.current_hour}")
        
        # Flash eyes to show current hour
        self.flash_hour_confirmation(crow, self.current_hour)
        
        # Optional: Also chime the new hour immediately
        immediate_chime = config.get("clock_button_immediate_chime", False)
        if immediate_chime:
            print("🔔 Chiming new hour immediately...")
            self.perform_hourly_chime(crow, config)
    
    def show_mode_info(self, crow, config):
        """Override to show clock-specific startup information"""
        test_mode = config.get("debug", False)
        
        if test_mode:
            print(f"🧪 DEBUG MODE: Chiming every {self.chime_interval} seconds")
        else:
            chime_minutes = self.chime_interval // 60
            print(f"🕐 Chiming every {chime_minutes} minutes")
        
        print(f"Current hour setting: {self.current_hour}")
        print("Button controls:")
        print("  Short press: Advance hour")
        print("  Long press: Cycle modes")
        print("=" * 50)
    
    def flash_hour_confirmation(self, crow, hour):
        """Flash eyes to confirm hour setting"""
        print(f"💡 Flashing {hour} times for hour {hour}")
        
        for i in range(hour):
            crow.leds.set_brightness(0.6)
            time.sleep(0.25)
            crow.leds.turn_off()
            time.sleep(0.25)
            
        print(f"✅ Hour {hour} confirmed")
    
    def perform_hourly_chime(self, crow, config):
        """Perform the hourly chime sequence"""
        hour = self.current_hour
        print(f"🕐 CHIMING HOUR {hour}")
        
        # Check conditions first (inherited method from BaseMode)
        light_sufficient, condition = crow.check_conditions()
        chime_volume = config.get("clock", {}).get("chime_volume", 0.7)
        
        if condition == "critical_battery":
            print("⚠️ Critical battery - performing minimal chime")
            # Could use inherited perform_battery_warning or custom
            crow.leds.flash_eyes(times=3)
            return
            
        if not light_sufficient:
            print("🌙 Too dark - performing quiet chime")
            for i in range(hour):
                print(f"  Dark caw {i+1}/{hour}")
                crow.amplifier.set_volume(chime_volume)
                crow.amplifier.play_wav()
                time.sleep(0.8)
            return
        
        # Full chime sequence
        print("🎭 Performing full chime sequence")
        crow.amplifier.set_volume(chime_volume)
        crow.leds.fade_in()
        
        for i in range(hour):
            print(f"  Caw {i+1}/{hour}")
            
            # Alternate servo positions
            if i % 2 == 0:
                crow.servo.to_top()
            else:
                crow.servo.to_bottom()
                
            crow.amplifier.play_wav()
            time.sleep(0.8)
        
        # Return to center and fade out
        crow.servo.to_midpoint()
        time.sleep(0.5)
        crow.leds.fade_out()
        
        print(f"✅ Chimed {hour} times")
        
        # Reset volume to normal
        crow.amplifier.set_volume(config["audio"]["volume"])
