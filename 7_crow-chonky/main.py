"""
Crow Bird for Adafruit RP2040 Prop-Maker Feather - Global Button Control System
===============================================================================

This is the main entry point with global button control for mode switching.

Global Button Controls:
- Long press (1500ms+): Cycle through available modes (configured in config.json)
- Short press (<1500ms): Call current mode's button_pressed() method

Available modes are defined in config.json under "available_modes"

Hardware Setup:
- Servo: Plug directly into built-in 3-pin servo header
- Speaker: Connect 4-8Ω speaker to built-in amplifier terminals
- LEDs: Connect to pin A0 through 200Ω resistor to GND
- Light sensor: Connect photoresistor between 3.3V and A1, with 10kΩ pulldown to GND
- Button: Connect button between D2 and GND (auto-enabled for global control)
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


class ModeManager:
    """Manages mode switching and global button control"""
    
    def __init__(self, crow, config):
        self.crow = crow
        self.config = config
        
        # Load available modes from config with fallback
        self.available_modes = self._load_available_modes()
        
        # Validate that at least default mode is available
        if "default" not in self.available_modes:
            print("⚠️ Warning: 'default' mode not in available_modes, adding it")
            self.available_modes.insert(0, "default")
        
        self.current_mode_name = config.get("mode", "default")
        
        # Validate current mode is in available modes
        if self.current_mode_name not in self.available_modes:
            print(f"⚠️ Warning: configured mode '{self.current_mode_name}' not in available_modes")
            print(f"   Falling back to 'default' mode")
            self.current_mode_name = "default"
        
        self.current_mode_module = None
        
        # Load initial mode
        self.load_mode(self.current_mode_name)
    
    def _load_available_modes(self):
        """Load available modes from config with validation"""
        # Try to get from main config first
        available_modes = self.config.get("available_modes", None)
        
        # If not found, try the underscore version (documentation format)
        if available_modes is None:
            available_modes = self.config.get("_available_modes", None)
        
        # Fallback to default modes if nothing in config
        if available_modes is None:
            print("⚠️ No available_modes found in config, using defaults")
            available_modes = ["default", "debug", "button_test", "battery_monitor"]
        
        # Validate that it's a list
        if not isinstance(available_modes, list):
            print("⚠️ available_modes in config is not a list, using defaults")
            available_modes = ["default", "debug", "button_test", "battery_monitor"]
        
        # Filter out empty strings and ensure all are strings
        available_modes = [str(mode).strip() for mode in available_modes if str(mode).strip()]
        
        if not available_modes:
            print("⚠️ available_modes list is empty, using defaults")
            available_modes = ["default", "debug", "button_test", "battery_monitor"]
        
        print(f"📋 Available modes from config: {available_modes}")
        return available_modes
    
    def _import_mode_safely(self, mode_name):
        """Safely import a mode module - CircuitPython compatible"""
        if mode_name == "default":
            return default_mode
        
        try:
            # Simple approach that works in CircuitPython
            # We'll use exec to dynamically import, which is the most reliable method
            exec(f"import modes.{mode_name} as imported_module")
            return locals()['imported_module']
            
        except ImportError as e:
            print(f"❌ Import error for mode {mode_name}: {e}")
            print(f"   Make sure file 'modes/{mode_name}.py' exists")
            return None
        except SyntaxError as e:
            print(f"❌ Syntax error in mode {mode_name}: {e}")
            print(f"   Check the Python syntax in 'modes/{mode_name}.py'")
            return None
        except Exception as e:
            print(f"❌ Unexpected error importing mode {mode_name}: {e}")
            print(f"   Error type: {type(e).__name__}")
            return None
    
    def load_mode(self, mode_name):
        """Load and initialize a mode module"""        
        print(f"📦 Loading mode: {mode_name}")
        
        # Validate mode is in available modes
        if mode_name not in self.available_modes:
            print(f"❌ Mode '{mode_name}' not in available modes: {self.available_modes}")
            if "default" in self.available_modes:
                print("🔄 Falling back to default mode")
                mode_name = "default"
            else:
                print("💥 Critical: default mode not available!")
                return False
        
        try:
            # Cleanup current mode if it has a cleanup method
            if (self.current_mode_module and 
                hasattr(self.current_mode_module, 'cleanup')):
                try:
                    self.current_mode_module.cleanup(self.crow, self.config)
                except Exception as e:
                    print(f"⚠️ Mode cleanup error: {e}")
            
            # Import new mode using safe import method
            new_module = self._import_mode_safely(mode_name)
            
            if new_module is None:
                if mode_name != "default":
                    print("🔄 Falling back to default mode")
                    return self.load_mode("default")
                else:
                    raise Exception("Cannot load default mode!")
            
            self.current_mode_module = new_module
            self.current_mode_name = mode_name
            
            # Initialize mode if it has an init method
            if hasattr(self.current_mode_module, 'init'):
                try:
                    self.current_mode_module.init(self.crow, self.config)
                except Exception as e:
                    print(f"⚠️ Mode init error: {e}")
            
            print(f"✅ Mode loaded: {mode_name}")
            
            # Flash LEDs to indicate mode (flash N times = mode position)
            try:
                mode_position = self.available_modes.index(mode_name) + 1
                self.crow.leds.flash_eyes(times=mode_position)
            except (ValueError, Exception):
                self.crow.leds.flash_eyes(times=1)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to load mode {mode_name}: {e}")
            print(f"   Error details: {type(e).__name__}: {e}")
            if mode_name != "default":
                print("🔄 Falling back to default mode")
                return self.load_mode("default")
            else:
                raise Exception(f"Cannot load default mode: {e}")
    
    def cycle_mode(self):
        """Switch to the next available mode"""
        try:
            current_index = self.available_modes.index(self.current_mode_name)
        except ValueError:
            print(f"⚠️ Current mode '{self.current_mode_name}' not in available modes")
            current_index = 0
        
        next_index = (current_index + 1) % len(self.available_modes)
        next_mode = self.available_modes[next_index]
        
        print(f"🔄 Mode switching: {self.current_mode_name} → {next_mode}")
        print(f"   ({current_index + 1}/{len(self.available_modes)}) → ({next_index + 1}/{len(self.available_modes)})")
        
        success = self.load_mode(next_mode)
        if not success:
            print("❌ Mode switch failed, staying in current mode")
    
    def handle_button_press(self):
        """Handle short button press - delegate to current mode"""
        if hasattr(self.current_mode_module, 'button_pressed'):
            try:
                print(f"📱 Button press → {self.current_mode_name}.button_pressed()")
                self.current_mode_module.button_pressed(self.crow, self.config)
            except Exception as e:
                print(f"💥 Error in {self.current_mode_name}.button_pressed(): {e}")
                print(f"   Error details: {type(e).__name__}: {e}")
                # Flash error indicator
                self.crow.leds.flash_eyes(times=5)
        else:
            print(f"ℹ️ Mode {self.current_mode_name} doesn't implement button_pressed()")
            # Flash to indicate button was received but no handler
            self.crow.leds.flash_eyes(times=1)
    
    def get_mode_info(self):
        """Get information about current mode and available modes"""
        return {
            "current_mode": self.current_mode_name,
            "available_modes": self.available_modes,
            "current_position": self.available_modes.index(self.current_mode_name) + 1 if self.current_mode_name in self.available_modes else 0,
            "total_modes": len(self.available_modes)
        }


class CrowBird:
    """Main crow bird controller using Prop-Maker Feather and bird libraries"""
    
    def __init__(self, config):
        """Initialize all bird components"""
        self.config = config
        self.setup_power()
        self.setup_components()
        print("🐦 Crow Bird initialized with config-driven modes")
        
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
        
        # Global button setup - auto-enable for mode switching
        self.setup_global_button()
        
        print("All components initialized!")
    
    def setup_global_button(self):
        """Setup global button for mode switching and mode actions"""
        button_config = self.config.get("button", {})
        button_enabled = button_config.get("enabled", True)  # Auto-enable by default
        
        # Auto-enable button if not explicitly configured
        if button_enabled or "button" not in self.config:
            try:
                from button import Button
                button_pin_name = button_config.get("pin", "D6")
                button_pin = getattr(board, button_pin_name)
                
                # Create button for global control
                self.button = Button(
                    button_pin,
                    debounce_ms=button_config.get("debounce_ms", 50),
                    long_press_ms=button_config.get("long_press_ms", 1500),  # Longer for mode switching
                    double_press_window_ms=button_config.get("double_press_window_ms", 500)
                )
                
                print(f"✅ Global button ready on pin {button_pin_name}")
                print(f"   Long press (≥{button_config.get('long_press_ms', 1500)}ms): Cycle modes")
                print(f"   Short press (<{button_config.get('long_press_ms', 1500)}ms): Mode action")
                
            except Exception as e:
                print(f"⚠️ Global button setup failed: {e}")
                print("   Mode switching disabled, but all modes will work normally")
                self.button = None
        else:
            self.button = None
            print("ℹ️ Button explicitly disabled - no global mode control")
    
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
                
            # Clean up button if enabled
            if hasattr(self, 'button') and self.button:
                self.button.deinit()
                
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
        print("Using default settings with global button control")
        # Return a minimal working config
        return {
            "mode": "default",
            "available_modes": ["default", "debug"],
            "pins": {"led": "A0", "light_sensor": "A1", "battery": ""},
            "battery": {"enabled": False},
            "button": {"enabled": True, "pin": "D6", "long_press_ms": 1500},
            "audio": {"directory": "audio", "sample_rate": 11000, "volume": 0.6},
            "sensors": {"light_threshold": 1000},
            "leds": {"max_brightness": 0.8},
            "servo": {"speed": 0.02, "pause": 0.5},
            "behavior": {"night_flash_count": 2}
        }


def main():
    """Main entry point with global button control and configurable mode management"""
    print("🐦 Crow Bird starting with Config-Driven Modes! 🐦")
    print("=" * 60)
    print("GLOBAL BUTTON CONTROLS:")
    print("  Long press (1500ms+) = Cycle through available modes")
    print("  Short press (<1500ms) = Current mode action")
    print("MODES ARE NOW CONFIGURED IN config.json!")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    
    try:
        # Create and initialize bird
        crow = CrowBird(config)
        
        # Create mode manager for mode switching
        mode_manager = ModeManager(crow, config)
        
        # Display mode information
        mode_info = mode_manager.get_mode_info()
        print(f"🚀 Starting in mode: {mode_info['current_mode']}")
        print(f"Available modes: {' → '.join(mode_info['available_modes'])}")
        print(f"Mode position: {mode_info['current_position']}/{mode_info['total_modes']}")
        print()
        
        # Set up global button controls if button is available
        if crow.button:
            def on_long_press():
                print("\n🔄 LONG PRESS DETECTED - Cycling modes...")
                mode_manager.cycle_mode()
                mode_info = mode_manager.get_mode_info()
                print(f"Now in mode: {mode_info['current_mode']} ({mode_info['current_position']}/{mode_info['total_modes']})")
                print("Ready for button input...\n")
            
            def on_short_press():
                print(f"\n📱 SHORT PRESS DETECTED - Mode: {mode_manager.current_mode_name}")
                mode_manager.handle_button_press()
                print("Ready for button input...\n")
            
            # Set global button callbacks
            crow.button.set_callbacks(
                on_press=on_short_press,
                on_long_press=on_long_press
            )
            
            print(f"🎮 Global Button Control Active:")
            print(f"   Pin: {config.get('button', {}).get('pin', 'D2')}")
            print(f"   Long press: Cycle modes")
            print(f"   Short press: Mode-specific action")
            print()
        else:
            print("⚠️ No button available - using mode from config only")
            print()
        
        # Main control loop with global button handling
        while True:
            try:
                # Update global button (this handles mode switching)
                if crow.button:
                    crow.button.update()
                
                # Run current mode (non-blocking check)
                if hasattr(mode_manager.current_mode_module, 'run'):
                    # Some modes are blocking, others are not
                    # We'll call run() and let the mode handle its own timing
                    mode_manager.current_mode_module.run(crow, config)
                    break  # Mode completed, exit main loop
                else:
                    print(f"❌ Mode {mode_manager.current_mode_name} has no run() method")
                    mode_manager.load_mode("default")
                
                # Small delay for button responsiveness
                time.sleep(0.01)
                
            except KeyboardInterrupt:
                print("\n🛑 Interrupted by user")
                break
            except Exception as e:
                print(f"💥 Fatal error in main loop: {e}")
                print(f"   Error details: {type(e).__name__}: {e}")
                # Try to flash LEDs to indicate error
                try:
                    crow.leds.flash_eyes(times=10)
                except:
                    pass
                break
                
    except Exception as e:
        print(f"💥 Fatal startup error: {e}")
        print(f"   Error details: {type(e).__name__}: {e}")
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