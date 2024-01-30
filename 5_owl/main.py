"""
Owl Bird, Jan 2024

Every `INTERVAL_MINUTES` this bird will check the light level, and if it is
bright enough, run the timed_actions below.

Modules used by owl:
- LEDs (eyes)
- Sensors (Light Sensor)
- Servo (neck)
- Speaker
"""

from machine import Timer
import _thread

# Modules from lib
from leds import Leds
from sensors import LightSensor
from servos import Servo
from speaker import Speaker


leds = Leds(19)
light_sensor = LightSensor(26)
servo = Servo(16)
speaker = Speaker(2, 1, 0, "audio/sf-owl.wav")

INTERVAL_MINUTES = 60


def light_rotate_hoot():
    leds.fade_in()
    servo.to_top()
    speaker.play_wav()
    servo.to_bottom()
    servo.to_midpoint()
    leds.fade_out()

def timed_actions():
    if light_sensor.over_minimum():
        light_rotate_hoot()
    else:
        leds.flash_eyes()


# === Timer === #
main_timer = Timer(-1)
interval = 60_000 * INTERVAL_MINUTES # 60_000ms = 1 min
main_timer.init(period=interval,
                mode=Timer.PERIODIC,
                callback=lambda t:timed_actions())


# === Initialization Actions ===
light_rotate_hoot()
