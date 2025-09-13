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
from lib.servos import Servo
from lib.leds import Leds
from lib.sensors import LightSensor
from lib.amplifier import Amplifier
from lib.battery import Battery

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
    """Main entry point - clean BaseMode architecture"""
    print("🐦 Crow Bird - Clean BaseMode Architecture! 🐦")
    print("=" * 60)
    print("ARCHITECTURE FEATURES:")
    print("  ✅ BaseMode contains default bird behavior")
    print("  ✅ All modes inherit automatic button handling")
    print("  ✅ Clean mode manager with no legacy code")
    print("  ✅ Simplified button flow")
    print("BUTTON CONTROLS:")
    print("  Long press = Cycle modes (handled globally)")
    print("  Short press = Mode action (handled by each mode automatically)")
    print("=" * 60)

    # Load configuration
    config = load_config()

    try:
        # Create and initialize bird hardware
        crow = CrowBird(config)

        # Create mode manager (handles all mode loading/switching)
        mode_manager = ModeManager(crow, config)

        # Display mode information
        mode_info = mode_manager.get_mode_info()
        print(f"🚀 Starting mode: {mode_info['current_mode']}")
        print(f"Mode class: {mode_info['mode_class']}")
        print(f"Available modes: {' → '.join(mode_info['available_modes'])}")
        print(f"Position: {mode_info['current_position']}/{mode_info['total_modes']}")
        print()

        # Set up GLOBAL button for mode switching ONLY
        if crow.button:
            def on_mode_switch():
                """Handle long press - cycle to next mode"""
                print("\n🔄 LONG PRESS DETECTED - Cycling modes...")
                mode_manager.cycle_mode()
                mode_info = mode_manager.get_mode_info()
                print(f"✅ Now in mode: {mode_info['current_mode']} ({mode_info['mode_class']})")
                print(f"📍 Position: {mode_info['current_position']}/{mode_info['total_modes']}")
                print("Ready for mode operation...\n")

            # ONLY set long press callback - short press handled by modes automatically
            crow.button.on_long_press = on_mode_switch
            # Explicitly clear short press to avoid confusion
            crow.button.on_press = None

            print(f"🎮 Global Button Control (Mode Switching Only):")
            print(f"   Pin: {config.get('button', {}).get('pin', 'D6')}")
            print(f"   Long press: Cycle modes")
            print(f"   Short press: Handled automatically by current mode")
            print()
        else:
            print("⚠️ No global button available - mode switching disabled")
            print()

        # CLEAN MAIN LOOP - minimal complexity
        print("🚀 Starting mode operation...")
        print("All button handling and timing managed by BaseMode architecture")
        print()

        # Main operation loop
        while True:
            try:
                # Handle global mode switching (long press only)
                if crow.button:
                    crow.button.update()

                # Run the current mode - it handles EVERYTHING else
                # This includes:
                # - Short button press handling
                # - Timing and intervals
                # - Bird actions
                # - Status updates
                # - Error handling
                mode_manager.run_current_mode()

                # If we get here, the mode exited normally
                print("🏁 Mode completed - this shouldn't normally happen")
                break

            except KeyboardInterrupt:
                print("\n🛑 Interrupted by user")
                break
            except Exception as e:
                print(f"💥 Fatal error: {e}")
                print(f"   Error type: {type(e).__name__}")
                try:
                    crow.leds.flash_eyes(times=10)  # Error indication
                except:
                    pass
                break

            # Very small delay for mode switching responsiveness
            time.sleep(0.01)

    except Exception as e:
        print(f"💥 Fatal startup error: {e}")
        print(f"   Error details: {type(e).__name__}: {e}")
        # Try to show error via LEDs
        try:
            error_leds = Leds(board.A0)
            error_leds.flash_eyes(times=10)
            error_leds.deinit()
        except:
            pass
    finally:
        # Clean up everything
        if 'crow' in locals():
            crow.cleanup()
        print("🐦 Crow bird shutdown complete.")


if __name__ == "__main__":
    main()