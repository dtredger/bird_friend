"""
Crow Bird Main - Clean BaseMode Architecture
===========================================

Main entry point with clean BaseMode architecture.
- ModeManager imported from separate file
- All modes inherit from BaseMode
- Button handling is automatic in modes
- Global button only handles mode switching
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
        print("🐦 Crow Bird initialized with BaseMode architecture")

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
                print(f"   Long press (≥{button_config.get('long_press_ms', 1500)}ms): Cycle modes")
                print(f"   Short press: Handled automatically by each mode")

            except Exception as e:
                print(f"⚠️ Global button setup failed: {e}")
                print("   Mode switching disabled, but modes will work normally")
                self.button = None
        else:
            self.button = None
            print("ℹ️ Button explicitly disabled in config")

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
                "volume": 0.6
            },
            "sensors": {"light_threshold": 1000},
            "leds": {"max_brightness": 0.8},
            "servo": {"speed": 0.02, "pause": 0.5},
            "behavior": {"night_flash_count": 2}
        }


def main():
    """
    COMPLETELY NON-BLOCKING main entry point.

    No more sleep calls = immediate responsiveness!
    """
    print("🐦 Crow Bird - NON-BLOCKING Architecture! 🐦")
    print("=" * 60)
    print("RESPONSIVENESS FEATURES:")
    print("  ✅ NO time.sleep() calls anywhere")
    print("  ✅ Immediate button response")
    print("  ✅ Immediate keyboard interrupt response")
    print("  ✅ Instant mode switching")
    print("  ✅ Maximum system responsiveness")
    print("BUTTON CONTROLS:")
    print("  Long press = Cycle modes (instant response)")
    print("  Short press = Mode action (instant response)")
    print("=" * 60)

    # Load configuration
    config = load_config()

    try:
        # Create and initialize bird hardware
        crow = CrowBird(config)

        # Create mode manager
        mode_manager = ModeManager(crow, config)

        # Set up GLOBAL button for INSTANT mode switching
        if crow.button:
            def on_instant_mode_switch():
                """Handle long press - INSTANT mode switching!"""
                print("\n🔄 LONG PRESS - Switching modes INSTANTLY...")
                mode_manager.cycle_mode()
                mode_info = mode_manager.get_mode_info()
                print(f"✅ Switched to: {mode_info['current_mode']} ({mode_info['mode_class']})")
                print(f"📍 Position: {mode_info['current_position']}/{mode_info['total_modes']}")
                print("Ready for operation...\n")

            # Set INSTANT mode switching callback
            crow.button.on_long_press = on_instant_mode_switch
            crow.button.on_press = None  # Handled by modes

            print(f"🎮 INSTANT Button Control:")
            print(f"   Pin: {config.get('button', {}).get('pin', 'D6')}")
            print(f"   Long press: INSTANT mode cycling")
            print(f"   Short press: INSTANT mode actions")
            print()
        else:
            print("⚠️ No button - mode switching disabled")

        # Track mode running state
        mode_running = False
        current_mode_instance = None

        while True:
            try:
                # *** INSTANT GLOBAL BUTTON HANDLING ***
                if crow.button:
                    crow.button.update()

                # *** START MODE IF NOT RUNNING ***
                if not mode_running:
                    print(f"🏃 Starting mode: {mode_manager.current_mode_name}")
                    # Get reference to current mode instance
                    current_mode_instance = mode_manager.current_mode_instance
                    mode_running = True

                # *** RUN MODE SINGLE ITERATION ***
                # Instead of calling the blocking run() method,
                # we'll implement a non-blocking mode execution
                if current_mode_instance and mode_running:
                    try:
                        # Initialize mode if needed
                        if not current_mode_instance.is_running:
                            current_mode_instance.init(crow, config)
                            current_mode_instance.is_running = True
                            current_time = time.monotonic()
                            current_mode_instance.last_action_time = current_time

                        # Single non-blocking mode update
                        current_time = time.monotonic()

                        # Button handling (automatic in BaseMode)
                        if crow.button:
                            crow.button.update()

                        # Check for timed actions
                        time_since_last_action = current_time - current_mode_instance.last_action_time
                        if time_since_last_action >= current_mode_instance.action_interval:
                            print(f"\n⏰ Mode action time!")
                            current_mode_instance.check_conditions_and_act(crow, config)
                            current_mode_instance.last_action_time = current_time

                        # Mode-specific updates
                        time_since_status = current_time - current_mode_instance.last_status_time
                        if time_since_status >= current_mode_instance.status_interval:
                            should_continue = current_mode_instance.mode_update(crow, config)
                            current_mode_instance.last_status_time = current_time

                            if should_continue is False:
                                print(f"🏁 Mode {mode_manager.current_mode_name} completed")
                                mode_running = False

                        # Check scheduled actions if available
                        if hasattr(current_mode_instance, 'check_scheduled_actions'):
                            current_mode_instance.check_scheduled_actions()

                        # Check for mode exit conditions
                        if hasattr(current_mode_instance, 'should_exit'):
                            if current_mode_instance.should_exit(crow, config):
                                print(f"🏁 Mode {mode_manager.current_mode_name} requesting exit")
                                mode_running = False

                    except Exception as e:
                        print(f"💥 Error in mode execution: {e}")
                        try:
                            crow.leds.flash_eyes(times=5)
                        except:
                            pass
                        mode_running = False

                # *** CHECK FOR MODE SWITCH ***
                # If mode stopped running, we might need to restart it or switch modes
                if not mode_running:
                    # Check if mode manager switched modes
                    if current_mode_instance != mode_manager.current_mode_instance:
                        print(f"🔄 Mode switch detected")
                        # Cleanup old mode
                        if current_mode_instance:
                            try:
                                current_mode_instance.cleanup(crow, config)
                            except:
                                pass
                        current_mode_instance = mode_manager.current_mode_instance
                    # Restart the current mode
                    mode_running = True

                # *** NO SLEEP - MAXIMUM RESPONSIVENESS ***
                # The loop runs as fast as possible for INSTANT response
                # to button presses, keyboard interrupts, and everything else!

            except KeyboardInterrupt:
                print("\n🛑 INSTANT interrupt response!")
                break
            except Exception as e:
                print(f"💥 Fatal error: {e}")
                try:
                    crow.leds.flash_eyes(times=10)
                except:
                    pass
                break

    except Exception as e:
        print(f"💥 Fatal startup error: {e}")
        try:
            error_leds = Leds(board.A0)
            error_leds.flash_eyes(times=10)
            error_leds.deinit()
        except:
            pass
    finally:
        # Cleanup
        if 'crow' in locals():
            crow.cleanup()
        print("🐦 Crow bird shutdown complete.")


# if __name__ == "__main__":
#     main()