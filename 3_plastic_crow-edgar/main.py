"""
Plastic Crow ("Edgar"), updated Mar 2024

Every `INTERVAL_MINUTES` this bird will check the schedule, and if it is
within the time window (between earliest and latest), run the timed_actions
below.

Modules used by owl:
- Access Point (to set time)
    - phew library (server)
- Schedule (checking time)
- LEDs (eyes)
- Servo (neck)
- Amplifier (audio)
"""

from machine import Timer
from time import sleep
import _thread

# Modules from lib
from schedule import Schedule
from leds import Leds
from servos import Servo
from amplifier import Amplifier
from access_point.methods import *

schedule = Schedule()
leds = Leds(7)
servo = Servo(0)
amplifier = Amplifier(21, 20, 19, audio_dir="audio", volume_change=-2)

INTERVAL_MINUTES = 60
DEBUG = False

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

def check_schedule():
    schedule.run(light_rotate_hoot)


# === Timer === #
def start_timer(main_timer, interval_min):
    interval = 60_000 * interval_min # 60_000ms = 1 min
    main_timer.init(period=interval,
                    mode=Timer.PERIODIC,
                    callback=lambda t:check_schedule())

# === Initialization Actions ===
start_timer(Timer(-1), INTERVAL_MINUTES)
light_rotate_hoot()



# === Access Point === #
# AP times out after 15 minutes, or can be deactivated by user in UI
global ap_timer
ap_timer = Timer(-1)
ap_timeout = 60000 * 15 # 15 minutes
ap_timer.init(period=ap_timeout, mode=Timer.ONE_SHOT, callback=lambda t:stop_access_point())

# Start Wireless Access Point
start_access_point()
