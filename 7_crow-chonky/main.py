"""
Crow Bird for Adafruit RP2040 Prop-Maker Feather - Global Button Control System
===============================================================================

This is the main entry point with global button control for mode switching.

Global Button Controls:
- Long press (1500ms+): Cycle through available modes
- Short press (<1500ms): Call current mode's button_pressed() method

Available modes cycle: default → debug → demo → manual → button_test → battery_monitor → single

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
        
        # Available modes in cycle order
        self.available_modes = [
            "default", "debug", "demo", "manual", 
            "button_test", "battery_monitor", "single"
        ]
        
        self.current_mode_name = config.get("mode", "default")
        self.current_mode_module = None
        
        # Load initial mode
        self.load_mode(self.current_mode_name)
    
    def load_mode(self, mode_name):
        """Load and initialize a mode module"""
        # Map 'normal' to 'default' for backwards compatibility
        if mode_name == "normal":
            mode_name = "default"
        
        print(f"📦 Loading mode: {mode_name}")
        
        try:
            # Cleanup current mode if it has a cleanup method
            if (self.current_mode_module and 
                hasattr(self.current_mode_module, 'cleanup')):
                try:
                    self.current_mode_module.cleanup(self.crow, self.config)
                except Exception as e:
                    print(f"⚠️ Mode cleanup error: {e}")
            
            # Import new mode
            if mode_name == "default":
                self.current_mode_module = default_mode
            else:
                module_name = f"modes.{mode_name}"
                self.current_mode_module = __import__(module_name, fromlist=[mode_name])
            
            self.current_mode_name = mode_name
            
            # Initialize mode if it has an init method
            if hasattr(self.current_mode_module, 'init'):
                self.current_mode_module.init(self.crow, self.config)
            
            print(f"✅ Mode loaded: {mode_name}")
            
            # Flash LEDs to indicate mode (flash N times = mode position)
            try:
                mode_position = self.available_modes.index(mode_name) + 1
                self.crow.leds.flash_eyes(times=mode_position)
            except (ValueError, Exception):
                self.crow.leds.flash_eyes(times=1)
            
        except Exception as e:
            print(f"❌ Failed to load mode {mode_name}: {e}")
            if mode_name != "default":
                print("🔄 Falling back to default mode")
                self.load_mode("default")
    
    def cycle_mode(self):
        """Switch to the next available mode"""
        try:
            current_index = self.available_modes.index(self.current_mode_name)
        except ValueError:
            current_index = 0
        
        next_index = (current_index + 1) % len(self.available_modes)
        next_mode = self.available_modes[next_index]
        
        print(f"🔄 Mode switching: {self.current_mode_name} → {next_mode}")
        print(f"   ({current_index + 1}/{len(self.available_modes)}) → ({next_index + 1}/{len(self.available_modes)})")
        
        self.load_mode(next_mode)
    
    def handle_button_press(self):
        """Handle short button press - delegate to current mode"""
        if hasattr(self.current_mode_module, 'button_pressed'):
            try:
                print(f"📱 Button press → {self.current_mode_name}.button_pressed()")
                self.current_mode_module.button_pressed(self.crow, self.config)
            except Exception as e:
                print(f"💥 Error in {self.current_mode_name}.button_pressed(): {e}")
                # Flash error indicator
                self.crow.leds.flash_eyes(times=5)
        else:
            print(f"ℹ️ Mode {self.current_mode_name} doesn't implement button_pressed()")
            # Flash to indicate button was received but no handler
            self.crow.leds.flash_eyes(times=1)


class CrowBird:
    """Main crow bird controller using Prop-Maker Feather and bird libraries"""
    
    def __init__(self, config):
        """Initialize all bird components"""
        self.config = config
        self.setup_power()
        self.setup_components()
        print("🐦 Crow Bird initialized with global button control")
        
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
                button_pin_name = button_config.get("pin", "D2")
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
        return None


def main():
    """Main entry point with global button control and mode management"""
    print("🐦 Crow Bird starting with Global Button Control! 🐦")
    print("=" * 60)
    print("GLOBAL BUTTON CONTROLS:")
    print("  Long press (1500ms+) = Cycle through modes")
    print("  Short press (<1500ms) = Current mode action")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    
    try:
        # Create and initialize bird
        crow = CrowBird(config)
        
        # Create mode manager for mode switching
        mode_manager = ModeManager(crow, config)
        
        # Set up global button controls if button is available
        if crow.button:
            def on_long_press():
                print("\n🔄 LONG PRESS DETECTED - Cycling modes...")
                mode_manager.cycle_mode()
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
        
        print(f"🚀 Starting in mode: {mode_manager.current_mode_name}")
        print(f"Available modes: {' → '.join(mode_manager.available_modes)}")
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
                # Try to flash LEDs to indicate error
                try:
                    crow.leds.flash_eyes(times=10)
                except:
                    pass
                break
                
    except Exception as e:
        print(f"💥 Fatal startup error: {e}")
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