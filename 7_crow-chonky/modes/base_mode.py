"""
BaseMode - Simple Syntax for CircuitPython
==========================================

No f-strings, no complex syntax, just basic Python that works on CircuitPython.
"""

import time


class BaseMode:
    """Simple base mode class with basic syntax"""

    def __init__(self):
        # Mode identification
        self.mode_name = self.__class__.__name__.replace('Mode', '').lower()
        if self.mode_name == 'base':
            self.mode_name = 'default'

        # State tracking
        self.is_running = False
        self.start_time = 0
        self.last_update_time = 0
        self.last_action_time = 0
        self.last_status_time = 0

        # Simple alarm scheduling
        self.scheduled_actions = []
        self.action_id = 0

        # Timing
        self.action_interval = 3600  # 1 hour in seconds
        self.status_interval = 30    # 30 seconds
        self.update_interval = 0.01  # 10ms


    def init(self, crow, config):
        """Initialize the mode"""
        print("Initializing " + self.mode_name + " mode")

        self.is_running = False
        self.start_time = time.monotonic()
        self.last_update_time = 0
        self.last_action_time = 0
        self.last_status_time = 0

        # Get timing from config
        interval_minutes = config.get("interval_minutes", 60)
        self.action_interval = interval_minutes * 60

        # Setup button handling
        self.setup_button_handling(crow, config)

        # Call mode-specific init
        try:
            self.mode_init(crow, config)
            print("Mode " + self.mode_name + " initialized")
        except Exception as e:
            print("Error in mode_init: " + str(e))
            raise

    def schedule_action(self, delay_seconds, callback, name):
        """Schedule an action to happen after delay_seconds"""
        target_time = time.monotonic() + delay_seconds
        self.action_id = self.action_id + 1

        action = {
            'id': self.action_id,
            'target_time': target_time,
            'callback': callback,
            'name': name
        }

        self.scheduled_actions.append(action)
        print("Scheduled " + name + " in " + str(delay_seconds) + "s")
        return self.action_id

    def check_scheduled_actions(self):
        """Check and execute any scheduled actions"""
        if not self.scheduled_actions:
            return

        current_time = time.monotonic()
        completed = []

        for i, action in enumerate(self.scheduled_actions):
            if current_time >= action['target_time']:
                print("Executing: " + action['name'])
                try:
                    action['callback']()
                except Exception as e:
                    print("Error in scheduled action: " + str(e))
                completed.append(i)

        # Remove completed actions (in reverse order)
        for i in reversed(completed):
            self.scheduled_actions.pop(i)

    def setup_button_handling(self, crow, config):
        """Set up button handling"""
        if crow.button:
            def button_pressed():
                print("Button pressed in " + self.mode_name + " mode")
                try:
                    self.on_button_press(crow, config)
                except Exception as e:
                    print("Button press error: " + str(e))
                    try:
                        crow.leds.flash_eyes(times=3)
                    except:
                        pass

            crow.button.on_press = button_pressed
            print("Button handling active")

    def run(self, crow, config):
        """Main run method with alarm processing"""
        print("Starting " + self.mode_name + " mode")

        if not self.is_running:
            try:
                self.init(crow, config)
                self.is_running = True
            except Exception as e:
                print("Init failed: " + str(e))
                return

        self.show_mode_info(crow, config)

        # Initial action
        self.check_conditions_and_act(crow, config)
        self.last_action_time = time.monotonic()

        try:
            while True:
                current_time = time.monotonic()

                # Handle button presses
                if crow.button:
                    crow.button.update()

                # Process scheduled actions - KEY LINE!
                self.check_scheduled_actions()

                # Check for regular timed actions
                time_since_action = current_time - self.last_action_time
                if time_since_action >= self.action_interval:
                    print("Time for scheduled action")
                    self.check_conditions_and_act(crow, config)
                    self.last_action_time = current_time

                # Mode updates
                time_since_status = current_time - self.last_status_time
                if time_since_status >= self.status_interval:
                    try:
                        should_continue = self.mode_update(crow, config)
                        if should_continue is False:
                            break
                    except Exception as e:
                        print("Mode update error: " + str(e))
                    self.last_status_time = current_time

                # Exit check
                if hasattr(self, 'should_exit'):
                    if self.should_exit(crow, config):
                        break

                self.last_update_time = current_time

                # NO SLEEP - immediate responsiveness!

        except KeyboardInterrupt:
            print("Mode interrupted")
        except Exception as e:
            print("Fatal error: " + str(e))
        finally:
            self.cleanup(crow, config)

    def check_conditions_and_act(self, crow, config):
        """Check conditions and act"""
        print("=== Checking conditions ===")

        light_sufficient, condition = crow.check_conditions()

        if condition == "critical_battery":
            print("Critical battery")
            self.perform_battery_warning(crow, config)
        elif light_sufficient:
            print("Good conditions - full action")
            self.perform_action(crow, config)
        else:
            print("Too dark - night action")
            self.perform_night_action(crow, config)

    def perform_action(self, crow, config):
        """Main action using scheduled timing"""
        print("Performing scheduled action sequence")

        # Immediate actions
        crow.leds.fade_in()
        crow.servo.to_top()
        crow.amplifier.play_wav()

        # Define functions for scheduled actions
        def move_bottom():
            crow.servo.to_bottom()
            crow.amplifier.play_wav()

        def move_center():
            crow.servo.to_midpoint()

        def fade_out():
            crow.leds.fade_out()

        # Schedule future actions
        self.schedule_action(0.5, move_bottom, "move_bottom")
        self.schedule_action(1.0, move_center, "move_center")
        self.schedule_action(1.5, fade_out, "fade_out")

        print("Action sequence scheduled")

    def perform_night_action(self, crow, config):
        """Night action"""
        night_flashes = config.get("behavior", {}).get("night_flash_count", 2)
        print("Night action - flashing " + str(night_flashes) + " times")
        crow.leds.flash_eyes(times=night_flashes)

    def perform_battery_warning(self, crow, config):
        """Battery warning"""
        print("Battery warning")
        crow.leds.flash_eyes(times=5)

    def cleanup(self, crow, config):
        """Cleanup method"""
        print("Cleaning up " + self.mode_name)

        # Cancel scheduled actions
        cancelled = len(self.scheduled_actions)
        self.scheduled_actions.clear()
        if cancelled > 0:
            print("Cancelled " + str(cancelled) + " scheduled actions")

        # Standard cleanup
        try:
            crow.leds.turn_off()
            crow.amplifier.stop()
            crow.servo.to_midpoint()
        except Exception as e:
            print("Cleanup error: " + str(e))

    # Methods to override in child classes
    def mode_init(self, crow, config):
        """Override for mode-specific initialization"""
        pass

    def mode_update(self, crow, config):
        """Override for mode-specific updates"""
        # Show status every 30 seconds
        current_time = time.monotonic()
        if int(current_time) % 30 == 0 and int(current_time) != int(self.last_update_time):
            scheduled_count = len(self.scheduled_actions)
            print("Mode status - Scheduled actions: " + str(scheduled_count))
        return True

    def should_exit(self, crow, config):
        """Override for custom exit conditions"""
        return False

    def on_button_press(self, crow, config):
        """Override for button press handling"""
        print("Button pressed - immediate action")
        self.check_conditions_and_act(crow, config)

    def show_mode_info(self, crow, config):
        """Override for mode-specific info"""
        interval_minutes = self.action_interval // 60
        print("=== " + self.mode_name + " Mode ===")
        print("Action interval: " + str(interval_minutes) + " minutes")
        print("Alarm scheduling: ACTIVE")
        print("Button response: INSTANT")
        print("=" * 30)

    # Utility methods
    def get_runtime(self):
        """Get runtime in seconds"""
        if self.start_time:
            return time.monotonic() - self.start_time
        return 0

    def get_time_until_next_action(self):
        """Get time until next action"""
        if self.last_action_time:
            elapsed = time.monotonic() - self.last_action_time
            return max(0, self.action_interval - elapsed)
        return 0