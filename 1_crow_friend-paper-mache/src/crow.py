import time
# from logger import logger
from threading import Thread
import gpiozero

# GPIOZERO_PIN_FACTORY=PiGPIOFactory python3
from gpiozero.pins.pigpio import PiGPIOFactory
gpiozero.Device.pin_factory = PiGPIOFactory()

# gpiozero.Device._default_pin_factory()

from . import audio

# Pi pins 24 & 25
BEAK_SERVO_PIN = 25
HEAD_SERVO_PIN = 24


class Crow(object):
    """
        Code for an animatronic crow with two servo motors and a speaker connected to a Raspberry Pi headphone jack.

        When choosing a power cord for raspberry pi, check voltage (5v) but also amps: it appears 0.7 is too low
        when servos are involved (board will shut down on AngularServo calls below)

        'To reduce servo jitter, use the pigpio pin factory.' See https://gpiozero.readthedocs.io/en/stable/api_output.html#servo
        RUN DAEMON -> $> sudo pigpiod (it is also a service that can be enabled)
    """

    def __init__(self, beak_pin=BEAK_SERVO_PIN, head_pin=HEAD_SERVO_PIN, sound_module=audio):
        # place Head in default position (-90 is max Right on servo)
        self.HEAD_SERVO = gpiozero.AngularServo(head_pin)
        self.head_at_rest = -90
        self.HEAD_SERVO.angle = self.head_at_rest
        # 90 = max open (but ~30 is a good open-mouth maximum)
        self.BEAK_SERVO = gpiozero.AngularServo(beak_pin, initial_angle=-90)
        self.beak_shut = -90
        self.BEAK_SERVO.angle = self.beak_shut
        self.audio = sound_module
        print("crow created")

    # rotate_direction either `right` or not (left)
    # The servo (appears to) struggle to reach 90 (and is noisy in
    # the attempt, so cap at 80 rotation)
    def rotate_caw_times(self, rotate_direction, times):
        print(f"rotate_direction: {rotate_direction}, times: {times}")
        angle = self.get_angle(rotate_direction)
        self.rotate_servo(self.HEAD_SERVO, angle)
        self.caw_x_times(times)
        self.rotate_servo(self.HEAD_SERVO, self.head_at_rest)

    # say 'surprise!' one time
    def surprise(self, rotate_direction='left'):
        surprise = self.audio.SOUNDS['surprise']
        self.rotate_and_vocalize(surprise, rotate_direction)

    # Open beak and rotate one direction (L or R), then crow
    # rotation a little slow
    def vocalize_random_rattle(self, rotate_direction='left'):
        rattle = self.audio.rand_rattle()
        self.rotate_and_vocalize(rattle, rotate_direction)

    # make random Multicaw sound (3, 9, or 10 caws)
    def vocalize_multicaw(self, rotate_direction='left'):
        sound = self.audio.rand_multicaw()
        self.rotate_and_vocalize(sound, rotate_direction)

    # Generic method for Rotate head in rotate_direction,
    # emitting sound, then rotating back to original position
    def rotate_and_vocalize(self, sound_dict, rotate_direction):
        angle = self.get_angle(rotate_direction)
        self.rotate_servo(self.HEAD_SERVO, angle)
        self.open_mouth_for_sound(self.BEAK_SERVO, sound_dict)
        self.rotate_servo(self.HEAD_SERVO, self.head_at_rest)

    def threaded_rotate_vocalize(self, sound_dict, rotate_dir):
        sleep_time = sound_dict['duration']
        rotations = Thread(target=self.rotate_and_back, args=(sleep_time, rotate_dir))
        vocalization = Thread(target=self.open_mouth_for_sound, args=(self.BEAK_SERVO, sound_dict,))
        rotations.start()
        vocalization.start()

    # Open mouth a bit, oscillate head back-and-forth, then close mouth,
    # all without sound. Crows seem to do this sometimes.
    def open_beak_rotate(self):
        self.move_beak(self.BEAK_SERVO, max_open=30)
        self.oscillate_back_and_forth(self.HEAD_SERVO)
        self.move_beak(self.BEAK_SERVO, max_open=-80)

    # THREADING TEST
    def rotate_and_back(self, sleep_time, rotate_dir):
        angle = self.get_angle(rotate_dir)
        self.rotate_servo(self.HEAD_SERVO, angle)
        time.sleep(sleep_time)
        self.rotate_servo(self.HEAD_SERVO, self.head_at_rest)

    def threaded_rotate_caw(self):
        sleep_time = 2
        rotations = Thread(target=self.rotate_and_back, args=(sleep_time,))
        caws = Thread(target=self.caw_x_times, args=(2,))
        rotations.start()
        caws.start()

    # Private Methods

    # Given a sound x seconds long, have the servo fully rotated (to its
    # open_position) at time = x/2, and back at shut_position at time = x
    def open_mouth_for_sound(self, servo, sound_dict, shut_position=-90, open_position=30):
        time_s = sound_dict['duration']
        audio_file = sound_dict['filename']
        start_time = time.time()
        self.rotate_servo(servo, open_position, interval=0.0001, speed_multiplier=5)
        self.audio.play(audio_file)
        elapsed_time = time.time() - start_time
        # count two rotation times, and only sleep for the remaining time in time_s
        # if it's greater than specified time_s
        if (time_s - (elapsed_time * 2)) > 0:
            time.sleep(time_s - (elapsed_time * 2))
        self.rotate_servo(servo, shut_position, interval=0.0001, speed_multiplier=5)

    # for example, with sleep time of 0.1 between each angle-set, the total
    # time comes to 9.66 (so almost all the time is sleep: 90*0.1)
    # a 0.01s sleep time gives a 90-degree rotation in 1.6 seconds
    def oscillate_back_and_forth(self, servo, interval=0.01):
        self.rotate_servo(servo, 0)
        for angle in range(0, 90):
            servo.angle = angle
            time.sleep(interval)
        for angle in range(90, -90, -1):
            servo.angle = angle
            time.sleep(interval)
        for angle in range(-90, 0):
            servo.angle = angle
            time.sleep(interval)

    # In cases where the current servo position is not what is desired,
    # slowly rotate to that position (to prevent violent jerk to the
    # starting position in some other method)
    def rotate_servo(self, servo, target_angle, interval=0.005, speed_multiplier=1):
        initial_angle = int(servo.angle)
        if target_angle > initial_angle:
            step = 1 * speed_multiplier
        else:
            step = -1 * speed_multiplier
        for angle in range(initial_angle, target_angle, step):
            servo.angle = angle

    # max_open takes a value from -90 (beak shut) => +90)
    # The beak appears fully open at +30
    def move_beak(self, servo, max_open, interval=0.03):
        initial_angle = self.beak_shut
        for ang in range(initial_angle, max_open):
            servo.angle = ang
            time.sleep(interval)

    # Caw the given integer times
    def caw_x_times(self, times):
        random_caw = self.audio.rand_caw1()
        # iterate through once fewer than `times`
        for x in range(1, times):
            shut_position = 20
            self.open_mouth_for_sound(
                self.BEAK_SERVO, random_caw, shut_position, open_position=30)
        # last iteration shut all the way
        self.open_mouth_for_sound(
            self.BEAK_SERVO, random_caw, shut_position=-90, open_position=30)

    # Determine the angle to rotate to, given the default start position.
    # Servo should not go outside (-80 <> 80)
    def get_angle(self, rotate_dir):
        start = self.head_at_rest
        if rotate_dir == 'right':
            return max(start - 80, -80)
        else:
            return min(start + 80, 80)
