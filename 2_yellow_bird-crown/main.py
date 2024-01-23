from machine import Timer, Pin, PWM
from wavePlayer import wavePlayer
from time import sleep
import math
import _thread

MAX_EYE_BRIGHTNESS = 0.20

def fade_in(eye_pin=16, sleep_time=0.005, max_brightness=MAX_EYE_BRIGHTNESS):
    eyes_pwm = PWM(Pin(eye_pin))
    eyes_pwm.freq(1000)  # Set the PWM frequency.
    duty = 0
    direction = 1
    for _ in range(256 * max_brightness):
        duty += direction
        eyes_pwm.duty_u16(duty * duty)
        sleep(sleep_time)
    
def fade_out(eye_pin=16, sleep_time=0.005):
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
def look_left_right(pin_number=28, sleep_interval=0.016, rotation_pause=1.3):
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

def chirping(times=2):
    for _ in range(times):
        player = wavePlayer(leftPin=Pin(15), rightPin=Pin(15))
        player.play('bird-chirping-400.wav')

def eye_flash(times=3):
    for _ in range(times):
        fade_in()
        fade_out()

def rotate_and_chirp():
    fade_in()
    _thread.start_new_thread(chirping, ())
    look_left_right()
    fade_out()
    
# === Hour Timer === #
main_timer = Timer(-1)
interval = 60000 * 60 # 60 seconds * 60 min = 1hr
main_timer.init(period=interval, mode=Timer.PERIODIC, callback=lambda t:rotate_and_chirp())

eye_flash()
rotate_and_chirp()