"""
Clock Mode - Hourly Chime with Intelligent Audio Selection
=========================================================

Intelligently selects sound files based on their configured caw counts
to achieve the exact number of chimes needed for each hour.
"""

import time
from modes.base_mode import BaseMode


class ClockMode(BaseMode):
    """Clock mode with intelligent audio selection for accurate chime counts"""

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

        # Show audio configuration info
        audio_info = crow.amplifier.get_sound_file_info()
        if isinstance(audio_info, dict):
            print(f"🎵 Audio: {audio_info['total_files']} files, strategy: {audio_info['strategy']}")
            print(f"    Max single file: {audio_info['max_single_file_caws']} caws")

        print("Button controls:")
        print("  Short press: Advance hour (with scheduled confirmation)")
        print("  Long press: Cycle modes")
        print("  All timing: Intelligent audio selection")
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
            print("🌙 Too dark - scheduling quiet intelligent chime")
            self.schedule_quiet_intelligent_chime(crow, config, hour)
            return

        # Full chime sequence with intelligent audio selection
        print("🎭 Scheduling full intelligent chime sequence")
        crow.amplifier.set_volume(chime_volume)
        crow.leds.fade_in()

        # Get the optimal file selection for this hour
        selected_files = crow.amplifier.select_files_for_caw_count(hour)

        print(f"🎯 Selected {len(selected_files)} files for {hour} chimes:")
        for i, filename in enumerate(selected_files):
            file_display = filename.split('/')[-1] if filename else "random"
            print(f"    {i+1}. {file_display}")

        # Schedule each file with appropriate timing and servo movements
        cumulative_delay = 0
        for i, filename in enumerate(selected_files):
            # Alternate servo positions for visual variety
            if i % 2 == 0:
                self.schedule_action(cumulative_delay,
                    lambda: crow.servo.to_top(),
                    f"file_{i+1}_servo_top")
            else:
                self.schedule_action(cumulative_delay,
                    lambda: crow.servo.to_bottom(),
                    f"file_{i+1}_servo_bottom")

            # Schedule the sound file to play
            # Capture filename in closure to avoid lambda late binding issues
            def create_play_function(file_to_play):
                if file_to_play is None:
                    return lambda: crow.amplifier.play_wav()  # Random file
                else:
                    return lambda: crow.amplifier.play_wav(file_to_play)

            self.schedule_action(cumulative_delay + 0.1,
                create_play_function(filename),
                f"file_{i+1}_sound")

            # Calculate delay for next file (longer gap between files than between individual chimes)
            file_gap = 1.2 if len(selected_files) > 1 else 0.5
            cumulative_delay += file_gap

        # Schedule cleanup after all files complete
        cleanup_delay = cumulative_delay + 0.5
        self.schedule_action(cleanup_delay,
            lambda: self.finish_chime_sequence(crow, config),
            "chime_cleanup")

        print(f"🔔 Scheduled INTELLIGENT chime sequence with {len(selected_files)} optimally selected files!")

    def schedule_quiet_intelligent_chime(self, crow, config, hour):
        """Schedule quiet chimes using intelligent file selection"""
        print(f"🌙 Scheduling quiet intelligent chimes for hour {hour}")

        # Use intelligent selection even for quiet chimes
        selected_files = crow.amplifier.select_files_for_caw_count(hour)

        cumulative_delay = 0
        for i, filename in enumerate(selected_files):
            # Quiet chimes - no servo movement, just audio
            def create_quiet_play_function(file_to_play):
                if file_to_play is None:
                    return lambda: crow.amplifier.play_wav()
                else:
                    return lambda: crow.amplifier.play_wav(file_to_play)

            self.schedule_action(cumulative_delay,
                create_quiet_play_function(filename),
                f"quiet_file_{i+1}")

            # Shorter gaps for quiet chimes
            cumulative_delay += 0.6

        # Schedule cleanup
        cleanup_delay = cumulative_delay + 0.3
        self.schedule_action(cleanup_delay,
            lambda: self.finish_quiet_chimes(crow, config),
            "quiet_cleanup")

        print(f"⏰ Scheduled {len(selected_files)} quiet intelligent chimes")

    def finish_chime_sequence(self, crow, config):
        """Scheduled cleanup after full chime sequence"""
        print("🧹 Finishing intelligent chime sequence...")
        crow.servo.to_midpoint()
        crow.leds.fade_out()

        # Reset volume to normal
        crow.amplifier.set_volume(config["audio"]["volume"])
        self.chime_in_progress = False

        print(f"✅ INTELLIGENT chime sequence complete!")

    def finish_quiet_chimes(self, crow, config):
        """Scheduled cleanup after quiet chimes"""
        print("🧹 Finishing quiet intelligent chimes...")
        self.chime_in_progress = False
        print(f"✅ Quiet intelligent chimes complete!")
