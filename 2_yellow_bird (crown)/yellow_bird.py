# micropython for yellow bird with neck servo
# connect to raspberry pi pico_w using minicom:
#    minicom -o -D /dev/tty.usbmodem14101
# to exit: ctrl-a, then esc-x
#
# https://docs.micropython.org/en/latest/rp2/quickref.html



from time import sleep
from machine import Timer, Pin, PWM

# == blink onboard LED ==

# pico_w has pin 'LED' while normal pico uses 25
led = Pin(25, Pin.OUT) # led = Pin("LED", Pin.OUT)

# RP2040’s system timer peripheral provides a global microsecond timebase and generates interrupts for it.
# The software timer is available currently, and there are unlimited number of them (memory permitting).
# There is no need to specify the timer id (id=-1 is supported at the moment) as it will default to this.

# led_blink_timer = Timer(-1)
# led_blink_timer.init(period=1000, mode=Timer.PERIODIC, callback=lambda t:led.toggle())


# == oscillate servo ==

# https://microcontrollerslab.com/servo-motor-raspberry-pi-pico-micropython/
# unsigned 16-bit value in the range 0 to 65535 inclusive.
# sleep_interval determines how quickly the servo rotates back and forth.
# Generally:
# * 0.01 (3 seconds)
# * 0.03 (8 seconds)
# * 0.06 (15 seconds)
def oscillate(pin_number=10, sleep_interval=0.03):
    pwm = PWM(Pin(pin_number))
    pwm.freq(50)
    for position in range(1900, 8300, 50):
        pwm.duty_u16(position)
        sleep(sleep_interval)
    for position in range(8300, 1900, -50):
        pwm.duty_u16(position)
        sleep(sleep_interval)
    pwm.deinit()    
    return True    



servo_timer = Timer(-1)
interval = 60000 # 1 minute
servo_timer.init(period=interval, mode=Timer.PERIODIC, callback=lambda t:oscillate())

# servo_timer.deinit()


# == Pulse Eyes ==

eyes_pwm = PWM(Pin(7))
eyes_pwm.freq(1000)  # Set the PWM frequency.

# Fade the LED in and out `pulse_times` times.
def pulse_eyes(pulse_times=2):
    duty = 0
    direction = 1
    for _ in range(pulse_times * 2 * 256):
        duty += direction
        if duty > 255:
            duty = 255
            direction = -1
        elif duty < 0:
            duty = 0
            direction = 1
        eyes_pwm.duty_u16(duty * duty)
        time.sleep(0.001)

def fade_in(sleep_time=0.01):
    duty = 0
    direction = 1
    for _ in range(256):
        duty += direction
        eyes_pwm.duty_u16(duty * duty)
        time.sleep(sleep_time)
    
def fade_out(sleep_time=0.01):
    duty = 255
    direction = -1
    for _ in range(256):
        duty += direction
        eyes_pwm.duty_u16(duty * duty)
        time.sleep(sleep_time)
    

# == Play Sound ==

def play_tone(frequency):
    # Set maximum volume
    buzzer.duty_u16(1000)
    # Play tone
    buzzer.freq(frequency)

def be_quiet():
    # Set minimum volume
    buzzer.duty_u16(0)

# while True:
#     play_tone(650)
#     sleep(0.75)
#     be_quiet()
#     sleep(0.75)


# == Play WAV file ==
# uses wavePlayer, which relies on:
#   * wave.py, which requires chunk.py
#   * myDMA, myPWM
# https://www.coderdojotc.org/micropython/sound/07-play-audio-file/
from machine import Pin
from wavePlayer import wavePlayer
from time import sleep

player = wavePlayer(leftPin=Pin(14), rightPin=Pin(15))
player.play('cardinal-truncated-loud.wav')


def double_chirp(times=1):
    player = wavePlayer(leftPin=Pin(14), rightPin=Pin(15))
    for _ in range(times):
        player.play('cardinal-truncated-loud.wav')
        player.play('cardinal-truncated-loud.wav')
        sleep(0.6)
    

     
# ++ Init actions ++


minute_in_ms = 60000
hour_in_ms = 3600000

# servo_timer = Timer(-1)
# servo_timer.init(period=10000, mode=Timer.PERIODIC, callback=lambda t:oscillate())


# ==== old main version
from machine import Timer, Pin, PWM
from wavePlayer import wavePlayer
from time import sleep
import math


def oscillate_chirp(pin_number=28, sleep_interval=0.03, chirp_times=1):
    oscillate_pin = PWM(Pin(pin_number))
    oscillate_pin.freq(50)
    for position in range(1900, 8300, 50):
        oscillate_pin.duty_u16(position)
        sleep(sleep_interval)
    double_chirp(chirp_times)
    for position in range(8300, 1900, -50):
        oscillate_pin.duty_u16(position)
        sleep(sleep_interval)
    oscillate_pin.deinit()   

def double_chirp(times=1):
    player = wavePlayer(leftPin=Pin(15), rightPin=Pin(15))
    for _ in range(times):
        player.play('cardinal-truncated-loud.wav')
        player.play('cardinal-truncated-loud.wav')
        sleep(0.6)

def fade_in(eye_pin=16, sleep_time=0.01, max_brightness=0.4):
    eyes_pwm = PWM(Pin(eye_pin))
    eyes_pwm.freq(1000)  # Set the PWM frequency.
    duty = 0
    direction = 1
    for _ in range(256 * max_brightness):
        duty += direction
        eyes_pwm.duty_u16(duty * duty)
        sleep(sleep_time)
    
def fade_out(eye_pin=16, sleep_time=0.01):
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
    
def glow_rotate_chirp():
    fade_in()
    oscillate_chirp()
    fade_out()
    
    
main_timer = Timer(-1)
interval = 60000 * 5 # 60 seconds * 60 min = 1hr
main_timer.init(period=interval, mode=Timer.PERIODIC, callback=lambda t:glow_rotate_chirp())

glow_rotate_chirp()
