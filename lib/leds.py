from time import sleep
from machine import Pin, PWM

class Leds:
    """
    Create an Led object that can be faded in,
    faded out, and set to flash X times.
    Wiring requires 200 ohm resistor in circuit between GPIO pin `pin_number`
    and ground.
    """
    def __init__(self, pin_number):
        self.eyes_pwm = PWM(Pin(pin_number))
        self.eyes_pwm.freq(1000)
        self.sleep_time = 0.005
        self.max_brightness = 1.0

    def fade_in(self):
        duty = 0
        direction = 2
        max_duty = (256 * self.max_brightness)
        for _ in range(256):
            if duty > max_duty:
                break
            duty += direction
            self.eyes_pwm.duty_u16(duty * duty)
            sleep(self.sleep_time)

    def fade_out(self):
        """
        The pin does not appear to return duty_u16 value after it is set,
        so assume fade_out starts from max brightness
        """
        duty = int(256 * self.max_brightness)
        direction = -2
        for _ in range(256):
            if duty <= 0:
                break
            duty += direction
            self.eyes_pwm.duty_u16(duty * duty)
            sleep(self.sleep_time)

    def flash_eyes(self, times=2):
        for _ in range(times):
            self.fade_in()
            self.fade_out()


# === CircuitPython ===
# Set EYE_PIN to the pin integer number (not object)
#
#     def fade_in(pin, sleep_interval=0.02, max_brightness=1.0):
#         max_duty = int(max_brightness * 65535)
#         pwm_pin = pwmio.PWMOut(pin)
#         for cycle in range(0, max_duty, 1000):
#             pwm_pin.duty_cycle = cycle
#             time.sleep(sleep_interval)
#         pwm_pin.deinit()
#
#     def fade_out(pin, sleep_interval=0.02):
#         pwm_pin = pwmio.PWMOut(pin)
#         for cycle in range(pwm_pin.duty_cycle, 0, -1000):
#             pwm_pin.duty_cycle = cycle
#             time.sleep(sleep_interval)
#         pwm_pin.deinit()
#
#     def flash_eyes(pin=EYE_PIN, times=2):
#         for _ in range(times):
#             fade_in(pin)
#             fade_out(pin)
