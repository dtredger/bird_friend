"""
Crow Bird for Adafruit RP2040 Prop-Maker Feather - Mode Dispatcher
================================================================

This is the main entry point that initializes the bird hardware and
dispatches to the appropriate mode based on configuration.

Available modes:
- default: Standard timed operation (contains core light_rotate_hoot function)
- debug: Component testing and diagnostics
- demo: Continuous demonstration mode
- calibration: Sensor calibration assistant
- setup: Initial setup and configuration
- maintenance: System diagnostics and logs
- single: Perform one action then stop

Hardware Setup:
- Servo: Plug directly into built-in 3-pin servo header
- Speaker: Connect 4-8Ω speaker to built-in amplifier terminals
- LEDs: Connect to pin A0 through 200Ω resistor to GND
- Light sensor: Connect photoresistor between 3.3V and A1, with 10kΩ pulldown to GND
- Battery monitoring: Connect voltage divider (BAT → 100kΩ → A3 → 100kΩ → GND)
"""

import board
import time
import digitalio
import json
import sys

# Import our CircuitPython bird libraries
from servos import Servo
from leds import Leds
from sensors import LightSensor
from amplifier import Amplifier
from battery import Battery

# Always import default mode for core functionality
import modes.default as default_mode


class CrowBird:
    """Main crow bird controller using Prop-Maker Feather and bird libraries"""
    
    def __init__(self, config):
        """Initialize all bird components"""
        self.config = config
        self.setup_power()
        self.setup_components()
        print("🐦 Crow Bird initialized")
        
    def setup_power(self):
        """Enable external power for servo and audio"""
        print("Enabling external power...")
        self.external_power = digitalio.DigitalInOut(board.EXTERNAL_POWER)
        self.external_power.direction = digitalio.Direction.OUTPUT
        self.external_power.value = True
        time.sleep(0.1)  # Give power time to stabilize
        
    def setup_components(self):
        """Initialize all hardware components using our libraries"""
        print("Setting up components...")
        
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
        
        print("All components initialized!")
    
    def check_conditions(self):
        """Check light and battery conditions, return if action should proceed"""
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
        """Clean up resources - especially important before deep sleep"""
        print("Cleaning up...")
        try:
            # Turn off LEDs
            if hasattr(self, 'leds'):
                self.leds.turn_off()
                self.leds.deinit()
            
            # Stop servo and deinit
            if hasattr(self, 'servo'):
                self.servo.deinit()
            
            # Deinit sensors
            if hasattr(self, 'light_sensor'):
                self.light_sensor.deinit()
                
            # Stop audio and deinit
            if hasattr(self, 'amplifier'):
                self.amplifier.stop()
                self.amplifier.deinit()
                
            # Battery doesn't need deinit in our implementation
            if hasattr(self, 'battery') and self.battery:
                pass
                
            # Turn off external power last
            self.external_power.value = False
            print("✅ Cleanup complete")
            
        except Exception as e:
            print(f"Cleanup error: {e}")


def load_config():
    """Load configuration from JSON file"""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
        print("✅ Configuration loaded from config.json")
        return config
    except (OSError, ValueError) as e:
        print(f"⚠️ config.json not found or invalid: {e}")
        print("Using default settings")
        return None


def import_mode(mode_name):
    """Dynamically import the specified mode module"""
    try:
        module_name = f"modes.{mode_name}"
        module = __import__(module_name, fromlist=[mode_name])
        return module
    except ImportError as e:
        print(f"❌ Could not import mode '{mode_name}': {e}")
        print("Available modes: default, debug, demo, calibration, setup, maintenance, single")
        return None


def main():
    """Main entry point - load config and dispatch to appropriate mode"""
    print("🐦 Crow Bird starting on Prop-Maker Feather! 🐦")
    print("Using CircuitPython bird libraries with modular modes")
    
    # Load configuration
    config = load_config()
    mode_name = config.get("mode", "default")
    
    # Map 'normal' to 'default' for backwards compatibility
    if mode_name == "normal":
        mode_name = "default"
        print("📝 Note: 'normal' mode is now called 'default'")
    
    print(f"Mode: {mode_name}")
    
    # Import the mode module (default is already imported)
    if mode_name == "default":
        mode_module = default_mode
    else:
        mode_module = import_mode(mode_name)
        if mode_module is None:
            print("❌ Failed to load mode, falling back to default mode")
            mode_module = default_mode
    
    try:
        # Create and initialize bird
        crow = CrowBird(config)
        
        # Check if mode module has a run function
        if hasattr(mode_module, 'run'):
            print(f"🚀 Starting {mode_name} mode...")
            mode_module.run(crow, config)
        else:
            print(f"❌ Mode {mode_name} does not have a run() function")
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        # Try to flash LEDs to indicate error
        try:
            error_leds = Leds(board.A0)
            error_leds.flash_eyes(times=10)
            error_leds.deinit()
        except:
            pass
    finally:
        # Clean up
        if 'crow' in locals():
            crow.cleanup()
        print("🐦 Crow bird shut down complete.")


if __name__ == "__main__":
    main()
