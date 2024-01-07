"""
Blue Parrot, Aug 03 2023

Sound disabled for blue parrot since it does not have 
a speaker.
"""

from machine import Timer, Pin, PWM
from wavePlayer import wavePlayer
from time import sleep
import math
import _thread

# GPIO, brightness, and timer interval
MAX_EYE_BRIGHTNESS = 0.8
EYE_PIN = 15
NECK_PIN = 22
# SPEAKER_PIN = 15
INTERVAL_MINUTES = 60

def fade_in(eye_pin=EYE_PIN, sleep_time=0.005, max_brightness=MAX_EYE_BRIGHTNESS):
    eyes_pwm = PWM(Pin(eye_pin))
    eyes_pwm.freq(1000)  # Set the PWM frequency.
    duty = 0
    direction = 2
    max_duty = (256 * max_brightness)
    for _ in range(256):
        if duty > max_duty:
            break
        duty += direction
        eyes_pwm.duty_u16(duty * duty)
        sleep(sleep_time)
    
def fade_out(eye_pin=EYE_PIN, sleep_time=0.005):
    eyes_pwm = PWM(Pin(eye_pin))
    eyes_pwm.freq(1000)  # Set the PWM frequency.
    duty = math.floor(math.sqrt(eyes_pwm.duty_u16()))
    direction = -2
    for _ in range(256):
        if duty <= 0:
            break
        duty += direction
        eyes_pwm.duty_u16(duty * duty)
        sleep(sleep_time)
    eyes_pwm.deinit()
    
def look_left_right(pin_number=NECK_PIN, sleep_interval=0.016, rotation_pause=1.3):
    """
    On Restart, the pin's current location will always return 0
    even though the actual position will be wherever it was when
    powered off. This causes unexpected rotation if you try to slowly
    rotate to a point; so set the end-point on
    """
    oscillate_pin = PWM(Pin(pin_number))
    oscillate_pin.freq(50)
    # For some reason, the bottom seems to be further from center than the top,
    # so bottom is set higher than expected
    bottom = 3500 # min 1900
    top = 7200 # max 8300
    mid_point = 5100
    # rotate one way, back past mid, then end in mid
    for position in range(mid_point, top, 50):
        oscillate_pin.duty_u16(position)
        sleep(sleep_interval)
    sleep(rotation_pause)    
    for position in range(oscillate_pin.duty_u16(), bottom, -50):
        oscillate_pin.duty_u16(position)
        sleep(sleep_interval)
    sleep(rotation_pause)
    for position in range(oscillate_pin.duty_u16(), mid_point, 50):     
        oscillate_pin.duty_u16(position)
        sleep(sleep_interval)
    oscillate_pin.deinit()    

# def chirping(times=2):
#     # TODO - waveplayer (specifically myPWM) is hardcoded to pin 15
#     player = wavePlayer(leftPin=Pin(SPEAKER_PIN), rightPin=Pin(SPEAKER_PIN))
#     for _ in range(times):
#         player.play('bird-chirping-400.wav')

def eye_flash(times=2):
    for _ in range(times):
        fade_in()
        fade_out()

def rotate_light_eyes():
    fade_in()
    # _thread.start_new_thread(chirping, ())
    look_left_right()
    fade_out()


# === Hour Timer === #
main_timer = Timer(-1)
interval = 60000 * INTERVAL_MINUTES # 60000ms = 1 min
main_timer.init(period=interval, mode=Timer.PERIODIC, callback=lambda t:rotate_light_eyes())

# On initialization, flash eyes, rotate, and chirp
eye_flash(times=6)
rotate_light_eyes()
