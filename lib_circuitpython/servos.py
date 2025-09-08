import time
import pwmio
from adafruit_motor import servo

class Servo:
    """
    MicroServo for neck of animatronic bird.
    Beginning from 90 degree position will allow rotation left and right.
    Wiring requires GPIO pin `pin`, 5v, and ground.
    Increasing `sleep_interval` will cause slower rotation.
    """
    def __init__(self, pin):
        self.servo_pwm = pwmio.PWMOut(pin, duty_cycle=2 ** 15, frequency=50)
        self.servo_obj = servo.Servo(self.servo_pwm)
        self.sleep_interval = 0.02
        self.rotation_pause = 1.3
        
        # Servo angle positions
        self.bottom_angle = 0    # min angle
        self.top_angle = 180     # max angle
        self.mid_angle = 90      # center position
        
        # Set initial position
        self.servo_obj.angle = self.mid_angle

    def to_top(self):
        current_angle = int(self.servo_obj.angle) if self.servo_obj.angle is not None else self.mid_angle
        step = 1 if current_angle < self.top_angle else -1
        for position in range(current_angle, self.top_angle, step):
            self.servo_obj.angle = position
            time.sleep(self.sleep_interval)
        time.sleep(self.rotation_pause)

    def to_bottom(self):
        current_angle = int(self.servo_obj.angle) if self.servo_obj.angle is not None else self.mid_angle
        step = 1 if current_angle < self.bottom_angle else -1
        for position in range(current_angle, self.bottom_angle, step):
            self.servo_obj.angle = position
            time.sleep(self.sleep_interval)
        time.sleep(self.rotation_pause)

    def to_midpoint(self):
        current_angle = int(self.servo_obj.angle) if self.servo_obj.angle is not None else self.mid_angle
        step = 1 if current_angle < self.mid_angle else -1
        for position in range(current_angle, self.mid_angle, step):
            self.servo_obj.angle = position
            time.sleep(self.sleep_interval)

    def sweep(self):
        """
        On Restart, the servo position will be unknown.
        This method performs a sweep to ensure known positioning.
        """
        # rotate one way, back past mid, then end in mid
        self.to_top()
        self.to_bottom()
        self.to_midpoint()

    def deinit(self):
        """Clean up PWM resources"""
        self.servo_pwm.deinit()


def rotate_servo_to(pin, end_pos, sleep_interval=0.01):
    """
    Standalone function to rotate servo to specific position
    """
    servo_pwm = pwmio.PWMOut(pin, duty_cycle=2 ** 15, frequency=50)
    servo_obj = servo.Servo(servo_pwm)
    current_angle = int(servo_obj.angle) if servo_obj.angle is not None else 90
    step = 1 if (current_angle < end_pos) else -1
    for position in range(current_angle, end_pos, step):
        servo_obj.angle = position
        time.sleep(sleep_interval)
    servo_pwm.deinit()

def servo_left_right_center(pin, rotation_pause=1.3):
    """
    Standalone function for left-right-center sweep
    """
    # rotate one way, back past mid, then end in mid
    rotate_servo_to(pin, 180)
    time.sleep(rotation_pause)
    rotate_servo_to(pin, 0)
    time.sleep(rotation_pause)
    rotate_servo_to(pin, 90)
