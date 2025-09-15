"""
BaseMode - Timer-Based Architecture
===================================
"""

import time


class BaseMode:
    """Timer-based base mode class"""

    def __init__(self):
        # Mode identification
        self.mode_name = self.__class__.__name__.replace('Mode', '').lower()
        if self.mode_name == 'base':
            self.mode_name = 'default'

        # State tracking
        self.is_running = False
        self.start_time = 0

        # Timer-based scheduling
        self.scheduled_actions = []
        self.action_id = 0

        # Timing intervals (for reference, not polling)
        self.action_interval = 3600  # 1 hour in seconds
        self.status_interval = 30    # 30 seconds


    def init(self, crow, config):
        """Initialize the mode"""
        print("Initializing " + self.mode_name + " mode")

        self.is_running = False
        self.start_time = time.monotonic()

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

        self.is_running = True

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

    def check_conditions_and_act(self, crow, config):
        """Check conditions and act"""
        print("=== Timer-triggered action ===")

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

        self.is_running = False

    # Methods to override in child classes
    def mode_init(self, crow, config):
        """Override for mode-specific initialization"""
        pass

    def on_button_press(self, crow, config):
        """Override for button press handling"""
        print("Button pressed - immediate action")
        self.check_conditions_and_act(crow, config)

    def show_mode_info(self, crow, config):
        """Override for mode-specific info"""
        interval_minutes = self.action_interval // 60
        print("=== " + self.mode_name + " Mode ===")
        print("Timer interval: " + str(interval_minutes) + " minutes")
        print("Alarm scheduling: ACTIVE")
        print("Button response: INSTANT")
        print("=" * 30)

    # Utility methods
    def get_runtime(self):
        """Get runtime in seconds"""
        if self.start_time:
            return time.monotonic() - self.start_time
        return 0

    def get_scheduled_count(self):
        """Get number of scheduled actions"""
        return len(self.scheduled_actions)