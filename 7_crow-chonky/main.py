"""
Crow Bird Main - Timer-Based Architecture
=========================================

Main entry point with true timer-based scheduling.
"""

import board
import time
import digitalio
import json

# Import our CircuitPython bird libraries
from servos import Servo
from leds import Leds
from sensors import LightSensor
from amplifier import Amplifier
from battery import Battery

# Import our mode manager
from modes.mode_manager import ModeManager


class CrowBird:
    """Main crow bird controller with all hardware components"""

    def __init__(self, config):
        self.config = config
        self.setup_power()
        self.setup_components()
        self.setup_intelligent_audio()
        print("🐦 Crow Bird initialized with timer-based architecture")

    def setup_power(self):
        """Enable external power for servo and audio"""
        print("⚡ Enabling external power...")
        self.external_power = digitalio.DigitalInOut(board.EXTERNAL_POWER)
        self.external_power.direction = digitalio.Direction.OUTPUT
        self.external_power.value = True
        time.sleep(0.1)  # Give power time to stabilize

    def setup_components(self):
        """Initialize all hardware components"""
        print("🔧 Setting up components...")

        # LED setup
        led_pin = getattr(board, self.config["pins"]["led"])
        self.leds = Leds(led_pin)
        self.leds.max_brightness = self.config["leds"]["max_brightness"]
        print("✅ LEDs ready")

        # Light sensor setup
        light_pin = getattr(board, self.config["pins"]["light_sensor"])
        self.light_sensor = LightSensor(light_pin)
        self.light_sensor.threshold = self.config["sensors"]["light_threshold"]
        print("✅ Light sensor ready")

        # Battery monitoring setup
        if self.config["battery"]["enabled"]:
            battery_pin = getattr(board, self.config["pins"]["battery"])
            self.battery = Battery(battery_pin)
            print("✅ Battery monitoring ready")
        else:
            self.battery = None
            print("⚠️ Battery monitoring disabled")

        # Servo setup
        self.servo = Servo(board.EXTERNAL_SERVO)
        self.servo.sleep_interval = self.config["servo"]["speed"]
        self.servo.rotation_pause = self.config["servo"]["pause"]
        print("✅ Servo ready")

        # Audio setup
        self.amplifier = Amplifier(
            board.I2S_WORD_SELECT,
            board.I2S_BIT_CLOCK,
            board.I2S_DATA,
            audio_dir=self.config["audio"]["directory"],
            sample_rate=self.config["audio"]["sample_rate"]
        )
        self.amplifier.set_volume(self.config["audio"]["volume"])
        print("✅ Audio ready")

        # Global button setup - ONLY for mode switching
        self.setup_global_button()

        print("🎉 All components initialized!")

    def setup_intelligent_audio(self):
        """Configure intelligent audio system with caw counting"""
        audio_config = self.config.get("audio", {})
        sound_files = audio_config.get("sound_files", {})

        if sound_files:
            print("🎵 Setting up intelligent audio system...")

            chime_strategy = audio_config.get("chime_strategy", "intelligent")
            fallback_behavior = audio_config.get("fallback_behavior", "repeat_single")

            # Validate and report on sound files
            existing_files = {}
            missing_files = []
            total_caws = 0

            for filename, caw_count in sound_files.items():
                full_path = f"/{audio_config.get('directory', 'audio')}/{filename}"
                try:
                    with open(full_path, 'rb'):
                        existing_files[filename] = caw_count
                        total_caws += caw_count
                        print(f"   ✅ {filename}: {caw_count} caws")
                except:
                    missing_files.append(filename)
                    print(f"   ❌ {filename}: NOT FOUND")

            if existing_files:
                self.amplifier.set_sound_files(
                    existing_files,
                    chime_strategy=chime_strategy,
                    fallback_behavior=fallback_behavior
                )

                max_caws = max(existing_files.values()) if existing_files else 0
                print(f"🎯 Intelligent audio configured:")
                print(f"   {len(existing_files)} files, {total_caws} total caws")
                print(f"   Max single file: {max_caws} caws")
                print(f"   Strategy: {chime_strategy}")
                print(f"   Fallback: {fallback_behavior}")

                if missing_files:
                    print(f"⚠️ {len(missing_files)} configured files missing:")
                    for filename in missing_files:
                        print(f"   - {filename}")

            else:
                print("⚠️ No valid sound files found - using random selection")
                self.amplifier.set_sound_files({})
        else:
            print("⚠️ No sound files configured - using random selection")
            self.amplifier.set_sound_files({})

    def setup_global_button(self):
        """Setup global button for mode switching ONLY"""
        button_config = self.config.get("button", {})
        button_enabled = button_config.get("enabled", True)

        if button_enabled:
            try:
                from button import Button
                button_pin_name = button_config.get("pin", "D6")
                button_pin = getattr(board, button_pin_name)

                # Create button for global mode switching ONLY
                self.button = Button(
                    button_pin,
                    debounce_ms=button_config.get("debounce_ms", 50),
                    long_press_ms=button_config.get("long_press_ms", 1500),
                    double_press_window_ms=button_config.get("double_press_window_ms", 500)
                )

                print(f"🎮 Global button ready on pin {button_pin_name}")

            except Exception as e:
                print(f"⚠️ Global button setup failed: {e}")
                self.button = None
        else:
            self.button = None

    def check_conditions(self):
        """Check light and battery conditions for mode decision making"""
        # Check battery status
        if self.battery:
            battery_status = self.battery.get_status()
            print(f"🔋 Battery: {battery_status['voltage']}V ({battery_status['percentage']}%)")

            if self.battery.is_critical_battery():
                print("⚠️ CRITICAL BATTERY!")
                return False, "critical_battery"

        # Check light level
        light_reading = self.light_sensor.read()
        light_sufficient = self.light_sensor.over_minimum()

        print(f"💡 Light reading: {light_reading} (sufficient: {light_sufficient})")

        return light_sufficient, "light_sufficient" if light_sufficient else "too_dark"

    def cleanup(self):
        """Clean up all resources before shutdown"""
        print("🧹 Cleaning up crow bird...")
        try:
            if hasattr(self, 'leds'):
                self.leds.turn_off()
                self.leds.deinit()

            if hasattr(self, 'servo'):
                self.servo.deinit()

            if hasattr(self, 'light_sensor'):
                self.light_sensor.deinit()

            if hasattr(self, 'amplifier'):
                self.amplifier.stop()
                self.amplifier.deinit()

            if hasattr(self, 'button') and self.button:
                self.button.deinit()

            # Turn off external power last
            self.external_power.value = False
            print("✅ Crow bird cleanup complete")

        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")


def load_config():
    """Load configuration from JSON file with sensible defaults"""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        print("✅ Configuration loaded from config.json")
        return config
    except (OSError, ValueError) as e:
        print(f"⚠️ config.json not found or invalid: {e}")
        print("📄 Using default configuration")
        return {
            "mode": "default",
            "available_modes": ["default", "clock", "debug"],
            "interval_minutes": 60,
            "pins": {
                "led": "A0",
                "light_sensor": "A1",
                "battery": ""
            },
            "battery": {"enabled": False},
            "button": {
                "enabled": True,
                "pin": "D6",
                "long_press_ms": 1500
            },
            "audio": {
                "directory": "audio",
                "sample_rate": 11000,
                "volume": 0.6,
                "sound_files": {
                    "crow_single.wav": 1,
                    "crow_double.wav": 2
                },
                "chime_strategy": "intelligent",
                "fallback_behavior": "repeat_single"
            },
            "sensors": {"light_threshold": 1000},
            "leds": {"max_brightness": 0.8},
            "servo": {"speed": 0.02, "pause": 0.5},
            "clock": {
                "chime_volume": 0.7,
                "chime_spacing_seconds": 0.8
            },
            "behavior": {"night_flash_count": 2}
        }


def main():
    """
    Timer-based main entry point
    """
    print("🐦 Crow Bird 🐦")
    print("=" * 60)

    # Load configuration
    config = load_config()

    try:
        # Create and initialize bird hardware
        crow = CrowBird(config)

        # Create mode manager
        mode_manager = ModeManager(crow, config)

        # Set up GLOBAL button for mode switching
        if crow.button:
            def on_mode_switch():
                """Handle long press - mode switching!"""
                print("\n🔄 Mode switch requested...")
                mode_manager.cycle_mode()
                mode_info = mode_manager.get_mode_info()
                print(f"✅ Switched to: {mode_info['current_mode']}")

                # Re-initialize the new mode
                current_mode = mode_manager.current_mode_instance
                if current_mode:
                    current_mode.init(crow, config)
                    schedule_next_action(current_mode, crow, config)

            crow.button.on_long_press = on_mode_switch
            print("🎮 Button control ready")
        else:
            print("⚠️ No button - mode switching disabled")

        # Initialize the starting mode
        current_mode = mode_manager.current_mode_instance
        if current_mode:
            current_mode.init(crow, config)
            print(f"🚀 Mode initialized: {mode_manager.current_mode_name}")

        # Schedule the first action
        schedule_next_action(current_mode, crow, config)

        print("⏰ Timer-based scheduling active")
        print("🎯 Main loop starting (Ctrl+C to exit)...")

        # SIMPLE, RESPONSIVE MAIN LOOP
        while True:
            # Handle button presses
            if crow.button:
                crow.button.update()

            # Handle scheduled actions
            current_mode = mode_manager.current_mode_instance
            if current_mode and hasattr(current_mode, 'check_scheduled_actions'):
                current_mode.check_scheduled_actions()

            # CRITICAL: Small sleep to allow keyboard interrupts
            time.sleep(0.01)  # 10ms - fast enough, allows interrupts

    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received - exiting...")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        try:
            crow.leds.flash_eyes(times=10)
        except:
            pass
    finally:
        # Cleanup
        if 'crow' in locals():
            crow.cleanup()
        print("🐦 Crow bird shutdown complete.")


def schedule_next_action(mode, crow, config):
    """Schedule the next mode action using timer"""
    if not mode:
        return

    interval_minutes = config.get("interval_minutes", 60)
    interval_seconds = interval_minutes * 60

    def perform_scheduled_action():
        """Callback for timer-scheduled action"""
        print(f"\n⏰ Timer-triggered action in {mode.mode_name} mode")

        try:
            # Perform the mode's action
            mode.check_conditions_and_act(crow, config)

            # Schedule the next action
            schedule_next_action(mode, crow, config)

        except Exception as e:
            print(f"💥 Error in scheduled action: {e}")
            # Still schedule next action to keep going
            schedule_next_action(mode, crow, config)

    # Schedule using the mode's alarm system
    if hasattr(mode, 'schedule_action'):
        action_id = mode.schedule_action(
            interval_seconds,
            perform_scheduled_action,
            f"next_mode_action"
        )
        print(f"⏰ Next action scheduled in {interval_minutes} minutes (ID: {action_id})")
    else:
        print("⚠️ Mode doesn't support timer scheduling")


if __name__ == "__main__":
    main()