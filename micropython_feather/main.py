# === CircuitPython code ===
#
# -- Propmaker Feather based bird --
#
# Main.py runs every time the feather is powered on.
# This code is based on previous birds, but uses CircuitPython
# (rather) than Micropython, so there are a few differences
# The features of this bird are:
#   1) Neck servo (common to all)
#   2) Fade in/out LED eyes (with new 200ohm resistor in circuit)
#   3) Audio out (with built-in amp, so much louder than other birds)
#   4) Light Sensor (controls when actions will happen)
#   5) Battery Power Reading
#   6) Randomizing Timer
#   7) Timed Actions
#
# The only new sensor is the light sensor, which gives the ability to
# disable the sound/motion during the night, without setting a time of day,
# which requires configuration. The appropriate light level is somewhat
# uncertain, but seems that sensor readings >= 1000 indicate no direct light
#
# Battery Power Reading is a circuit that allows reading the voltage of the
# lithium ion battery (which will cut out ~3.2v) available on the Feather.
#
# Randomizing Timer adds some randomness into the Timed Actions. This module can
# accept different sources of randomness, and return a countdown to the next time
# a timed action should happen

import os
import digitalio
import board
import time # Servo, LEDs,
import pwmio # Servo, LEDs
from adafruit_motor import servo # Servo
import analogio # Light sensor, Battery reading
import random # Randomizing Timer
import alarm # Timed actions

# CONFIGURATION
#
# Feather pin the servo is attached to
SERVO_PIN = board.EXTERNAL_SERVO
# the Feather pin the eyes are attached to
EYE_PIN = board.D12
# Audio Pins are preconfigured to use:
# I2S_BIT_CLOCK, I2S_WORD_SELECT, I2S_DATA
# Pin for light sensor
LIGHT_PIN = board.A1

# enable external power pin.
# provides power to the external components on Propmaker Feather (Audio, Server)
external_power = digitalio.DigitalInOut(board.EXTERNAL_POWER)
external_power.switch_to_output(value=True)


# 1) Neck Servo
#
# def rotate_servo_to(pin, end_pos, sleep_interval=0.01):
#     servo_pmw = pwmio.PWMOut(pin, duty_cycle=2 ** 15, frequency=50)
#     servo_obj = servo.Servo(servo_pmw)
#     current_angle = int(servo_obj.angle) if servo_obj.angle < 181 else 90
#     step = 1 if (current_angle < end_pos) else -1
#     for position in range(current_angle, end_pos, step):
#         servo_obj.angle = position
#         time.sleep(sleep_interval)
#     servo_pmw.deinit()
#
# def servo_left_right_center(pin=SERVO_PIN, rotation_pause=1.3):
#     """
#     On Restart, the pin's current location will always return 0
#     even though the actual position will be wherever it was when
#     powered off. This causes unexpected rotation if you specify a
#     starting point
#     """
#     # rotate one way, back past mid, then end in mid
#     rotate_servo_to(pin, 180)
#     time.sleep(rotation_pause)
#     rotate_servo_to(pin, 0)
#     time.sleep(rotation_pause)
#     rotate_servo_to(pin, 90)
#
#
# # 2) LED Eyes
#
# def fade_in(pin, sleep_interval=0.02, max_brightness=1.0):
#     max_duty = int(max_brightness * 65535)
#     pwm_pin = pwmio.PWMOut(pin)
#     for cycle in range(0, max_duty, 1000):
#         pwm_pin.duty_cycle = cycle
#         time.sleep(sleep_interval)
#     pwm_pin.deinit()
#
# def fade_out(pin, sleep_interval=0.02):
#     pwm_pin = pwmio.PWMOut(pin)
#     for cycle in range(pwm_pin.duty_cycle, 0, -1000):
#         pwm_pin.duty_cycle = cycle
#         time.sleep(sleep_interval)
#     pwm_pin.deinit()
#
# def flash_eyes(pin=EYE_PIN, times=2):
#     for _ in range(times):
#         fade_in(pin)
#         fade_out(pin)
#


# # 3) Audio
#
# # # Feather does not include audioio
import os # Audio
import audiobusio # Audio
import audiomixer # Audio
import audiocore # Audio
# # Non-feather: from audioio import AudioOut
# from audiopwmio import PWMAudioOut as AudioOut # Audio
#
#
# #
# def play_file(filename):
#     """Plays a WAV file in its entirety (function blocks until done)."""
#     print("Playing", filename)
#     with open(f"{filename}", "rb") as file:
#         audio.play(audiocore.WaveFile(file))
#         # Randomly flicker the LED a bit while audio plays
#         while audio.playing:
#             # led.duty_cycle = random.randint(5000, 30000)
#             time.sleep(0.1)
#     # led.duty_cycle = 65535  # Back to full brightness
# #
wavs = []
for filename in os.listdir('/WAVs'):
    if filename.lower().endswith('.wav') and not filename.startswith('.'):
        wavs.append("/WAVs/"+filename)
# #
# # # ['/WAVs/crow_1-2.wav']
# #
#
# 24
# 25
# 13
#
audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)
mixer = audiomixer.Mixer(voice_count=1, sample_rate=11025, channel_count=1,
                         bits_per_sample=16, samples_signed=True, buffer_size=32768)

# Generate one period of sine wave.
# length = 8000 // 440
# sine_wave = array.array("H", [0] * length)
# for i in range(length):
#     sine_wave[i] = int(math.sin(math.pi * 2 * i / length) * (2 ** 15) + 2 ** 15)

# sine_wave = audiocore.RawSample(sine_wave, sample_rate=8000)
# i2s = audiobusio.I2SOut(board.D1, board.D0, board.D9)
# i2s.play(sine_wave, loop=True)
# time.time.sleep(1)
# i2s.stop()


mixer.voice[0].level = 1 #Default
track_number = 0
wav_filename = wavs[track_number]

wav_file = open(wav_filename, "rb")
wave = audiocore.WaveFile(wav_file)
audio.play(mixer)
mixer.voice[0].play(wave)


# 4) Light Sensor

# This sensor has a range somewhere between 100-1300
def is_too_dark(a_pin=LIGHT_PIN, darkness_thresh=1000):
    sensor = analogio.AnalogIn(a_pin)
    darkness_level = sensor.value
    sensor.deinit()
    return True if darkness_level > darkness_thresh else False


# 5) Power Reading

# Wiring available on
# learn.adafruit.com/adafruit-rp2040-prop-maker-feather/power-management

def get_voltage(pin):
    return pin.value / 65535 * 3.3 * 2

def log_voltage(pin, log_file='logging.txt'):
    vbat_voltage = analogio.AnalogIn(board.A3)
    battery_voltage = get_voltage(vbat_voltage)
    try:
        with open(log_file, 'a') as fp:
            fp.write(f"{time.monotonic()} since reset, battery: {battery_voltage}")
    except Exception as e:
        print(e)
        pass


# 6) Randomizing Timer

# Returns a time within +/- range_pct of an hour, in seconds
def random_hourish_s():
    range_pct = 15
    time_mod = random.randint(60 - range_pct, 60 + range_pct)
    return (60 * time_mod)


# 7) == Timed Actions ==

def regular_interaction():
    if is_too_dark():
        flash_eyes()
        # check again in 10 min
        next_run_s = (60 * 10)
    else:
        fade_in()
        servo_left_right_center()
        fade_out()
        next_run_s = random_hourish_s()
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + next_run_s)
    # Exit the program, and then deep sleep until the alarm wakes us.
    alarm.exit_and_deep_sleep_until_alarms(time_alarm)
