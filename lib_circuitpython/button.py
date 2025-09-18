"""
Button Module for CircuitPython Bird Projects
============================================

Provides debounced button input with callback functionality.
Supports single press, long press, and double press detection.

Hardware Setup:
- Connect button between GPIO pin and GND (uses internal pull-up)
- Or connect button between GPIO pin and 3.3V (uses internal pull-down)
- External pull-up/pull-down resistors (10kΩ) can also be used

Example Usage:
    from button import Button
    
    def on_button_press():
        print("Button pressed!")
    
    button = Button(board.D6, on_press=on_button_press)
    
    # In main loop:
    while True:
        button.update()  # Call this regularly to check button state
        time.sleep(0.01)
"""

import time
import digitalio


class Button:
    """
    Debounced button with callback support and multiple press detection.
    """

    def __init__(self, pin, on_press=None, on_long_press=None, on_double_press=None,
                 pull=digitalio.Pull.UP, debounce_ms=50, long_press_ms=1000,
                 double_press_window_ms=500):
        """
        Args:
            pin: CircuitPython pin object (e.g., board.D6)
            on_press: Callback function for single press (optional)
            on_long_press: Callback function for long press (optional)
            on_double_press: Callback function for double press (optional)
            pull: digitalio.Pull.UP or digitalio.Pull.DOWN
            debounce_ms: Debounce time in milliseconds
            long_press_ms: Time for long press detection in milliseconds
            double_press_window_ms: Time window for double press detection
        """
        self.pin_obj = digitalio.DigitalInOut(pin)
        self.pin_obj.direction = digitalio.Direction.INPUT
        self.pin_obj.pull = pull

        # Determine pressed state based on pull resistor
        self.pressed_state = False if pull == digitalio.Pull.UP else True

        # Callback functions
        self.on_press = on_press
        self.on_long_press = on_long_press
        self.on_double_press = on_double_press

        # Timing parameters (convert to seconds)
        self.debounce_time = debounce_ms / 1000.0
        self.long_press_time = long_press_ms / 1000.0
        self.double_press_window = double_press_window_ms / 1000.0

        # Initialize current time FIRST
        current_time = time.monotonic()

        # State tracking - initialize with current pin state
        self.last_state = self.pin_obj.value == self.pressed_state
        self.last_change_time = current_time
        self.press_start_time = 0
        self.last_press_time = 0
        self.press_count = 0
        self.long_press_triggered = False

        # Statistics
        self.total_presses = 0
        self.total_long_presses = 0
        self.total_double_presses = 0

        # Small stabilization delay to let pin settle
        time.sleep(0.01)

    def update(self):
        """
        Update button state and trigger callbacks.
        Call this method regularly (every 10ms or so) in your main loop.
        """
        current_time = time.monotonic()
        current_state = self.pin_obj.value == self.pressed_state
        
        # Check for state change with debouncing
        if current_state != self.last_state:
            if current_time - self.last_change_time > self.debounce_time:
                self.last_change_time = current_time
                self.last_state = current_state
                
                if current_state:  # Button pressed
                    self._on_button_pressed(current_time)
                else:  # Button released
                    self._on_button_released(current_time)
        
        # Check for long press while button is held
        if (current_state and not self.long_press_triggered and 
            current_time - self.press_start_time > self.long_press_time):
            self._trigger_long_press()
        
        # Check for double press timeout
        if (self.press_count > 0 and 
            current_time - self.last_press_time > self.double_press_window):
            self._process_pending_presses()

    def _on_button_pressed(self, current_time):
        """Handle button press event"""
        self.press_start_time = current_time
        self.long_press_triggered = False

    def _on_button_released(self, current_time):
        """Handle button release event"""
        press_duration = current_time - self.press_start_time
        
        # Only count as press if it wasn't a long press and lasted reasonable time
        if not self.long_press_triggered and press_duration > self.debounce_time:
            self.press_count += 1
            self.last_press_time = current_time
            self.total_presses += 1

    def _trigger_long_press(self):
        """Trigger long press callback"""
        self.long_press_triggered = True
        self.total_long_presses += 1
        
        if self.on_long_press:
            try:
                self.on_long_press()
            except Exception as e:
                print(f"Error in long press callback: {e}")

    def _process_pending_presses(self):
        """Process accumulated press events"""
        if self.press_count == 1:
            # Single press
            if self.on_press:
                try:
                    self.on_press()
                except Exception as e:
                    print(f"Error in press callback: {e}")
                    
        elif self.press_count >= 2:
            # Double press (or more)
            self.total_double_presses += 1
            if self.on_double_press:
                try:
                    self.on_double_press()
                except Exception as e:
                    print(f"Error in double press callback: {e}")
        
        # Reset press counter
        self.press_count = 0

    def is_pressed(self):
        """Check if button is currently pressed (immediate, no debouncing)"""
        return self.pin_obj.value == self.pressed_state

    def wait_for_press(self, timeout_ms=None):
        """
        Block until button is pressed or timeout occurs.
        
        Args:
            timeout_ms: Timeout in milliseconds (None for no timeout)
            
        Returns:
            True if button was pressed, False if timeout occurred
        """
        start_time = time.monotonic()
        timeout_seconds = timeout_ms / 1000.0 if timeout_ms else None
        
        while True:
            self.update()
            
            # Check for timeout
            if timeout_seconds and (time.monotonic() - start_time) > timeout_seconds:
                return False
            
            # Check if button was pressed (look for press count increase)
            if self.press_count > 0:
                # Process the press immediately
                self._process_pending_presses()
                return True
            
            time.sleep(0.01)  # Small delay to prevent busy waiting

    def set_callbacks(self, on_press=None, on_long_press=None, on_double_press=None):
        """Update callback functions"""
        if on_press is not None:
            self.on_press = on_press
        if on_long_press is not None:
            self.on_long_press = on_long_press
        if on_double_press is not None:
            self.on_double_press = on_double_press

    def get_statistics(self):
        """Get button press statistics"""
        return {
            'total_presses': self.total_presses,
            'total_long_presses': self.total_long_presses,
            'total_double_presses': self.total_double_presses,
            'current_state': self.is_pressed()
        }

    def reset_statistics(self):
        """Reset button press statistics"""
        self.total_presses = 0
        self.total_long_presses = 0
        self.total_double_presses = 0

    def deinit(self):
        """Clean up button resources"""
        self.pin_obj.deinit()


# Helper functions for simple button usage
def create_simple_button(pin, callback, pull=digitalio.Pull.UP):
    """Create a simple button with single press callback"""
    return Button(pin, on_press=callback, pull=pull)


def wait_for_button_press(pin, timeout_ms=None, pull=digitalio.Pull.UP):
    """Simple function to wait for a button press"""
    button = Button(pin, pull=pull)
    try:
        return button.wait_for_press(timeout_ms)
    finally:
        button.deinit()


def test_button(pin, duration_seconds=30):
    """Test button functionality for specified duration"""
    print(f"=== Button Test (Pin {pin}) ===")
    print("Press button to test single press")
    print("Hold button for long press")
    print("Double-click for double press")
    print(f"Test will run for {duration_seconds} seconds...")
    
    def on_press():
        print("📱 Single press detected!")
    
    def on_long_press():
        print("⏳ Long press detected!")
    
    def on_double_press():
        print("⚡ Double press detected!")
    
    button = Button(pin, on_press=on_press, on_long_press=on_long_press, on_double_press=on_double_press)
    
    start_time = time.monotonic()
    try:
        while time.monotonic() - start_time < duration_seconds:
            button.update()
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nTest interrupted")
    finally:
        stats = button.get_statistics()
        print(f"\n=== Test Results ===")
        print(f"Single presses: {stats['total_presses']}")
        print(f"Long presses: {stats['total_long_presses']}")
        print(f"Double presses: {stats['total_double_presses']}")
        button.deinit()


if __name__ == "__main__":
    # Example usage
    import board
    test_button(board.D6, duration_seconds=30)