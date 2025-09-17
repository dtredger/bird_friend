"""
Clock Mode - Hourly Chime with Alarm Scheduling
===============================================

Intelligently selects sound files based on their configured caw counts
to achieve the exact number of chimes needed for each hour.
"""

import time
from modes.base_mode import BaseMode


class ClockMode(BaseMode):
    """Clock mode with alarm-based hourly chiming"""

    def __init__(self):
        super().__init__()
        self.current_hour = 12
        self.last_chime_time = 0
        self.chime_interval = 60  # Will be set from config
        self.chime_in_progress = False

    def mode_init(self, crow, config):
        """Initialize clock-specific settings"""
        print("🕐 Clock mode initializing with ALARM SCHEDULING...")

        # Clock-specific state
        self.current_hour = 12
        self.last_chime_time = 0
        self.chime_in_progress = False

        # Get chime interval from config
        chime_interval_minutes = config.get("clock_chime_interval_minutes", 60)
        test_mode = config.get("debug", False)
        self.chime_interval = 30 if test_mode else (chime_interval_minutes * 60)

        # Flash LEDs to show current hour using alarms
        self.schedule_hour_confirmation(crow, self.current_hour)

        print(f"✅ Clock mode ready with ALARMS - hour set to {self.current_hour}")

    def check_conditions_and_act(self, crow, config):
        print("🔔 Scheduled chime action triggered")
        self.perform_hourly_chime(crow, config)

    def on_button_press(self, crow, config):
        """Override to handle hour advancement with alarm-scheduled confirmation"""
        self.current_hour += 1
        if self.current_hour > 12:
            self.current_hour = 1

        print(f"🕐 Hour advanced to {self.current_hour}")

        # Schedule confirmation flashes using alarms
        self.schedule_hour_confirmation(crow, self.current_hour)

        # Optional: Also chime the new hour immediately
        immediate_chime = config.get("clock_button_immediate_chime", False)
        if immediate_chime:
            print("🔔 Scheduling immediate chime...")
            # Schedule chime after confirmation flashes complete
            flash_duration = self.current_hour * 0.5 + 0.5
            self.schedule_action(flash_duration,
                lambda: self.perform_hourly_chime(crow, config),
                "immediate_chime")

    def schedule_hour_confirmation(self, crow, hour):
        """Schedule hour confirmation flashes using alarm system"""
        print(f"💡 Scheduling {hour} confirmation flashes")

        for i in range(hour):
            # Schedule each flash on/off pair
            flash_delay = i * 0.5

            # Flash on
            self.schedule_action(flash_delay,
                lambda: crow.leds.set_brightness(0.6),
                f"flash_{i+1}_on")

            # Flash off
            self.schedule_action(flash_delay + 0.25,
                lambda: crow.leds.turn_off(),
                f"flash_{i+1}_off")

        print(f"⏰ Scheduled {hour} confirmation flashes with precise alarm timing")

    def show_mode_info(self, crow, config):
        """Override to show clock-specific startup information"""
        test_mode = config.get("debug", False)
        interval_minutes = config.get("interval_minutes", 60)

        if test_mode:
            print(f"🧪 DEBUG MODE: ALARM-scheduled chiming every {interval_minutes} minutes")
        else:
            print(f"🕐 ALARM-scheduled chiming every {interval_minutes} minutes")

        print(f"Current hour setting: {self.current_hour}")
        print("ALARM-ENHANCED Button controls:")
        print("  Short press: Advance hour (with scheduled confirmation)")
        print("  Long press: Cycle modes")
        print("  All timing: Non-blocking alarm-based")
        print("=" * 50)

    def perform_hourly_chime(self, crow, config):
        """Perform the hourly chime sequence using alarm scheduling"""
        if self.chime_in_progress:
            print("⚠️ Chime sequence already in progress")
            return

        self.chime_in_progress = True
        hour = self.current_hour
        print(f"🕐 Starting ALARM-SCHEDULED chime for hour {hour}")

        # Check conditions first
        light_sufficient, condition = crow.check_conditions()
        chime_volume = config.get("clock", {}).get("chime_volume", 0.7)

        if condition == "critical_battery":
            print("⚠️ Critical battery - performing minimal chime")
            crow.leds.flash_eyes(times=3)
            self.chime_in_progress = False
            return

        if not light_sufficient:
            print("🌙 Too dark - scheduling quiet chime")
            self.schedule_quiet_chime(crow, config, hour)
            return

        # Full chime sequence with precise alarm timing
        print("🎭 Scheduling full chime sequence with PRECISE timing")
        crow.amplifier.set_volume(chime_volume)
        crow.leds.fade_in()

        # Schedule each chime with precise timing
        for i in range(hour):
            chime_delay = i * 0.8  # 0.8 seconds between chimes

            # Alternate servo positions for visual variety
            if i % 2 == 0:
                self.schedule_action(chime_delay,
                    lambda: crow.servo.to_top(),
                    f"chime_{i+1}_top")
            else:
                self.schedule_action(chime_delay,
                    lambda: crow.servo.to_bottom(),
                    f"chime_{i+1}_bottom")

            # Schedule sound slightly after servo movement
            self.schedule_action(chime_delay + 0.1,
                lambda: crow.amplifier.play_wav(),
                f"chime_{i+1}_sound")

        # Schedule cleanup after all chimes complete
        cleanup_delay = hour * 0.8 + 0.5
        self.schedule_action(cleanup_delay,
            lambda: self.finish_chime_sequence(crow, config),
            "chime_cleanup")

        print(f"🔔 Scheduled {hour} chimes with PRECISE ALARM TIMING!")

    def schedule_quiet_chime(self, crow, config, hour):
        """Schedule quiet chimes for dark conditions using alarms"""
        print(f"🌙 Scheduling {hour} quiet chimes")

        for i in range(hour):
            delay = i * 0.5  # Faster quiet chimes
            self.schedule_action(delay,
                lambda: crow.amplifier.play_wav(),
                f"quiet_chime_{i+1}")

        # Schedule cleanup
        cleanup_delay = hour * 0.5 + 0.3
        self.schedule_action(cleanup_delay,
            lambda: self.finish_quiet_chimes(crow, config),
            "quiet_cleanup")

        print(f"⏰ Scheduled {hour} quiet chimes")

    def finish_chime_sequence(self, crow, config):
        """Scheduled cleanup after full chime sequence"""
        print("🧹 Finishing chime sequence...")
        crow.servo.to_midpoint()
        crow.leds.fade_out()

        # Reset volume to normal
        crow.amplifier.set_volume(config["audio"]["volume"])
        self.chime_in_progress = False

        print(f"✅ ALARM-SCHEDULED chime sequence complete!")

    def finish_quiet_chimes(self, crow, config):
        """Scheduled cleanup after quiet chimes"""
        print("🧹 Finishing quiet chimes...")
        self.chime_in_progress = False
        print(f"✅ Quiet chimes complete!")
