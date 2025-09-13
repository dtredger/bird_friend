"""
Debug Mode - Component Testing
=========================================================

This mode inherits all the default bird behavior and overrides
the button press to cycle through component tests.

Inherits from BaseMode:
- Automatic button handling ✅
- Standard timed bird actions ✅ 
- All cleanup and error handling ✅
- Just overrides button behavior for testing ✅
"""

import time
from base_mode import BaseMode


class DebugMode(BaseMode):
    """Debug mode - cycles through component tests on button press"""
    
    def __init__(self):
        super().__init__()
        self.test_index = 0
        
        # Define test sequence
        self.tests = [
            ("Battery Test", self.test_battery),
            ("LED Test", self.test_leds),
            ("Servo Test", self.test_servo),
            ("Light Sensor Test", self.test_light_sensor),
            ("Audio Test", self.test_audio),
            ("Full Action Test", self.test_full_action),
            ("System Info", self.system_info)
        ]
        
    def mode_init(self, crow, config):
        """Initialize debug mode"""
        print("🔧 Debug mode initializing...")
        self.test_index = 0
        print("✅ Debug mode ready - press button to run tests")
    
    def on_button_press(self, crow, config):
        """Override button behavior to cycle through tests instead of default action"""
        if self.test_index >= len(self.tests):
            self.test_index = 0
            print("\n🔄 Restarting test sequence...")
        
        test_name, test_func = self.tests[self.test_index]
        
        print(f"\n--- Test {self.test_index + 1}/{len(self.tests)}: {test_name} ---")
        
        try:
            test_func(crow, config)
            print(f"✅ {test_name} completed")
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            crow.leds.flash_eyes(times=5)
        
        self.test_index += 1
        
        if self.test_index >= len(self.tests):
            print(f"\n🎉 All {len(self.tests)} tests completed!")
        else:
            next_test_name, _ = self.tests[self.test_index]
            print(f"Next test: {next_test_name}")
    
    def show_mode_info(self, crow, config):
        """Override to show debug-specific info"""
        interval_minutes = self.action_interval / 60
        print("🔧 Debug Mode - Component Testing")
        print(f"   Default bird actions every {interval_minutes:.0f} minutes")
        print(f"   {len(self.tests)} component tests available")
        print("Button controls:")
        print("  Short press: Run next component test")
        print("  Long press: Exit to next mode")
        print("  (Standard bird actions happen automatically)")
        print("=" * 50)
    
    # Test methods - simplified versions
    def test_battery(self, crow, config):
        """Quick battery test"""
        if crow.battery:
            status = crow.battery.get_status()
            print(f"  Battery: {status['voltage']}V ({status['percentage']}%) - {status['level']}")
        else:
            print("  ❌ Battery monitoring not available")

    def test_leds(self, crow, config):
        """Quick LED test"""
        print("  Testing LEDs...")
        crow.leds.fade_in()
        time.sleep(0.5)
        crow.leds.fade_out()

    def test_servo(self, crow, config):
        """Quick servo test"""
        print("  Testing servo...")
        crow.servo.to_top()
        time.sleep(0.5)
        crow.servo.to_bottom()
        time.sleep(0.5)
        crow.servo.to_midpoint()

    def test_light_sensor(self, crow, config):
        """Quick light sensor test"""
        reading = crow.light_sensor.read()
        sufficient = crow.light_sensor.over_minimum()
        print(f"  Light: {reading} (sufficient: {sufficient})")

    def test_audio(self, crow, config):
        """Quick audio test"""
        print("  Testing audio...")
        crow.amplifier.play_tone(frequency=440, duration=0.3, volume=0.3)

    def test_full_action(self, crow, config):
        """Test the inherited default action"""
        print("  Testing full action sequence...")
        # Just call the inherited perform_action method!
        self.perform_action(crow, config)

    def system_info(self, crow, config):
        """Show system info"""
        print(f"  Mode: {self.mode_name}")
        print(f"  Audio dir: {config['audio']['directory']}")
        print(f"  Light threshold: {config['sensors']['light_threshold']}")
        print(f"  Interval: {self.action_interval/60:.0f} minutes")
