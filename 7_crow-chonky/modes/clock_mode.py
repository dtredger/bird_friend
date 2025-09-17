"""
Clock Mode - Intelligent Chiming with Caw Counting
==================================================

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

        # Configure intelligent audio chiming
        self.setup_intelligent_audio(crow, config)

        # Flash LEDs to show current hour using alarms
        self.schedule_hour_confirmation(crow, self.current_hour)

        print(f"✅ Clock mode ready with INTELLIGENT CHIMING - hour set to {self.current_hour}")

    def setup_intelligent_audio(self, crow, config):
        """Configure the amplifier with sound file caw counts"""
        audio_config = config.get("audio", {})
        sound_files = audio_config.get("sound_files", {})
        chime_strategy = audio_config.get("chime_strategy", "intelligent")
        fallback_behavior = audio_config.get("fallback_behavior", "repeat_single")

        if sound_files:
            print(f"🎵 Configuring intelligent chiming with {len(sound_files)} sound files:")

            # Verify files exist and show configuration
            existing_files = {}
            missing_files = []

            for filename, caw_count in sound_files.items():
                full_path = f"/{audio_config.get('directory', 'audio')}/{filename}"
                try:
                    with open(full_path, 'rb'):
                        existing_files[filename] = caw_count
                        print(f"   ✅ {filename}: {caw_count} caws")
                except:
                    missing_files.append(filename)
                    print(f"   ❌ {filename}: NOT FOUND")

            if missing_files:
                print(f"⚠️ {len(missing_files)} configured files not found - will use fallback behavior")

            # Configure the amplifier
            crow.amplifier.set_sound_files(
                existing_files,
                chime_strategy=chime_strategy,
                fallback_behavior=fallback_behavior
            )

            print(f"🎯 Chiming strategy: {chime_strategy}")
            print(f"🔄 Fallback behavior: {fallback_behavior}")

        else:
            print("⚠️ No sound files configured - using random selection")
            crow.amplifier.set_sound_files({})

    def run(self, crow, config):
        """Override the default run method for clock-specific behavior."""
        print(f"🕐 Starting clock mode")

        # Initialize if not already done
        if not self.is_running:
            try:
                self.init(crow, config)
                self.is_running = True
            except Exception as e:
                print(f"💥 Failed to initialize {self.mode_name}: {e}")
                return

        # Display startup info
        self.show_mode_info(crow, config)

        # Initialize timing variables
        self.last_update_time = time.monotonic()
        self.last_status_time = time.monotonic()

        # Clock-specific main loop
        try:
            while True:
                current_time = time.monotonic()

                # Button handling (inherited from BaseMode)
                if crow.button:
                    crow.button.update()

                # *** Process scheduled actions (chime sequences) ***
                self.check_scheduled_actions()

                # Check if it's time to chime (instead of regular actions)
                time_since_last_chime = current_time - self.last_chime_time

                if time_since_last_chime >= self.chime_interval:
                    print(f"\n🔔 Chime time! ({self.chime_interval} seconds elapsed)")
                    self.perform_hourly_chime(crow, config)
                    self.last_chime_time = current_time

                # Mode status updates
                time_since_status = current_time - self.last_status_time
                if time_since_status >= self.status_interval:
                    try:
                        should_continue = self.mode_update(crow, config)
                        if should_continue is False:
                            break
                    except Exception as e:
                        print(f"💥 Error in mode_update: {e}")
                    self.last_status_time = current_time

                # Update timing
                self.last_update_time = current_time

        except KeyboardInterrupt:
            print(f"\n🛑 Clock mode interrupted")
        except Exception as e:
            print(f"💥 Error in clock mode: {e}")
            try:
                crow.leds.flash_eyes(times=10)
            except:
                pass
        finally:
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
            scheduled_count = len(self.scheduled_actions)

            # Show sound file info occasionally
            if int(current_time) % 30 == 0:
                info = crow.amplifier.get_sound_file_info()
                if isinstance(info, dict):
                    print(f"🎵 Sound files: {info['total_files']} files, strategy: {info['strategy']}")

            print(f"🕐 Hour: {self.current_hour}, Next chime: {time_until_chime:.0f}s, Scheduled: {scheduled_count}")

        return True

    def on_button_press(self, crow, config):
        """Override to handle hour advancement with intelligent chiming demo"""
        self.current_hour += 1
        if self.current_hour > 12:
            self.current_hour = 1

        print(f"🕐 Hour advanced to {self.current_hour}")

        # Schedule confirmation flashes using alarms
        self.schedule_hour_confirmation(crow, self.current_hour)

    def schedule_hour_confirmation(self, crow, hour):
        """Schedule hour confirmation flashes using alarm system"""
        print(f"💡 Scheduling {hour} confirmation flashes")

        for i in range(hour):
            flash_delay = i * 0.5

            self.schedule_action(flash_delay,
                lambda: crow.leds.set_brightness(0.6),
                f"flash_{i+1}_on")

            self.schedule_action(flash_delay + 0.25,
                lambda: crow.leds.turn_off(),
                f"flash_{i+1}_off")

        print(f"⏰ Scheduled {hour} confirmation flashes")

    def show_mode_info(self, crow, config):
        """Override to show clock-specific startup information"""
        chime_minutes = self.chime_interval // 60
        print(f"🕐 Intelligent chiming every {chime_minutes} minutes")
        print(f"Current hour setting: {self.current_hour}")

        # Show audio configuration
        info = crow.amplifier.get_sound_file_info()
        if isinstance(info, dict) and info['total_files'] > 0:
            print(f"🎵 {info['total_files']} sound files configured ({info['strategy']} strategy)")
            max_caws = info['max_single_file_caws']
            print(f"   Max caws per file: {max_caws}, Total possible: {info['total_possible_caws']}")
        else:
            print("🎵 Using random sound file selection")

        print("Button controls:")
        print("  Short press: Advance hour")
        print("  Long press: Cycle modes")
        print("=" * 50)

    def perform_hourly_chime(self, crow, config):
        """Perform hourly chime using sound selection"""
        if self.chime_in_progress:
            print("⚠️ Chime sequence already in progress")
            return

        self.chime_in_progress = True
        hour = self.current_hour
        print(f"🕐 Starting chime for hour {hour}")

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

        # Full intelligent chime sequence
        print("🎭 Scheduling full intelligent chime sequence")
        crow.amplifier.set_volume(chime_volume)
        crow.leds.fade_in()

        # Get chime spacing from config
        chime_spacing = config.get("clock", {}).get("chime_spacing_seconds", 0.8)

        # Schedule servo movements for visual effect
        for i in range(min(hour, 6)):  # Limit servo movements to avoid excessive motion
            movement_delay = i * chime_spacing

            if i % 2 == 0:
                self.schedule_action(movement_delay,
                    lambda: crow.servo.to_top(),
                    f"movement_{i+1}_top")
            else:
                self.schedule_action(movement_delay,
                    lambda: crow.servo.to_bottom(),
                    f"movement_{i+1}_bottom")

        # Schedule the intelligent chiming
        self.schedule_action(0.2,
            lambda: self.play_intelligent_chime_sequence(crow, config, hour),
            "intelligent_chime_sequence")

        # Schedule cleanup after estimated completion time
        # Estimate based on number of files that might be played
        estimated_duration = self.estimate_chime_duration(crow, hour, chime_spacing)
        cleanup_delay = estimated_duration + 1.0

        self.schedule_action(cleanup_delay,
            lambda: self.finish_intelligent_chime(crow, config),
            "chime_cleanup")

        print(f"🔔 Scheduled intelligent chime for {hour} caws!")

    def play_intelligent_chime_sequence(self, crow, config, hour):
        """Play the intelligent chime sequence"""
        print(f"🎵 Playing intelligent chime sequence for {hour} caws...")

        try:
            played_files = crow.amplifier.play_chime_sequence(hour)

            # Log what was played for debugging
            file_names = [f.split('/')[-1] for f in played_files]
            print(f"🎶 Intelligent chime complete - played: {file_names}")

        except Exception as e:
            print(f"💥 Error in intelligent chiming: {e}")
            # Fallback to simple chiming
            crow.amplifier.play_wav()

    def estimate_chime_duration(self, crow, hour, spacing):
        """Estimate how long the chime sequence will take"""
        info = crow.amplifier.get_sound_file_info()

        if isinstance(info, dict) and info['total_files'] > 0:
            # Estimate based on typical file count for this hour
            estimated_files = min(hour, 4)  # Most efficient packing
            estimated_duration = estimated_files * 2.0  # ~2 seconds per file
        else:
            # Random file mode - assume one file per caw
            estimated_duration = hour * 2.0

        return max(estimated_duration, hour * 0.5)  # Minimum reasonable duration

    def schedule_quiet_intelligent_chime(self, crow, config, hour):
        """Schedule quiet chimes for dark conditions"""
        print(f"🌙 Scheduling {hour} quiet intelligent chimes")

        # Quiet chime - just audio, no servo movement or LEDs
        self.schedule_action(0.1,
            lambda: self.play_quiet_intelligent_chime(crow, config, hour),
            "quiet_intelligent_chime")

        # Quick cleanup
        cleanup_delay = self.estimate_chime_duration(crow, hour, 0.5) + 0.5
        self.schedule_action(cleanup_delay,
            lambda: self.finish_quiet_chimes(crow, config),
            "quiet_cleanup")

    def play_quiet_intelligent_chime(self, crow, config, hour):
        """Play quiet intelligent chime"""
        quiet_volume = config.get("clock", {}).get("chime_volume", 0.7) * 0.5
        crow.amplifier.set_volume(quiet_volume)

        played_files = crow.amplifier.play_chime_sequence(hour)
        file_names = [f.split('/')[-1] for f in played_files]
        print(f"🌙 Quiet intelligent chime complete: {file_names}")

    def finish_intelligent_chime(self, crow, config):
        """Scheduled cleanup after intelligent chime sequence"""
        print("🧹 Finishing intelligent chime sequence...")
        crow.servo.to_midpoint()
        crow.leds.fade_out()

        # Reset volume to normal
        crow.amplifier.set_volume(config["audio"]["volume"])
        self.chime_in_progress = False

        print(f"✅ Intelligent chime sequence complete!")

    def finish_quiet_chimes(self, crow, config):
        """Scheduled cleanup after quiet chimes"""
        print("🧹 Finishing quiet intelligent chimes...")
        crow.amplifier.set_volume(config["audio"]["volume"])
        self.chime_in_progress = False
        print(f"✅ Quiet intelligent chimes complete!")