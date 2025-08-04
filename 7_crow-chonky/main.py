"""
Crow, Aug 2025

Every `INTERVAL_MINUTES` this bird will check the light level, and if it is
bright enough, run the timed_actions below.

Modules used:
- LEDs (eyes)
- Sensors (Light Sensor)
- Servo (neck)
- Amplifier
"""

""" CONFIGURATION """
DEBUG = True
INTERVAL_MINUTES = 60
LED_PIN = 18
LIGHT_SENSOR_PIN = 26
SERVO_PIN = 25
AMPLIFIER_PINS = [17, 16, 15]


from machine import Timer
from time import sleep
import _thread

# Modules from lib
from leds import Leds
from sensors import LightSensor
from servos import Servo
from amplifier import Amplifier

leds = Leds(LED_PIN)
light_sensor = LightSensor(LIGHT_SENSOR_PIN)
servo = Servo(SERVO_PIN)
amplifier = Amplifier(*AMPLIFIER_PINS, audio_dir="audio")

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

