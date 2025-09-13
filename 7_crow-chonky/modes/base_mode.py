"""
BaseMode - Default Bird Behavior with Automatic Button Handling
===============================================================

This is the base class that ALL modes inherit from.
Contains the standard bird behavior that can be overridden as needed.

Default behavior:
- Automatic button handling (fixes the button ignore issue)
- Timed actions every interval_minutes
- Light/battery condition checking
- Standard bird action sequence (light_rotate_hoot)
- Proper cleanup and error handling

Inherit from this class and override methods to customize:
- perform_action() - change what the bird does
- on_button_press() - change button behavior
- mode_update() - add status updates or checks
- show_mode_info() - customize startup display
- cleanup() - add custom cleanup
"""

import time


class BaseMode:
    """
    Base mode class with default bird behavior and automatic button handling.

    All modes should inherit from this class to ensure consistent behavior
    and automatic button handling that fixes the button ignore issue.
    """

    def __init__(self):
        # Auto-generate mode name from class name
        self.mode_name = self.__class__.__name__.replace('Mode', '').lower()
        if self.mode_name == 'base':
            self.mode_name = 'default'

        # State tracking
        self.is_running = False
        self.start_time = 0
        self.last_update_time = 0
        self.last_action_time = 0

        # Timing configuration (set from config in mode_init)
        self.update_interval = 0.01  # 10ms for button responsiveness
        self.action_interval = 60 * 60  # 1 hour default

    def init(self, crow, config):
        """Initialize the mode - sets up timing and button handling"""
        print(f"🚀 Initializing {self.mode_name} mode...")

        # Reset state
        self.is_running = False
        self.start_time = time.monotonic()
        self.last_update_time = 0
        self.last_action_time = 0

        # Get timing from config
        interval_minutes = config.get("interval_minutes", 60)
        self.action_interval = interval_minutes * 60

        # Set up automatic button callbacks
        self.setup_button_handling(crow, config)

        # Call mode-specific initialization
        try:
            self.mode_init(crow, config)
            print(f"✅ {self.mode_name} mode initialized")
        except Exception as e:
            print(f"❌ Error in {self.mode_name} mode_init(): {e}")
            raise

    def setup_button_handling(self, crow, config):
        """Set up automatic button event handling - FIXES BUTTON ISSUE"""
        if crow.button:
            def on_short_press():
                """Handle short button press automatically"""
                print(f"📱 Button press in {self.mode_name} mode")
                try:
                    self.on_button_press(crow, config)
                except Exception as e:
                    print(f"💥 Error in {self.mode_name}.on_button_press(): {e}")
                    try:
                        crow.leds.flash_eyes(times=3)  # Error indication
                    except:
                        pass

            # Set the short press callback
            # (long press remains global for mode switching)
            crow.button.on_press = on_short_press

            print(f"🎮 Automatic button handling active for {self.mode_name} mode")
        else:
            print(f"⚠️ No button available for {self.mode_name} mode")

    def run(self, crow, config):
        """
        Main run method with default bird behavior and AUTOMATIC BUTTON HANDLING.

        This implements the standard timed bird behavior and FIXES THE BUTTON ISSUE
        by automatically calling button.update() in the main loop.

        Override this method for completely different behavior, or override
        specific methods like perform_action() for customization.
        """
        print(f"🕐 Starting {self.mode_name} mode - standard timed operation")

        # Initialize if not already done
        if not self.is_running:
            try:
                self.init(crow, config)
                self.is_running = True
            except Exception as e:
                print(f"💥 Failed to initialize {self.mode_name}: {e}")
                return

        # Display mode-specific startup info
        self.show_mode_info(crow, config)

        # Perform initial action on startup
        print("🚀 Performing startup action...")
        self.check_conditions_and_act(crow, config)
        self.last_action_time = time.monotonic()

        try:
            # Main mode loop with AUTOMATIC BUTTON HANDLING
            while True:
                current_time = time.monotonic()

                # *** AUTOMATIC BUTTON HANDLING - FIXES THE BUTTON ISSUE! ***
                if crow.button:
                    crow.button.update()

                # Check if it's time for the next scheduled action
                time_since_last_action = current_time - self.last_action_time

                if time_since_last_action >= self.action_interval:
                    print(f"\n⏰ Action time! ({self.action_interval/60:.0f} minutes elapsed)")
                    self.check_conditions_and_act(crow, config)
                    self.last_action_time = current_time

                # Call mode-specific update logic
                try:
                    should_continue = self.mode_update(crow, config)
                    if should_continue is False:
                        print(f"🏁 {self.mode_name} mode completed normally")
                        break
                except Exception as e:
                    print(f"💥 Error in {self.mode_name}.mode_update(): {e}")
                    # Flash error indicator and continue
                    try:
                        crow.leds.flash_eyes(times=5)
                    except:
                        pass
                    time.sleep(1)  # Brief pause on error

                # Update timing
                self.last_update_time = current_time

                # Sleep for responsiveness - important for button detection
                time.sleep(self.update_interval)

        except KeyboardInterrupt:
            print(f"\n🛑 {self.mode_name} mode interrupted by user")
        except Exception as e:
            print(f"💥 Fatal error in {self.mode_name} mode: {e}")
            try:
                crow.leds.flash_eyes(times=10)
            except:
                pass
        finally:
            # Always clean up
            try:
                self.cleanup(crow, config)
            except Exception as e:
                print(f"⚠️ Cleanup error in {self.mode_name}: {e}")

    def check_conditions_and_act(self, crow, config):
        """Check conditions and perform appropriate action - core default behavior"""
        print(f"=== {self.mode_name} Condition Check ===")
        local_time = time.localtime()
        print(f"Time: {local_time[3]:02d}:{local_time[4]:02d}")

        # Check conditions (light level, battery)
        light_sufficient, condition = crow.check_conditions()

        if condition == "critical_battery":
            print("⚠️ Critical battery - performing warning flash only")
            self.perform_battery_warning(crow, config)
        elif light_sufficient:
            print("✅ Conditions good - performing full action")
            self.perform_action(crow, config)
        else:
            print("🌙 Too dark - performing night action")
            self.perform_night_action(crow, config)

        print("=== Check Complete ===\n")

    def perform_action(self, crow, config):
        """
        Perform the main bird action - THE CORE DEFAULT BEHAVIOR.

        This is the classic light_rotate_hoot sequence.
        Override this method to change what the bird does during normal operation.
        """
        print("🐦 Performing main bird action sequence...")

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

        print("✅ Action sequence complete!")

    def perform_night_action(self, crow, config):
        """Perform action when it's too dark - just flash eyes"""
        night_flashes = config.get("behavior", {}).get("night_flash_count", 2)
        print(f"🌙 Night action - flashing {night_flashes} times")
        crow.leds.flash_eyes(times=night_flashes)

    def perform_battery_warning(self, crow, config):
        """Perform action when battery is critical - minimal flash"""
        print("🔋 Battery warning - critical level")
        crow.leds.flash_eyes(times=5)

    # UTILITY METHODS

    def get_runtime(self):
        """Get how long the mode has been running"""
        if self.start_time:
            return time.monotonic() - self.start_time
        return 0

    def get_time_until_next_action(self):
        """Get time until next scheduled action"""
        if self.last_action_time:
            elapsed = time.monotonic() - self.last_action_time
            return max(0, self.action_interval - elapsed)
        return 0

    def get_status_string(self):
        """Get a status string for the mode"""
        runtime = self.get_runtime()
        next_action_minutes = self.get_time_until_next_action() / 60
        return f"{self.mode_name} mode (runtime: {runtime:.1f}s, next action: {next_action_minutes:.1f}m)"

    # METHODS TO OVERRIDE IN CHILD CLASSES

    def mode_init(self, crow, config):
        """
        Override this method for mode-specific initialization.
        Called once when the mode starts.
        """
        pass

    def mode_update(self, crow, config):
        """
        Override this method for mode-specific logic that runs every loop.

        The default behavior handles timed actions automatically.
        Use this for status updates, additional checks, etc.

        Returns:
            True: Continue running the mode (default)
            False: Exit the mode normally
            None/nothing: Continue running (same as True)
        """
        # Default: provide periodic status updates
        current_time = time.monotonic()

        # Status update every 30 seconds
        if int(current_time) % 30 == 0 and int(current_time) != int(self.last_update_time):
            next_action_minutes = self.get_time_until_next_action() / 60
            print(f"📊 {self.mode_name}: Next action in {next_action_minutes:.1f} minutes")

        return True  # Continue running

    def on_button_press(self, crow, config):
        """
        Override this method to handle short button presses.
        Default: perform immediate action.
        """
        print(f"📱 Button pressed - performing immediate action!")
        self.check_conditions_and_act(crow, config)

    def show_mode_info(self, crow, config):
        """
        Override this method to display mode-specific startup information.
        """
        interval_minutes = self.action_interval / 60
        print(f"📊 {self.mode_name} Mode - Standard Bird Behavior")
        print(f"   Action interval: {interval_minutes:.0f} minutes")
        print(f"   Press button for immediate action")
        print(f"   Long press button to cycle modes")
        print("=" * 50)
    
    def cleanup(self, crow, config):
        """
        Override this method for mode-specific cleanup.
        Called when the mode exits.
        """
        print(f"🧹 {self.mode_name} mode cleaning up...")
        
        # Standard cleanup - turn off LEDs, stop audio, center servo
        try:
            crow.leds.turn_off()
            crow.amplifier.stop()
            crow.servo.to_midpoint()
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
        
        print(f"✅ {self.mode_name} mode cleanup complete")