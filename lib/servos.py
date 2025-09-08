from time import sleep
from machine import Pin, PWM

class Servo:
    """
    MicroServo for neck of animatronic bird.
    Beginning from 90 degree position will allow rotation left and right.
    Wiring requires GPIO pin `pin_number`, 5v, and ground.
    Increasing `sleep_interval` will cause slower rotation.
    """
    def __init__(self, pin_number):
        self.oscillate_pin = PWM(Pin(pin_number))
        self.oscillate_pin.freq(50)
        self.sleep_interval = 0.02
        self.rotation_pause = 1.3
        # For some reason, the bottom seems to be further from center than
        # top, so bottom is set higher than expected
        self.bottom = 3500 # min 1900
        self.top = 7200 # max 8300
        self.mid_point = 5100

    def to_top(self):
        for position in range(self.mid_point, self.top, 50):
            self.oscillate_pin.duty_u16(position)
            sleep(self.sleep_interval)
        sleep(self.rotation_pause)

    def to_bottom(self):
        for position in range(self.oscillate_pin.duty_u16(), self.bottom, -50):
            self.oscillate_pin.duty_u16(position)
            sleep(self.sleep_interval)
        sleep(self.rotation_pause)

    def to_midpoint(self):
        for position in range(self.oscillate_pin.duty_u16(), self.mid_point, 50):
            self.oscillate_pin.duty_u16(position)
            sleep(self.sleep_interval)


    def sweep(self):
        """
        On Restart, the pin's current location will always return 0
        even though the actual position will be wherever it was when
        powered off. This causes unexpected rotation if you try to slowly
        rotate to a point; so set the end-point on
        """
        # rotate one way, back past mid, then end in mid
        self.to_top()
        self.to_bottom()
        self.to_midpoint()
