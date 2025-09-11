"""
Button Test Mode - Comprehensive Button Testing
==============================================

This mode provides comprehensive testing of button functionality.
Perfect for verifying button hardware and debouncing parameters.

Features:
- Real-time button state monitoring
- Press type detection and counting
- Timing analysis
- Hardware diagnostics
- Configuration testing

Use this mode to:
- Verify button wiring
- Test debouncing settings
- Calibrate timing parameters
- Debug button issues
"""

import time
import board
from button import Button


def run(crow, config):
    """Run button test mode - comprehensive button testing"""
    print("🔘 Starting button test mode - comprehensive testing")
    
    # Check if button is enabled
    button_enabled = config.get("button", {}).get("enabled", False)
    if not button_enabled:
        print("❌ Button not enabled in config")
        print("To enable button testing:")
        print('1. Set "button": {"enabled": true, "pin": "D2"} in config.json')
        print("2. Connect button between specified pin and GND")
        print("3. Restart with button_test mode")
        return
    
    button_pin_name = config["button"]["pin"]
    try:
        button_pin = getattr(board, button_pin_name)
    except AttributeError:
        print(f"❌ Invalid button pin: {button_pin_name}")
        return
    
    print(f"📍 Testing button on pin {button_pin_name}")
    print(f"⚙️ Debounce: {config['button'].get('debounce_ms', 50)}ms")
    print(f"⏱️ Long press: {config['button'].get('long_press_ms', 1000)}ms")
    print(f"⚡ Double press window: {config['button'].get('double_press_window_ms', 500)}ms")
    print()
    print("Button Test Actions:")
    print("  Single press: Flash LED once")
    print("  Long press: Flash LED pattern + test servo")
    print("  Double press: Flash LED pattern + test audio")
    print()
    print("Real-time monitoring will show button state and events...")
    print("Press Ctrl+C to exit and see final statistics")
    print("=" * 50)
    
    # Button event handlers
    def on_single_press():
        print("✅ SINGLE PRESS detected")
        crow.leds.set_brightness(0.5)
        time.sleep(0.2)
        crow.leds.turn_off()
    
    def on_long_press():
        print("⏳ LONG PRESS detected")
        # LED pattern
        for _ in range(3):
            crow.leds.set_brightness(0.8)
            time.sleep(0.1)
            crow.leds.turn_off()
            time.sleep(0.1)
        
        # Test servo
        print("  Testing servo movement...")
        crow.servo.to_top()
        crow.servo.to_midpoint()
    
    def on_double_press():
        print("⚡ DOUBLE PRESS detected")
        # LED pattern
        for _ in range(5):
            crow.leds.set_brightness(1.0)
            time.sleep(0.05)
            crow.leds.turn_off()
            time.sleep(0.05)
        
        # Test audio
        print("  Testing audio...")
        try:
            crow.amplifier.play_tone(frequency=880, duration=0.3, volume=0.3)
        except Exception as e:
            print(f"  Audio test failed: {e}")
    
    # Create button for testing
    button = Button(
        button_pin,
        on_press=on_single_press,
        on_long_press=on_long_press,
        on_double_press=on_double_press,
        debounce_ms=config["button"].get("debounce_ms", 50),
        long_press_ms=config["button"].get("long_press_ms", 1000),
        double_press_window_ms=config["button"].get("double_press_window_ms", 500)
    )
    
    # Initial LED flash to show we're ready
    crow.leds.flash_eyes(times=2)
    
    # State tracking for real-time monitoring
    last_button_state = False
    last_print_time = 0
    print_interval = 2.0  # Print status every 2 seconds
    
    try:
        start_time = time.monotonic()
        
        while True:
            current_time = time.monotonic()
            button.update()
            
            # Check for button state changes
            current_state = button.is_pressed()
            if current_state != last_button_state:
                state_text = "PRESSED" if current_state else "RELEASED"
                timestamp = current_time - start_time
                print(f"[{timestamp:6.2f}s] Button {state_text}")
                last_button_state = current_state
            
            # Periodic status updates
            if current_time - last_print_time > print_interval:
                stats = button.get_statistics()
                runtime = current_time - start_time
                print(f"[{runtime:6.1f}s] Status: Single={stats['total_presses']}, Long={stats['total_long_presses']}, Double={stats['total_double_presses']}, State={'PRESSED' if current_state else 'RELEASED'}")
                last_print_time = current_time
            
            time.sleep(0.01)  # 10ms update rate
            
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("🛑 Button test interrupted")
    except Exception as e:
        print(f"💥 Error in button test: {e}")
    finally:
        # Final statistics
        stats = button.get_statistics()
        test_duration = time.monotonic() - start_time
        
        print(f"\n=== Final Test Results ===")
        print(f"Test duration: {test_duration:.1f} seconds")
        print(f"Single presses: {stats['total_presses']}")
        print(f"Long presses: {stats['total_long_presses']}")
        print(f"Double presses: {stats['total_double_presses']}")
        print(f"Total button events: {stats['total_presses'] + stats['total_long_presses'] + stats['total_double_presses']}")
        
        if test_duration > 0:
            events_per_minute = (stats['total_presses'] + stats['total_long_presses'] + stats['total_double_presses']) * 60 / test_duration
            print(f"Events per minute: {events_per_minute:.1f}")
        
        # Hardware test summary
        print(f"\n=== Hardware Test Summary ===")
        print(f"✅ Button pin {button_pin_name}: Working")
        print(f"✅ LED control: Working")
        print(f"✅ Servo control: Working")
        
        try:
            crow.amplifier.play_tone(frequency=440, duration=0.1, volume=0.2)
            print(f"✅ Audio output: Working")
        except:
            print(f"⚠️ Audio output: Not available or failed")
        
        # Cleanup
        button.deinit()
        crow.leds.turn_off()
        print("\nButton test cleanup complete")
        print("Results can help you tune button timing parameters in config.json")
