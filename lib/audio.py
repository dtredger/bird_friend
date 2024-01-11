# # 3) Audio
#

# Bit clock pin: board.D9
# Word select pin: board.D10
# Data pin: board.D11
#
# Pico GP0 to breakout BCLK
# Pico GP1 to breakout LRC
# Pico GP2 to breakout DIN





import time
import array
import math
import audiocore
import board
import audiobusio

bclk = board.D9
lrc = board.D10
din = board.D11
audio = audiobusio.I2SOut(bclk, lrc, din)
# I2SOut(board.D9, board.D10, board.D11)

tone_volume = 1  # Increase this to increase the volume of the tone.
frequency = 440  # Set this to the Hz of the tone you want to generate.
length = 8000 // frequency
sine_wave = array.array("h", [0] * length)
for i in range(length):
    sine_wave[i] = int((math.sin(math.pi * 2 * i / length)) * tone_volume * (2 ** 15 - 1))
sine_wave_sample = audiocore.RawSample(sine_wave)


while True:
    print('play')
    audio.play(sine_wave_sample, loop=True)
    time.sleep(1)
    audio.stop()
    print('stopping')
    time.sleep(1)

# # # Feather does not include audioio
# import os # Audio
# import audiobusio # Audio
# import audiomixer # Audio
# import audiocore # Audio
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
# wavs = []
# for filename in os.listdir('/WAVs'):
#     if filename.lower().endswith('.wav') and not filename.startswith('.'):
#         wavs.append("/WAVs/"+filename)
# #
# # # ['/WAVs/crow_1-2.wav']
# #
#
# 24
# 25
# 13
#
# audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)
# mixer = audiomixer.Mixer(voice_count=1, sample_rate=11025, channel_count=1,
#                          bits_per_sample=16, samples_signed=True, buffer_size=32768)
#
# # # Generate one period of sine wave.
# # length = 8000 // 440
# # sine_wave = array.array("H", [0] * length)
# # for i in range(length):
# #     sine_wave[i] = int(math.sin(math.pi * 2 * i / length) * (2 ** 15) + 2 ** 15)
# #
# # sine_wave = audiocore.RawSample(sine_wave, sample_rate=8000)
# # i2s = audiobusio.I2SOut(board.D1, board.D0, board.D9)
# # i2s.play(sine_wave, loop=True)
# # time.time.sleep(1)
# # i2s.stop()
# #
# #
# # mixer.voice[0].level = 1 #Default
# # track_number = 0
# # wav_filename = wavs[track_number]
# # wav_file = open(wav_filename, "rb")
# # wave = audiocore.WaveFile(wav_file)
# # audio.play(mixer)
# # mixer.voice[0].play(wave)
