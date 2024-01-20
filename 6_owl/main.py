"""
Owl Bird, Jan 2024

Modules used by owl:
- Servo (neck)
- LEDs (eyes)
- Audio
- Light Sensor
- Time Randomizer

"""

from machine import Timer
import _thread

# Modules from lib
from audio import *
from leds import *
from sensors import *
from servos import *

servo = Servo(16)
leds = Leds(18)
speaker = Speaker(2, 1, 0, "audio/great-horned-owl-44100k.wav")
l = LightSensor(26)

INTERVAL_MINUTES = 1 #60

def rotate_light_eyes():
    leds.fade_in()
    servo.sweep()
    leds.fade_out()

def hourly_actions():
    rotate_light_eyes()
    speaker.play_wav()
    f = open('data.txt', 'a')
    light_sensor = str(l.read())
    f.write(light_sensor)
    f.close()

# === Hour Timer === #
main_timer = Timer(-1)
interval = 60000 * INTERVAL_MINUTES # 60000ms = 1 min
main_timer.init(period=interval,
                mode=Timer.PERIODIC,
                callback=lambda t:hourly_actions())

# On initialization, flash eyes, rotate, and chirp
leds.flash_eyes(times=6)
rotate_light_eyes()
speaker.play_wav()
