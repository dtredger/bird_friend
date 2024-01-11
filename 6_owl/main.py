"""
Owl Bird, Jan 2024

Modules used by owl:
- Servo (neck)
- LEDs (eyes)
- Light Sensor
- Time Randomizer

Sound is disabled since there is no included speaker
"""

from machine import Timer
import _thread

# Modules from lib
from servos import *
from leds import *
from read_sensors import *

servo = Servo(16)
leds = Leds(18)

INTERVAL_MINUTES = 60

def rotate_light_eyes():
    leds.fade_in()
    servo.sweep()
    leds.fade_out()


# === Hour Timer === #
main_timer = Timer(-1)
interval = 60000 * INTERVAL_MINUTES # 60000ms = 1 min
main_timer.init(period=interval,
                mode=Timer.PERIODIC,
                callback=lambda t:rotate_light_eyes())

# On initialization, flash eyes, rotate, and chirp
leds.flash_eyes(times=6)
rotate_light_eyes()
