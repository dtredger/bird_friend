"""
Debug Mode - Component Testing and Diagnostics
==============================================

This mode tests all components individually and provides
detailed diagnostic information. Useful for troubleshooting
hardware issues and verifying proper setup.

Tests performed:
- Battery monitoring and voltage readings
- LED brightness and fading
- Servo movement and positioning
- Light sensor readings and calibration
- Audio playback and volume
- System information
"""

import time
# Import the default mode to access core light_rotate_hoot function
import modes.default as default_mode


def test_battery(crow, config):
    """Test battery monitoring"""
    print("\n--- Battery Test ---")
    if crow.battery:
        for i in range(3):
            status = crow.battery.get_status()
            print(f"Reading {i+1}:")
            print(f"  Raw ADC: {status['raw_adc']}")
            print(f"  Voltage: {status['voltage']}V")
            print(f"  Percentage: {status['percentage']}%")
            print(f"  Level: {status['level']}")
            print(f"  Low battery: {crow.battery.is_low_battery()}")
            print(f"  Critical: {crow.battery.is_critical_battery()}")
            time.sleep(1)
        crow.battery.log_status()
    else:
        print("❌ Battery monitoring not available")


def test_leds(crow, config):
    """Test LED functionality"""
    print("\n--- LED Test ---")
    
    # Test basic on/off
    print("Testing basic on/off...")
    crow.leds.turn_on()
    time.sleep(1)
    crow.leds.turn_off()
    time.sleep(0.5)
    
    # Test brightness levels
    print("Testing brightness levels...")
    for brightness in [0.2, 0.5, 0.8, 1.0]:
        print(f"  Brightness: {brightness}")
        crow.leds.set_brightness(brightness)
        time.sleep(0.8)
    crow.leds.turn_off()
    
    # Test fade in/out
    print("Testing fade effects...")
    crow.leds.fade_in()
    time.sleep(0.5)
    crow.leds.fade_out()
    
    # Test flash pattern
    print("Testing flash pattern...")
    crow.leds.flash_eyes(times=3)


def test_servo(crow, config):
    """Test servo movement"""
    print("\n--- Servo Test ---")
    
    print("Testing individual movements...")
    print("  Moving to center...")
    crow.servo.to_midpoint()
    time.sleep(1)
    
    print("  Moving to top...")
    crow.servo.to_top()
    time.sleep(1)
    
    print("  Moving to bottom...")
    crow.servo.to_bottom()
    time.sleep(1)
    
    print("  Returning to center...")
    crow.servo.to_midpoint()
    time.sleep(1)
    
    print("Testing full sweep...")
    crow.servo.sweep()


def test_light_sensor(crow, config):
    """Test light sensor readings"""
    print("\n--- Light Sensor Test ---")
    
    current_threshold = crow.light_sensor.threshold
    print(f"Current threshold: {current_threshold}")
    
    print("Taking 10 readings...")
    readings = []
    for i in range(10):
        reading = crow.light_sensor.read()
        stable_reading = crow.light_sensor.read_stable()
        over_min = crow.light_sensor.over_minimum()
        voltage = crow.light_sensor.voltage()
        
        readings.append(reading)
        print(f"  Reading {i+1}: {reading} (stable: {stable_reading}, sufficient: {over_min}, voltage: {voltage:.2f}V)")
        time.sleep(0.5)
    
    avg_reading = sum(readings) // len(readings)
    min_reading = min(readings)
    max_reading = max(readings)
    
    print(f"Statistics:")
    print(f"  Average: {avg_reading}")
    print(f"  Min: {min_reading}")
    print(f"  Max: {max_reading}")
    print(f"  Variance: {max_reading - min_reading}")
    
    # Log a reading
    crow.light_sensor.log_reading()
    print("Sample reading logged to sensor_log.txt")


def test_audio(crow, config):
    """Test audio functionality"""
    print("\n--- Audio Test ---")
    
    # Test tone generation
    print("Testing tone generation...")
    frequencies = [440, 523, 659, 784]  # A, C, E, G notes
    for freq in frequencies:
        print(f"  Playing {freq}Hz...")
        crow.amplifier.play_tone(frequency=freq, duration=0.5, volume=0.3)
        time.sleep(0.2)
    
    # Test volume levels
    print("Testing volume levels...")
    for volume in [0.2, 0.5, 0.8]:
        print(f"  Volume: {volume}")
        crow.amplifier.set_volume(volume)
        crow.amplifier.play_tone(frequency=440, duration=0.5)
        time.sleep(0.2)
    
    # Restore original volume
    crow.amplifier.set_volume(config["audio"]["volume"])
    
    # Test WAV playback
    print("Testing WAV file playback...")
    try:
        crow.amplifier.play_wav()
        print("  WAV playback successful")
    except Exception as e:
        print(f"  WAV playback failed: {e}")


def test_full_action_sequence(crow, config):
    """Test the complete action sequence using default mode's function"""
    print("\n--- Full Action Sequence Test ---")
    print("Using core light_rotate_hoot function from default mode...")
    default_mode.light_rotate_hoot(crow)


def system_info(crow, config):
    """Display system information"""
    print("\n--- System Information ---")
    print(f"Mode: debug")
    print(f"Config file loaded: config.json")
    print(f"Audio directory: {config['audio']['directory']}")
    print(f"Sample rate: {config['audio']['sample_rate']}")
    print(f"Interval: {config.get('interval_minutes', 60)} minutes")
    print(f"Light threshold: {config['sensors']['light_threshold']}")
    print(f"LED max brightness: {config['leds']['max_brightness']}")
    print(f"Servo speed: {config['servo']['speed']}")
    
    # Check for audio files
    try:
        import os
        audio_dir = config['audio']['directory']
        files = [f for f in os.listdir(audio_dir) if f.lower().endswith('.wav')]
        print(f"Audio files found: {len(files)}")
        for file in files[:5]:  # Show first 5
            print(f"  - {file}")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")
    except Exception as e:
        print(f"Could not list audio files: {e}")


def run(crow, config):
    """Run debug mode - comprehensive component testing"""
    print("🔧 Starting debug mode - component testing and diagnostics")
    print("Core functionality imported from default mode")
    
    try:
        # Display system info
        system_info(crow, config)
        
        # Test each component
        test_battery(crow, config)
        test_leds(crow, config)
        test_servo(crow, config)
        test_light_sensor(crow, config)
        test_audio(crow, config)
        
        # Test full sequence using default mode's function
        test_full_action_sequence(crow, config)
        
        print("\n✅ All component tests completed!")
        print("Debug mode finished - check output for any issues")
        
    except KeyboardInterrupt:
        print("\n🛑 Debug mode interrupted")
    except Exception as e:
        print(f"💥 Error in debug mode: {e}")
        crow.leds.flash_eyes(times=10)  # Error indication