import time
import pwmio

class Leds:
    """
    Create an Led object that can be faded in,
    faded out, and set to flash X times.
    Wiring requires 200 ohm resistor in circuit between GPIO pin `pin`
    and ground.
    """
    def __init__(self, pin):
        self.led_pwm = pwmio.PWMOut(pin)
        self.sleep_time = 0.005
        self.max_brightness = 1.0

    def fade_in(self, sleep_interval=None, max_brightness=None):
        """Fade LEDs in to max brightness"""
        if sleep_interval is None:
            sleep_interval = self.sleep_time
        if max_brightness is None:
            max_brightness = self.max_brightness
            
        max_duty = int(max_brightness * 65535)
        for cycle in range(0, max_duty, 1000):
            self.led_pwm.duty_cycle = cycle
            time.sleep(sleep_interval)

    def fade_out(self, sleep_interval=None):
        """Fade LEDs out from current brightness"""
        if sleep_interval is None:
            sleep_interval = self.sleep_time
            
        for cycle in range(self.led_pwm.duty_cycle, 0, -1000):
            if cycle < 0:
                cycle = 0
            self.led_pwm.duty_cycle = cycle
            time.sleep(sleep_interval)
        
        # Ensure fully off
        self.led_pwm.duty_cycle = 0

    def flash_eyes(self, times=2, fade_speed=None):
        """Flash the LEDs a specified number of times"""
        for _ in range(times):
            self.fade_in(fade_speed)
            self.fade_out(fade_speed)

    def set_brightness(self, brightness):
        """Set LED brightness (0.0 to 1.0)"""
        duty = int(brightness * 65535)
        self.led_pwm.duty_cycle = min(65535, max(0, duty))

    def turn_on(self):
        """Turn LEDs on to max brightness"""
        self.set_brightness(self.max_brightness)

    def turn_off(self):
        """Turn LEDs off"""
        self.set_brightness(0)

    def pulse_eyes(self, pulse_times=2, speed=0.01):
        """Pulse the LEDs in and out"""
        for _ in range(pulse_times):
            # Fade in
            for cycle in range(0, 65535, 2000):
                self.led_pwm.duty_cycle = cycle
                time.sleep(speed)
            # Fade out
            for cycle in range(65535, 0, -2000):
                self.led_pwm.duty_cycle = cycle
                time.sleep(speed)
        self.led_pwm.duty_cycle = 0

    def deinit(self):
        """Clean up PWM resources"""
        self.led_pwm.deinit()


# Standalone helper functions
def fade_in(pin, sleep_interval=0.02, max_brightness=1.0):
    """Standalone function to fade in LEDs"""
    max_duty = int(max_brightness * 65535)
    led_pwm = pwmio.PWMOut(pin)
    for cycle in range(0, max_duty, 1000):
        led_pwm.duty_cycle = cycle
        time.sleep(sleep_interval)
    led_pwm.deinit()

def fade_out(pin, sleep_interval=0.02):
    """Standalone function to fade out LEDs"""
    led_pwm = pwmio.PWMOut(pin)
    for cycle in range(led_pwm.duty_cycle, 0, -1000):
        led_pwm.duty_cycle = cycle
        time.sleep(sleep_interval)
    led_pwm.deinit()

def flash_eyes(pin, times=2):
    """Standalone function to flash LEDs"""
    for _ in range(times):
        fade_in(pin)
        fade_out(pin)
