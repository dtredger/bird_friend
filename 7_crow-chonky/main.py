"""
Crow Bird for Adafruit RP2040 Prop-Maker Feather
================================================

Implements the same logic as 7_crow-chonky/main.py but uses the Prop-Maker Feather's
built-in servo header, I2S audio amplifier, and the CircuitPython bird libraries.

Hardware Setup:
- Servo: Plug directly into built-in 3-pin servo header (no wiring needed)
- Speaker: Connect 4-8Ω speaker to built-in amplifier terminals (+ and -)  
- LEDs: Connect to pin A0 through 200Ω resistor to GND
- Light sensor: Connect photoresistor between 3.3V and A1, with 10kΩ pulldown to GND
- Battery monitoring: Connect voltage divider (BAT → 100kΩ → A3 → 100kΩ → GND)

The bird will:
- Check light level every INTERVAL_MINUTES 
- If bright enough: light eyes, move servo, play sounds
- If too dark: just flash eyes briefly
- Log sensor data and battery status if DEBUG is enabled
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

# Import our battery monitoring library
try:
    from battery import Battery
    BATTERY_AVAILABLE = True
except ImportError:
    print("⚠️ battery.py not found - battery monitoring disabled")
    BATTERY_AVAILABLE = False

# === CONFIGURATION ===
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
        return {
            "debug": True,
            "interval_minutes": 60,
            "pins": {
                "led": "A0",
                "light_sensor": "A1",
                "battery": "A3"
            },
            "audio": {
                "directory": "audio",
                "volume": 1.0
            },
            "sensors": {
                "light_threshold": 25000
            }
        }

# Load configuration
config = load_config()
DEBUG = config.get("debug", True)
INTERVAL_MINUTES = config.get("interval_minutes", 60)

class CrowBird:
    """Main crow bird controller using Prop-Maker Feather and bird libraries"""
    
    def __init__(self):
        """Initialize all bird components"""
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
        
        # LED setup using our Leds library
        led_pin = getattr(board, config["pins"]["led"])
        self.leds = Leds(led_pin)
        print("✅ LEDs ready")
        
        # Light sensor setup using our LightSensor library
        light_pin = getattr(board, config["pins"]["light_sensor"])
        self.light_sensor = LightSensor(light_pin)
        # Override threshold from config
        self.light_sensor.threshold = config["sensors"]["light_threshold"]
        print("✅ Light sensor ready")
        
        # Battery monitoring setup using our Battery library
        if BATTERY_AVAILABLE:
            battery_pin = getattr(board, config["pins"]["battery"])
            self.battery = Battery(battery_pin)
            print("✅ Battery monitoring ready")
        else:
            self.battery = None
            print("⚠️ Battery monitoring disabled")
        
        # Servo setup using our Servo library with built-in header
        self.servo = Servo(board.EXTERNAL_SERVO)
        print("✅ Servo ready")
        
        # Audio setup using our Amplifier library with built-in I2S
        self.amplifier = Amplifier(
            board.I2S_WORD_SELECT,
            board.I2S_BIT_CLOCK, 
            board.I2S_DATA,
            audio_dir=config["audio"]["directory"]
        )
        self.amplifier.set_volume(config["audio"]["volume"])
        print("✅ Audio ready")
        
        print("All components initialized!")
    
    def light_rotate_hoot(self):
        """Main bird action sequence - light eyes, rotate head, make sounds"""
        print("🐦 Performing bird action sequence...")
        
        # Check battery level before intensive actions
        if self.battery and self.battery.is_critical_battery():
            print("⚠️ Critical battery - skipping action to preserve power")
            self.leds.flash_eyes(times=5)  # Warning flash
            return
        
        # Light up eyes using our Leds library
        self.leds.fade_in()
        
        # Move to top and play sound
        self.servo.to_top()
        self.amplifier.play_wav()
        
        time.sleep(0.5)
        
        # Move to bottom and play sound
        self.servo.to_bottom() 
        self.amplifier.play_wav()
        
        time.sleep(0.5)
        
        # Return to center and fade out eyes
        self.servo.to_midpoint()
        self.leds.fade_out()
        
        print("Action sequence complete!")
    
    def timed_actions(self):
        """Check conditions and perform appropriate action"""
        print(f"\n=== Timed Action Check ===")
        print(f"Time: {time.localtime()}")
        
        # Log sensor data if debugging
        if DEBUG:
            self.light_sensor.log_reading()
            if self.battery:
                self.battery.log_status()
        
        # Check battery status using our Battery library
        if self.battery:
            battery_status = self.battery.get_status()
            print(f"🔋 Battery: {battery_status['voltage']}V ({battery_status['percentage']}%)")
            
            if self.battery.is_low_battery():
                print("🔋 Low battery warning")
            if self.battery.is_critical_battery():
                print("⚠️ CRITICAL BATTERY!")
        else:
            print("🔋 Battery monitoring not available")
            
        # Check light level using our LightSensor library
        light_reading = self.light_sensor.read()
        light_sufficient = self.light_sensor.over_minimum()
        
        print(f"Light reading: {light_reading}")
        print(f"Light sufficient: {light_sufficient}")
        
        if light_sufficient:
            print("Sufficient light - performing full action")
            self.light_rotate_hoot()
        else:
            print("Insufficient light - just flashing eyes")
            self.leds.flash_eyes()
            
        print("=== Check Complete ===\n")
    
    def test_all_components(self):
        """Test all components individually"""
        print("\n=== Component Test Mode ===")
        
        # Test battery monitoring using our PropMakerBattery library
        if self.battery:
            print("Testing battery monitoring...")
            status = self.battery.get_status()
            print(f"Battery: {status['voltage']}V ({status['percentage']}%)")
            print(f"Battery level: {status['level']}")
            self.battery.log_status()
        else:
            print("Battery monitoring not available")
        time.sleep(1)
        
        # Test LEDs
        print("Testing LEDs...")
        self.leds.flash_eyes(times=3)
        time.sleep(1)
        
        # Test servo
        print("Testing servo...")
        self.servo.sweep()  # Use the sweep method from our Servo library
        time.sleep(1)
        
        # Test light sensor
        print("Testing light sensor...")
        for i in range(5):
            reading = self.light_sensor.read()
            over_min = self.light_sensor.over_minimum()
            print(f"Light reading {i+1}: {reading} (sufficient: {over_min})")
            time.sleep(0.5)
        
        # Test audio
        print("Testing audio...")
        self.amplifier.play_wav()
        
        print("All component tests complete!")
    
    def run_main_loop(self):
        """Run the main program loop"""
        print(f"Starting main loop - checking every {INTERVAL_MINUTES} minutes")
        
        # Initial action on startup
        self.timed_actions()
        
        # Main loop
        while True:
            try:
                # Sleep for the specified interval
                sleep_seconds = INTERVAL_MINUTES * 60
                print(f"Sleeping for {INTERVAL_MINUTES} minutes...")
                time.sleep(sleep_seconds)
                
                # Perform timed actions
                self.timed_actions()
                
            except KeyboardInterrupt:
                print("\nShutting down...")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                # Flash eyes to indicate error
                self.leds.flash_eyes(times=5)
                time.sleep(5)  # Wait before retrying
    
    def cleanup(self):
        """Clean up resources using library deinit methods"""
        print("Cleaning up...")
        try:
            if hasattr(self, 'leds'):
                self.leds.deinit()
            if hasattr(self, 'servo'):
                self.servo.deinit()
            if hasattr(self, 'light_sensor'):
                self.light_sensor.deinit()
            if hasattr(self, 'amplifier'):
                self.amplifier.deinit()
            if hasattr(self, 'battery') and self.battery:
                self.battery.deinit()
            self.external_power.value = False
        except Exception as e:
            print(f"Cleanup error: {e}")


def main():
    """Main entry point"""
    print("🐦 Crow Bird starting on Prop-Maker Feather! 🐦")
    print("Using CircuitPython bird libraries with battery monitoring")
    
    try:
        # Create and initialize bird
        crow = CrowBird()
        
        # Choose mode - uncomment one of these:
        
        # 1. Test mode - test all components once then stop
        if DEBUG:
            crow.test_all_components()
        
        # 2. Normal mode - run continuous timed loop  
        crow.run_main_loop()
        
        # 3. Single action test
        # crow.light_rotate_hoot()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        # Try to flash LEDs to indicate error
        try:
            from leds import Leds
            error_leds = Leds(board.A0)
            error_leds.flash_eyes(times=10)
            error_leds.deinit()
        except:
            pass
    finally:
        # Clean up
        if 'crow' in locals():
            crow.cleanup()
        print("Crow bird shut down complete.")


if __name__ == "__main__":
    main()