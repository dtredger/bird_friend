import math
import struct
from machine import Pin, I2S

class Speaker:
    """
    Speaker and audio out for bird. Uses I2S audio,
    which requires 3 pins (in addition to 5v and ground):
    - LRC (Left-Right Clock/Word select)
    - BCLK (Bit Clock/Serial Clock)
    - DIN (Serial Data In)
    Can play test tone, or specific WAV.
    All WAVs must currently have the same sample_rate (11_000).
    `play_wav` buffer and bytearray may also need to be adjusted for different
    files.
    
    Anecdotally, 8ohm 0.5w speakers are too quiet to be effective, but 2w
    speakers seem fine. If necessary, solder 100k resistor between "gain"
    and gnd on the amplifier to boost level by +15 decibels
    """
    def __init__(self, leftright, bit_clk, data_in, wav_file):
        self.sample_rate = 11_000
        self.bits = 16
        self.wav_file = wav_file
        self.audio_out = I2S(1,
                             sck=Pin(bit_clk),
                             ws=Pin(leftright),
                             sd=Pin(data_in),
                             mode=I2S.TX,
                             bits=self.bits,
                             format=I2S.MONO,
                             rate=self.sample_rate,
                             ibuf=20000)

    def make_tone(self, rate=22_050, frequency=440):
        # create a buffer containing the pure tone samples
        samples_per_cycle = rate // frequency
        sample_size_in_bytes = self.bits // 8
        samples = bytearray(samples_per_cycle * sample_size_in_bytes)
        volume_reduction_factor = 32
        range = pow(2, self.bits) // 2 // volume_reduction_factor

        if self.bits == 16:
            format = "<h"
        else:  # assume 32 bits
            format = "<l"

        for i in range(samples_per_cycle):
            sample = range + int((range - 1) * math.sin(2 * math.pi * i / samples_per_cycle))
            struct.pack_into(format, samples, i * sample_size_in_bytes, sample)
        return samples

    def play_tone(self):
        samples = self.make_tone()
        self.audio_out.write(samples)

    def play_wav(self):
        """
        Depending on wav file, seek location and bytearray size may need
        to be modified (200, 30_000 work well with 25kb 1 second wav)
        """
        wav = open(self.wav_file, "rb")
        _ = wav.seek(200)  # advance to first byte of Data section in WAV file
        # allocate sample array
        wav_samples = bytearray(30_000)
        # memoryview used to reduce heap allocation
        wav_samples_mv = memoryview(wav_samples)
        num_read = wav.readinto(wav_samples_mv)
        self.audio_out.write(wav_samples_mv[:num_read])

    def select_wav(self):
        wavs = []
        for filename in os.listdir(f'/{self.audio_dir}'):
            if filename.lower().endswith('.wav') and not filename.startswith('.'):
                wavs.append("/WAVs/"+filename)

    def __del__(self):
        self.audio_out.deinit()





# # === CircuitPython ===
#
# import time
# import array
# import math
# import audiocore
# import board
# import audiobusio
#
# bclk = board.D9
# lrc = board.D10
# din = board.D11
# audio = audiobusio.I2SOut(bclk, lrc, din)
# # I2SOut(board.D9, board.D10, board.D11)
#
# tone_volume = 1  # Increase this to increase the volume of the tone.
# frequency = 440  # Set this to the Hz of the tone you want to generate.
# length = 8000 // frequency
# sine_wave = array.array("h", [0] * length)
# for i in range(length):
#     sine_wave[i] = int((math.sin(math.pi * 2 * i / length)) * tone_volume * (2 ** 15 - 1))
# sine_wave_sample = audiocore.RawSample(sine_wave)
#
#
# while True:
#     print('play')
#     audio.play(sine_wave_sample, loop=True)
#     time.sleep(1)
#     audio.stop()
#     print('stopping')
#     time.sleep(1)
#
# # # Feather does not include audioio
# import os # Audio
# import audiobusio # Audio
# import audiomixer # Audio
# import audiocore # Audio
# # Non-feather: from audioio import AudioOut
# from audiopwmio import PWMAudioOut as AudioOut # Audio
#
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
#
# audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)
# mixer = audiomixer.Mixer(voice_count=1, sample_rate=11025, channel_count=1,
#                          bits_per_sample=16, samples_signed=True, buffer_size=32768)
#
# # Generate one period of sine wave.
# length = 8000 // 440
# sine_wave = array.array("H", [0] * length)
# for i in range(length):
#     sine_wave[i] = int(math.sin(math.pi * 2 * i / length) * (2 ** 15) + 2 ** 15)
#
# sine_wave = audiocore.RawSample(sine_wave, sample_rate=8000)
# i2s = audiobusio.I2SOut(board.D1, board.D0, board.D9)
# i2s.play(sine_wave, loop=True)
# time.time.sleep(1)
# i2s.stop()
#
#
# mixer.voice[0].level = 1 #Default
# track_number = 0
# wav_filename = wavs[track_number]
# wav_file = open(wav_filename, "rb")
# wave = audiocore.WaveFile(wav_file)
# audio.play(mixer)
# mixer.voice[0].play(wave)
