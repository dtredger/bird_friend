"""
Baby Crow, Mar 2024

Every `INTERVAL_MINUTES` this bird will check the light level, and if it is
bright enough, run the timed_actions below.

Modules used by owl:
- LEDs (eyes)
- Sensors (Light Sensor)
- Servo (neck)
- Amplifier
"""

from machine import Timer
from time import sleep
import _thread

# Modules from lib
from leds import Leds
from sensors import LightSensor
from servos import Servo
from amplifier import Amplifier


leds = Leds(18)
light_sensor = LightSensor(26)
servo = Servo(22)
amplifier = Amplifier(9,8,7, audio_dir="audio")

DEBUG = True
INTERVAL_MINUTES = 60

def light_rotate_hoot():
    leds.fade_in()
    servo.to_top()
    amplifier.play_wav()
    sleep(0.5)
    servo.to_bottom()
    amplifier.play_wav()
    sleep(0.5)
    servo.to_midpoint()
    leds.fade_out()

def timed_actions():
    if DEBUG == True:
        light_sensor.log_reading()
    if light_sensor.over_minimum():
        light_rotate_hoot()
    else:
        leds.flash_eyes()

# === Timer === #
def start_timer(main_timer, interval_min):
    interval = 60_000 * interval_min # 60_000ms = 1 min
    main_timer.init(period=interval,
                    mode=Timer.PERIODIC,
                    callback=lambda t:timed_actions())

# === Initialization Actions ===
start_timer(Timer(-1), INTERVAL_MINUTES)
light_rotate_hoot()

