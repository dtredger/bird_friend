"""
Clock Mode - Simplified and Organized
====================================

Hourly chime mode with intelligent audio selection and light-based volume.
"""

from modes.base_mode import BaseMode
from config import get_config_value, config_section


class ClockMode(BaseMode):
    """Clock mode with intelligent chiming based on hour setting"""

    def __init__(self):
        super().__init__()
        self.current_hour = 6
        self.chime_in_progress = False

    def mode_init(self, crow, config):
        """Initialize clock mode"""
        print("🕐 Clock mode initializing...")
        self.current_hour = 12
        self.chime_in_progress = False
        self.schedule_hour_confirmation(crow, self.current_hour)
        print(f"✅ Clock mode ready - hour set to {self.current_hour}")

    def on_button_press(self, crow, config):
        """Advance hour and show confirmation"""
        self.current_hour += 1
        if self.current_hour > 12:
            self.current_hour = 1
        print(f"🕐 Hour advanced to {self.current_hour}")
        self.schedule_hour_confirmation(crow, self.current_hour)

    def check_conditions_and_act(self, crow, config):
        """Timer-triggered chime action"""
        print("🔔 Scheduled chime action triggered")
        self.perform_hourly_chime(crow, config)

    def perform_hourly_chime(self, crow, config):
        """Perform intelligent chime sequence with light-based volume"""
        if self.chime_in_progress:
            print("⚠️ Chime sequence already in progress")
            return

        self.chime_in_progress = True
        hour = self.current_hour
        print(f"🕐 Starting intelligent chime for hour {hour}")

        # Check conditions
        light_condition, battery_ok = crow.check_conditions()

        if not battery_ok:
            print("⚠️ Critical battery")
            crow.leds.flash_eyes(times=3)
            self.chime_in_progress = False
            return

        if light_condition == "dark":
            print("🌙 Too dark - LED flash only")
            BEHAVIOR_DEFAULTS = {"night_flash_count": 2}
            behavior_config = config_section(config, "behavior", BEHAVIOR_DEFAULTS)
            crow.leds.flash_eyes(times=behavior_config["night_flash_count"])
            self.chime_in_progress = False
            return

        # Set volume and start sequence (now uses smart fallback!)
        chime_volume = self.get_volume_for_light_condition(config, light_condition)
        original_volume = get_config_value(config, "amplifier.volume", 0.6)

        print(f"🔊 Using {light_condition} volume: {chime_volume}")
        crow.amplifier.set_volume(chime_volume)
        crow.leds.fade_in()

        # Get optimal file selection
        selected_files = crow.amplifier.select_files_for_caw_count(hour)
        print(f"🎯 Selected {len(selected_files)} files for {hour} chimes")

        # Schedule each file with servo movements
        cumulative_delay = 0
        for i, filename in enumerate(selected_files):
            # Servo movement (reduced in quiet mode)
            if light_condition != "quiet" or i % 2 == 0:
                servo_action = crow.servo.to_top if i % 2 == 0 else crow.servo.to_bottom
                self.schedule_action(cumulative_delay, servo_action, f"servo_{i+1}")

            # Audio playback
            def create_play_function(file_to_play):
                return lambda: crow.amplifier.play_wav(file_to_play) if file_to_play else lambda: crow.amplifier.play_wav()

            self.schedule_action(cumulative_delay + 0.1, create_play_function(filename), f"sound_{i+1}")

            # Timing between files
            cumulative_delay += 0.8 if light_condition == "quiet" else 1.2

        # Schedule cleanup
        self.schedule_action(cumulative_delay + 0.5,
                           lambda: self.finish_chime_sequence(crow, original_volume),
                           "cleanup")

    def finish_chime_sequence(self, crow, original_volume):
        """Complete chime sequence and restore settings"""
        crow.servo.to_midpoint()
        crow.leds.fade_out()
        crow.amplifier.set_volume(original_volume)
        self.chime_in_progress = False
        print("✅ Chime sequence complete")

    def schedule_hour_confirmation(self, crow, hour):
        """Schedule LED flashes to confirm current hour"""
        print(f"💡 Scheduling {hour} confirmation flashes")
        for i in range(hour):
            flash_delay = i * 0.5
            self.schedule_action(flash_delay, lambda: crow.leds.set_brightness(0.6), f"flash_{i+1}_on")
            self.schedule_action(flash_delay + 0.25, lambda: crow.leds.turn_off(), f"flash_{i+1}_off")

    def get_volume_for_light_condition(self, config, light_condition):
        """
        Get appropriate volume for light condition.
        Uses clock-specific volumes if configured, otherwise falls back to base amplifier volumes.

        Smart Fallback Logic:
        1. If config has clock.quiet_chime_volume AND clock.chime_volume → use clock volumes
        2. Otherwise → use base class method (amplifier.quiet_volume / amplifier.volume)

        This eliminates duplication while preserving clock-specific volume capability!
        """
        # Check if clock-specific volumes are configured
        clock_quiet_volume = get_config_value(config, "clock.quiet_chime_volume", None)
        clock_normal_volume = get_config_value(config, "clock.chime_volume", None)

        # If clock volumes are configured, use them
        if clock_quiet_volume is not None and clock_normal_volume is not None:
            return clock_quiet_volume if light_condition == "quiet" else clock_normal_volume

        # Otherwise, fall back to base amplifier volumes
        return super().get_volume_for_light_condition(config, light_condition)

    def show_mode_info(self, crow, config):
        """Display clock mode information with smart volume source detection"""
        interval_minutes = get_config_value(config, "interval_minutes", 60)

        SENSOR_DEFAULTS = {"light_threshold": 1000, "quiet_light_threshold": 3000}
        sensor_config = config_section(config, "sensors", SENSOR_DEFAULTS)

        print(f"🕐 Light-based chiming every {interval_minutes} minutes")
        print(f"Current hour setting: {self.current_hour}")

        try:
            audio_info = crow.amplifier.get_sound_file_info()
            if isinstance(audio_info, dict):
                print(f"🎵 Audio: {audio_info['total_files']} files, strategy: {audio_info['strategy']}")
        except:
            print("🎵 Audio: Basic configuration")

        # Show volume configuration (clock-specific or fallback)
        clock_quiet_vol = get_config_value(config, "clock.quiet_chime_volume", None)
        clock_normal_vol = get_config_value(config, "clock.chime_volume", None)

        if clock_quiet_vol is not None and clock_normal_vol is not None:
            quiet_vol, normal_vol = clock_quiet_vol, clock_normal_vol
            vol_type = "clock"
        else:
            quiet_vol = get_config_value(config, "amplifier.quiet_volume", 0.3)
            normal_vol = get_config_value(config, "amplifier.volume", 0.6)
            vol_type = "amplifier (fallback)"

        print(f"🔊 Light-based chime volumes ({vol_type}):")
        print(f"   < {sensor_config['light_threshold']}: No sound (dark)")
        print(f"   {sensor_config['light_threshold']}-{sensor_config['quiet_light_threshold']}: Quiet volume ({quiet_vol})")
        print(f"   >= {sensor_config['quiet_light_threshold']}: Full volume ({normal_vol})")

        print("Button controls:")
        print("  Short press: Advance hour (with confirmation)")
        print("  Long press: Cycle modes")
        print("=" * 50)
