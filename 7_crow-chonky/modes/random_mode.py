"""
Random Mode - Variable Interval Bird Actions
===========================================

This mode randomizes the interval between bird actions using a
configurable multiplier. For example, with a 0.25 multiplier and
60 minute interval, actions will occur randomly between 45-75 minutes.

Configuration:
    "random": {
        "interval_variance": 0.25  // ±25% variance
    }
"""

import random
from modes.base_mode import BaseMode
from config import get_config_value, config_section


class RandomMode(BaseMode):
    """Mode with randomized action intervals"""

    def __init__(self):
        super().__init__()
        self.interval_variance = 0.25  # Default ±25%
        self.last_interval = None

    def mode_init(self, crow, config):
        """Initialize random mode"""
        print("🎲 Random mode initializing...")

        # Get interval variance from config
        self.interval_variance = get_config_value(
            config,
            "random.interval_variance",
            0.25
        )

        # Validate variance (must be between 0 and 1)
        if not (0 <= self.interval_variance <= 1):
            print("⚠️ Invalid variance " + str(self.interval_variance) + ", using 0.25")
            self.interval_variance = 0.25

        variance_percent = int(self.interval_variance * 100)
        base_minutes = self.action_interval / 60
        min_minutes = base_minutes * (1 - self.interval_variance)
        max_minutes = base_minutes * (1 + self.interval_variance)

        print("✅ Random mode ready")
        print("   Base interval: " + str(int(base_minutes)) + " minutes")
        print("   Variance: ±" + str(variance_percent) + "%")
        print("   Range: " + str(int(min_minutes)) + "-" + str(int(max_minutes)) + " minutes")

    def get_next_interval(self):
        """
        Override to return randomized interval.

        Returns:
            float: Randomized interval in seconds
        """
        # Calculate min and max intervals
        min_interval = self.action_interval * (1 - self.interval_variance)
        max_interval = self.action_interval * (1 + self.interval_variance)

        # Generate random interval
        randomized_interval = random.uniform(min_interval, max_interval)

        # Store for display
        self.last_interval = randomized_interval

        # Log the randomization
        base_minutes = self.action_interval / 60
        random_minutes = randomized_interval / 60
        diff_minutes = random_minutes - base_minutes
        diff_percent = (diff_minutes / base_minutes) * 100

        print("🎲 Randomized interval: " + str(round(random_minutes, 1)) + " min " +
              "(" + ("+" if diff_percent >= 0 else "") + str(int(diff_percent)) + "% from " +
              str(int(base_minutes)) + " min base)")

        return randomized_interval

    def show_mode_info(self, crow, config):
        """Display random mode information"""
        base_minutes = self.action_interval / 60
        variance_percent = int(self.interval_variance * 100)
        min_minutes = base_minutes * (1 - self.interval_variance)
        max_minutes = base_minutes * (1 + self.interval_variance)

        print("=== 🎲 Random Mode ===")
        print("Base interval: " + str(int(base_minutes)) + " minutes")
        print("Variance: ±" + str(variance_percent) + "%")
        print("Actual range: " + str(int(min_minutes)) + "-" + str(int(max_minutes)) + " minutes")

        if self.last_interval:
            last_minutes = self.last_interval / 60
            print("Last scheduled: " + str(round(last_minutes, 1)) + " minutes")

        # Light sensor info
        SENSOR_DEFAULTS = {
            "light_threshold": 1000,
            "quiet_light_threshold": 3000
        }
        AMPLIFIER_DEFAULTS = {
            "volume": 0.6,
            "quiet_volume": 0.3
        }

        sensor_config = config_section(config, "sensors", SENSOR_DEFAULTS)
        amp_config = config_section(config, "amplifier", AMPLIFIER_DEFAULTS)

        print("\nLight-based volume control:")
        print("  < " + str(sensor_config['light_threshold']) + ": No sound (dark)")
        print("  " + str(sensor_config['light_threshold']) + "-" +
              str(sensor_config['quiet_light_threshold']) + ": Quiet (" +
              str(amp_config['quiet_volume']) + ")")
        print("  >= " + str(sensor_config['quiet_light_threshold']) + ": Full (" +
              str(amp_config['volume']) + ")")

        print("\nButton controls:")
        print("  Short press: Trigger action immediately")
        print("  Long press: Cycle modes")
        print("=" * 50)

    def on_button_press(self, crow, config):
        """Override to show next scheduled time after action"""
        # Perform the action
        super().on_button_press(crow, config)

        # Show when next action will be
        if self.last_interval:
            next_minutes = self.last_interval / 60
            print("⏰ Next automatic action in ~" + str(round(next_minutes, 1)) + " minutes")