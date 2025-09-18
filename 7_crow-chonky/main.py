"""
Updated main.py - Uses lib/config.py and services handle their own defaults
"""

import board
import time
import digitalio
import json

# Import our config module
from config import load_config_file, get_config_value, config_section

# Import our CircuitPython bird libraries
from servos import Servo
from leds import Leds
from sensors import LightSensor
from amplifier import Amplifier
from battery import Battery

# Import our mode manager
from modes.mode_manager import ModeManager


class CrowBird:
    """Main crow bird controller"""

    def __init__(self, config):
        self.config = config
        self.setup_power()
        self.setup_components()
        self.setup_intelligent_audio()
        print("🐦 Crow Bird initialized")

    def setup_power(self):
        """Enable external power for servo and audio"""
        print("⚡ Enabling external power...")
        self.external_power = digitalio.DigitalInOut(board.EXTERNAL_POWER)
        self.external_power.direction = digitalio.Direction.OUTPUT
        self.external_power.value = True
        time.sleep(0.1)

    def setup_components(self):
        """Initialize all hardware components - each handles its own defaults"""
        print("🔧 Setting up components...")

        # LED setup - service handles defaults
        LED_DEFAULTS = {"max_brightness": 0.8}
        led_config = config_section(self.config, "leds", LED_DEFAULTS)
        led_pin_name = get_config_value(self.config, "pins.led", "A0")

        led_pin = getattr(board, led_pin_name)
        self.leds = Leds(led_pin)
        self.leds.max_brightness = led_config["max_brightness"]
        print(f"✅ LEDs ready on {led_pin_name}")

        # Light sensor setup - service handles defaults
        SENSOR_DEFAULTS = {
            "light_threshold": 1000,
            "quiet_light_threshold": 3000
        }
        sensor_config = config_section(self.config, "sensors", SENSOR_DEFAULTS)
        light_pin_name = get_config_value(self.config, "pins.light_sensor", "A1")

        light_pin = getattr(board, light_pin_name)
        self.light_sensor = LightSensor(light_pin)
        self.light_sensor.threshold = sensor_config["light_threshold"]

        print(f"✅ Light sensor ready on {light_pin_name} (thresholds: {sensor_config['light_threshold']}/{sensor_config['quiet_light_threshold']})")

        # Battery monitoring setup - service handles defaults
        BATTERY_DEFAULTS = {"enabled": False}
        battery_config = config_section(self.config, "battery", BATTERY_DEFAULTS)

        if battery_config["enabled"]:
            battery_pin_name = get_config_value(self.config, "pins.battery", "A3")
            if battery_pin_name:
                battery_pin = getattr(board, battery_pin_name)
                self.battery = Battery(battery_pin)
                print(f"✅ Battery monitoring ready on {battery_pin_name}")
            else:
                print("⚠️ Battery enabled but no pin configured")
                self.battery = None
        else:
            self.battery = None
            print("⚠️ Battery monitoring disabled")

        # Servo setup - service handles defaults
        SERVO_DEFAULTS = {
            "speed": 0.02,
            "pause": 0.5
        }
        servo_config = config_section(self.config, "servo", SERVO_DEFAULTS)

        self.servo = Servo(board.EXTERNAL_SERVO)
        self.servo.sleep_interval = servo_config["speed"]
        self.servo.rotation_pause = servo_config["pause"]
        print("✅ Servo ready")

        # Audio setup - service handles defaults
        AMPLIFIER_DEFAULTS = {
            "directory": "audio",
            "sample_rate": 11000,
            "volume": 0.6
        }
        amp_config = config_section(self.config, "amplifier", AMPLIFIER_DEFAULTS)

        self.amplifier = Amplifier(
            board.I2S_WORD_SELECT,
            board.I2S_BIT_CLOCK,
            board.I2S_DATA,
            audio_dir=amp_config["directory"],
            sample_rate=amp_config["sample_rate"]
        )
        self.amplifier.set_volume(amp_config["volume"])
        print("✅ Audio ready")

        # Global button setup - service handles defaults
        self.setup_global_button()

        print("🎉 All components initialized!")

    def setup_global_button(self):
        """Setup global button - service handles defaults"""
        BUTTON_DEFAULTS = {
            "enabled": True,
            "long_press_ms": 1000,
            "debounce_ms": 50,
            "double_press_window_ms": 500
        }
        button_config = config_section(self.config, "button", BUTTON_DEFAULTS)

        if button_config["enabled"]:
            try:
                from button import Button
                button_pin_name = get_config_value(self.config, "pins.button", "D6")
                button_pin = getattr(board, button_pin_name)

                self.button = Button(
                    button_pin,
                    debounce_ms=button_config["debounce_ms"],
                    long_press_ms=button_config["long_press_ms"],
                    double_press_window_ms=button_config["double_press_window_ms"]
                )

                print(f"🎮 Global button ready on pin {button_pin_name}")

            except Exception as e:
                print(f"⚠️ Global button setup failed: {e}")
                self.button = None
        else:
            self.button = None

    def check_conditions(self):
        """Check light and battery conditions - uses sensor service defaults"""
        battery_ok = True

        # Check battery status
        if self.battery:
            battery_status = self.battery.get_status()
            print(f"🔋 Battery: {battery_status['voltage']}V ({battery_status['percentage']}%)")

            if self.battery.is_critical_battery():
                print("⚠️ CRITICAL BATTERY!")
                battery_ok = False

        # Check light level - get thresholds from sensor service
        light_reading = self.light_sensor.read()
        dark_threshold = get_config_value(self.config, "sensors.light_threshold", 1000)
        quiet_threshold = get_config_value(self.config, "sensors.quiet_light_threshold", 3000)

        if light_reading < dark_threshold:
            light_condition = "dark"
            print(f"💡 Light: {light_reading} → DARK (< {dark_threshold})")
        elif light_reading < quiet_threshold:
            light_condition = "quiet"
            print(f"💡 Light: {light_reading} → QUIET (< {quiet_threshold})")
        else:
            light_condition = "normal"
            print(f"💡 Light: {light_reading} → NORMAL (>= {quiet_threshold})")

        return light_condition, battery_ok

    def setup_intelligent_audio(self):
        """Configure intelligent audio - service handles defaults"""
        AUDIO_DEFAULTS = {
            "sound_files": {},
            "chime_strategy": "intelligent",
            "fallback_behavior": "repeat_single",
            "directory": "audio"
        }
        audio_config = config_section(self.config, "amplifier", AUDIO_DEFAULTS)
        sound_files = audio_config["sound_files"]

        if sound_files:
            print("🎵 Setting up intelligent audio system...")

            # Validate and report on sound files
            existing_files = {}
            missing_files = []
            total_caws = 0

            for filename, caw_count in sound_files.items():
                full_path = f"/{audio_config['directory']}/{filename}"
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
                    chime_strategy=audio_config["chime_strategy"],
                    fallback_behavior=audio_config["fallback_behavior"]
                )

                print(f"🎯 Intelligent audio configured:")
                print(f"   {len(existing_files)} files, {total_caws} total caws")
                print(f"   Strategy: {audio_config['chime_strategy']}")

                if missing_files:
                    print(f"⚠️ {len(missing_files)} configured files missing")

            else:
                print("⚠️ No valid sound files found - using random selection")
                self.amplifier.set_sound_files({})
        else:
            print("⚠️ No sound files configured - using random selection")
            self.amplifier.set_sound_files({})

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


def main():
    """Main entry point with service-based defaults"""
    print("🐦 Crow Bird 🐦")
    print("=" * 60)

    # Load configuration using lib/config.py
    config = load_config_file("config.json")

    try:
        # Create and initialize bird hardware (services handle defaults)
        crow = CrowBird(config)

        # Create mode manager
        mode_manager = ModeManager(crow, config)

        # Set up global button for mode switching
        if crow.button:
            def on_mode_switch():
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

        # Main loop
        while True:
            # Handle button presses
            if crow.button:
                crow.button.update()

            # Handle scheduled actions
            current_mode = mode_manager.current_mode_instance
            if current_mode and hasattr(current_mode, 'check_scheduled_actions'):
                current_mode.check_scheduled_actions()

            # Small sleep to allow keyboard interrupts
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received - exiting...")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        try:
            crow.leds.flash_eyes(times=10)
        except:
            pass
    finally:
        if 'crow' in locals():
            crow.cleanup()
        print("🐦 Crow bird shutdown complete.")


def schedule_next_action(mode, crow, config):
    """Schedule the next mode action using timer"""
    if not mode:
        return

    interval_minutes = get_config_value(config, "interval_minutes", 60)
    interval_seconds = interval_minutes * 60

    def perform_scheduled_action():
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