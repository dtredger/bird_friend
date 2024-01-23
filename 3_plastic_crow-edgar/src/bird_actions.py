# Code for paper-mache crow, adapted to use pico_w
# does not currently have a speaker, so only controls:
# - neck rotation
# - beak opening
# The pico_w seems to retain time, so use clock
import os
from machine import Pin, PWM
import wave
from wavePlayer import wavePlayer
import time
from time import sleep
import json
import math
import random
import _thread
from phew import logging


SPEAKER_PIN = 15
LED_PIN = 16
SERVO_PIN = 28

MAX_EYE_BRIGHTNESS = 0.80
RUN_EVERY_MIN_DEBUG = False # set True to run actions every min

# Audio file length of frames/framerate should give number of seconds
def select_audio():
    path = f"audio_files/{random.choice(os.listdir('audio_files'))}"
    audio_file = wave.open(path)
    length_s = audio_file.getnframes() / audio_file.getframerate()
    return [path, length_s]

def fade_in(eye_pin=LED_PIN, sleep_time=0.005, max_brightness=MAX_EYE_BRIGHTNESS):
    eyes_pwm = PWM(Pin(eye_pin))
    eyes_pwm.freq(1000)  # Set the PWM frequency.
    duty = 0
    direction = 1
    for _ in range(256 * max_brightness):
        duty += direction
        eyes_pwm.duty_u16(duty * duty)
        sleep(sleep_time)

def fade_out(eye_pin=LED_PIN, sleep_time=0.005):
    eyes_pwm = PWM(Pin(eye_pin))
    eyes_pwm.freq(1000)  # Set the PWM frequency.
    duty = math.floor(math.sqrt(eyes_pwm.duty_u16()))
    direction = -1
    for _ in range(256):
        if duty <= 0:
            break
        duty += direction
        eyes_pwm.duty_u16(duty * duty)
        sleep(sleep_time)
    eyes_pwm.deinit()

# On Restart, the pin's current location will always return 0
# even though the actual position will be wherever it was when
# powered off. This causes unexpected rotation if you try to slowly
# rotate to a point; so set the end-point on
# Takes 5 seconds with:
# - sleep_interval=0.01
# - bottom = 3300
# - top = 7400
# takes 4 seconds with:
# - sleep_interval=0.01
# - bottom = 3500
# - top = 7200
def look_left_right(pin_number=SERVO_PIN, sleep_interval=0.01, rotation_pause=1.3):
    oscillate_pin = PWM(Pin(pin_number))
    oscillate_pin.freq(50)
    # For some reason, the bottom seems to be further from center than the top,
    # so bottom is higher than expected
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

def chirp(times=2, target_time=0):
    audio_file, length_s = select_audio()
    # Set times to be slightly less than target_time
    if target_time:
        times = int(target_time / length_s)
    for _ in range(times):
        player = wavePlayer(leftPin=Pin(SPEAKER_PIN), rightPin=Pin(SPEAKER_PIN))
        player.play(audio_file)

def flash_eyes(times=3):
    for _ in range(times):
        fade_in()
        fade_out()

def rotate_and_chirp(times=1):
    # TODO - chirp X number of times
    fade_in()
    _thread.start_new_thread(chirp, ([None, 4]))
    look_left_right()
    fade_out()

# ---- Data Loading ----

def load_data(data_file='data.json'):
    try:
        data = open(data_file)
        json_data = json.loads(data.read())
        earliest = json_data["earliest"]
        latest = json_data["latest"]
        interval = json_data["interval"]
        return {"earliest": earliest, "latest": latest, "interval": interval}
    except Exception as e:
        logging.info(f"load_data error {e}")
        return {}

def get_latest_time():
    try:
        time_arr = load_data()['latest'].split(":")
        return {"hour": int(time_arr[0]), "min": int(time_arr[1])}
    except Exception:
        return {"hour": 24, "min": 0}

def get_interval():
    # match every minute for debugging
    if RUN_EVERY_MIN_DEBUG:
        return {"hour": 0, "min": 1}
    try:
        time_arr = load_data()['interval'].split(":")
        return {"hour": int(time_arr[0]), "min": int(time_arr[1])}
    except Exception:
        return {"hour": 1, "min": 0}

def get_set_hour_min(key):
    time_arr = load_data()[key].split(":")
    hour = int(time_arr[0])
    min = int(time_arr[1])
    return [hour, min]

def get_current_hour_min():
    hour_now = time.localtime()[3]
    min_now = time.localtime()[4]
    return [hour_now, min_now]

def time_after_earliest():
    hour_set, min_set = get_set_hour_min('earliest')
    hour_now, min_now = get_current_hour_min()
    if hour_now > hour_set:
        return True
    elif hour_now == hour_set and min_now >= min_set:
        return True
    else:
        return False

def time_before_latest():
    hour_set, min_set = get_set_hour_min('latest')
    hour_now, min_now = get_current_hour_min()
    if hour_now < hour_set:
        return True
    elif hour_now == hour_set and min_now < min_set:
        return True
    else:
        return False


def run_actions(force=False):
    if force:
        rotate_and_chirp()
    hour, minute = get_current_hour_min()
    interval_min = get_interval()["min"]
    logging.info(f"hour: {hour}; minute: {minute}")
    if minute % interval_min == 0:
        logging.info("minute interval match")
        rotate_and_chirp(times=interval_min)
    elif get_interval()["hour"] == 1:
        logging.info("hour interval match")
        if minute == 0:
            rotate_and_chirp(times=hour)
    else:
        logging.info(f"minute {minute} does not match interval {interval_min}")

# **** SCHEDULER ****

def run_bird_schedule():
    if (time_after_earliest() and time_before_latest()):
        logging.info('within time window')
        run_actions()
    elif time_after_earliest() == False:
        logging.info('time_after_earliest FALSE')
    elif time_before_latest() == False:
        logging.info('time_before_latest FALSE')
    else:
        logging.info('some other error')
