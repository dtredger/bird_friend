# Code for an animatronic crow with two servo motors and a speaker connected to a Raspberry Pi headphone jack.
#
# When choosing a power cord for raspberry pi, check voltage (5v) but also amps: it appears 0.7 is too low
# when servos are involved (board will shut down on AngularServo calls below)
#
#
# 'To reduce servo jitter, use the pigpio pin factory.'
# See https://gpiozero.readthedocs.io/en/stable/api_output.html#servo
# RUN DAEMON -> $> sudo pigpiod
#
# also has a service that can be started: systemtl enable pigpiod
#

import datetime


from src.crow import *

DEBUG_MODE = True

# Start blocking loop that runs hour_callback at the top of the hour
#
# @param crow [Crow] crow object
# @return [Nil]
def run_schedule(crow, earliest_hour=7):
    while True:
        hour = datetime.datetime.now().hour
        minute = datetime.datetime.now().minute
        # do not caw before 7am
        if DEBUG_MODE == True:
            print("debug mode on. Running `crow.vocalize_multicaw('left')`")
            crow.vocalize_multicaw('left')
        if hour >= earliest_hour:
            # convert 24-hr time to 12-hr
            if hour > 12:
                hour = hour - 12
            # Actions at 8am, 4pm, on the hour, and half-hour
            if hour == 8 and minute == 0:
                crow.vocalize_multicaw('left')
            elif hour == 4 and minute == 0:
                crow.vocalize_multicaw('left')
            elif minute == 0:
                crow.rotate_caw_times('left', hour)
            elif minute % 30 == 0:
                crow.vocalize_random_rattle('left')
            time.sleep(60)


if __name__ == '__main__':
    print(f'Starting Crow Friend. Cawing on the Hour :)')
    crow_friend = Crow()
    crow_friend.surprise()
    # begin waiting for hour
    run_schedule(crow_friend)
