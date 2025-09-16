import math
import os
import random
import time
import audiobusio
import audiocore
import audiomixer
import array


class Amplifier:
    """
    Amplifier and audio out for bird using CircuitPython I2S audio.
    Requires 3 pins (in addition to 5v and ground):
    - LRC (Left-Right Clock/Word select)
    - BCLK (Bit Clock/Serial Clock)  
    - DIN (Serial Data In)
    Can play test tone, or specific WAV files.

    CircuitPython I2S is more flexible with sample rates than MicroPython.

    For Propmaker Feather, use:
    - board.I2S_BIT_CLOCK for bit_clk
    - board.I2S_WORD_SELECT for leftright
    - board.I2S_DATA for data_in
    """

    def __init__(self, leftright, bit_clk, data_in, audio_dir="", sample_rate=11000, bits=16):
        self.sample_rate = sample_rate
        self.bits = bits
        self.audio_dir = audio_dir

        # Initialize I2S audio output
        self.audio = audiobusio.I2SOut(bit_clk, leftright, data_in)

        # Initialize mixer for better audio handling
        self.mixer = audiomixer.Mixer(
            voice_count=1,
            sample_rate=self.sample_rate,
            channel_count=1,
            bits_per_sample=self.bits,
            samples_signed=True,
            buffer_size=4096
        )

        # Start audio output
        self.audio.play(self.mixer)

    def make_tone(self, frequency=440, duration=1.0, volume=0.5):
        """Generate a sine wave tone using the configured sample rate"""
        # FIXED: Use configured sample rate instead of hardcoded value
        length = int(self.sample_rate * duration)
        sine_wave = array.array("h", [0] * length)

        volume_factor = int(volume * (2 ** 15 - 1))

        for i in range(length):
            sine_wave[i] = int(
                math.sin(2 * math.pi * frequency * i / self.sample_rate) * volume_factor
            )

        return audiocore.RawSample(sine_wave, sample_rate=self.sample_rate)

    def play_tone(self, frequency=440, duration=1.0, volume=0.5):
        """Play a tone of specified frequency and duration"""
        tone = self.make_tone(frequency, duration, volume)
        self.mixer.voice[0].play(tone)

        # Wait for tone to finish
        while self.mixer.voice[0].playing:
            time.sleep(0.1)

    def play_wav(self, filename=None, volume=None):
        """
        Play a WAV file. If no filename specified, play a random WAV from audio_dir.
        """
        if filename is None:
            filename = self.random_wav()

        if not filename.startswith('/') and self.audio_dir:
            filename = f"/{self.audio_dir}/{filename}"

        try:
            with open(filename, "rb") as wav_file:
                wave = audiocore.WaveFile(wav_file)

                # Set volume if given
                if not volume is None:
                    self.mixer.voice[0].level = volume

                # Play the file
                self.mixer.voice[0].play(wave)

                # Wait for playback to complete
                while self.mixer.voice[0].playing:
                    time.sleep(0.1)

        except Exception as e:
            print(f"Error playing {filename}: {e}")

    def random_wav(self):
        """Select a random WAV file from the audio directory"""
        wavs = []
        audio_path = f'/{self.audio_dir}' if self.audio_dir else '/'

        try:
            for filename in os.listdir(audio_path):
                if filename.lower().endswith('.wav') and not filename.startswith('.'):
                    wavs.append(filename)
        except OSError:
            print(f"Could not list directory: {audio_path}")
            return None

        if not wavs:
            print(f"No WAV files found in {audio_path}")
            return None

        selected = random.choice(wavs)
        return f"{audio_path}/{selected}" if audio_path != '/' else selected

    def play_multiple_wav(self, count=2, delay=0.5):
        """Play multiple random WAV files with delay between them"""
        for _ in range(count):
            self.play_wav()
            if delay > 0:
                time.sleep(delay)

    def set_volume(self, volume):
        """Set the output volume (0.0 to 1.0)"""
        self.mixer.voice[0].level = max(0.0, min(1.0, volume))

    def stop(self):
        """Stop current playback"""
        self.mixer.voice[0].stop()

    def is_playing(self):
        """Check if audio is currently playing"""
        return self.mixer.voice[0].playing

    def deinit(self):
        """Clean up audio resources"""
        self.stop()
        self.audio.stop()
        self.audio.deinit()


# Helper functions for playing specific files
def play_file(filename, audio_dir=""):
    """Play a single WAV file using temporary Amplifier instance"""
    import board

    # Use default I2S pins for Propmaker Feather
    amp = Amplifier(
        board.I2S_WORD_SELECT,
        board.I2S_BIT_CLOCK,
        board.I2S_DATA,
        audio_dir=audio_dir
    )

    try:
        amp.play_wav(filename)
    finally:
        amp.deinit()


def play_tone_simple(frequency=440, duration=1.0):
    """Play a simple tone using temporary Amplifier instance"""
    import board

    amp = Amplifier(
        board.I2S_WORD_SELECT,
        board.I2S_BIT_CLOCK,
        board.I2S_DATA
    )

    try:
        amp.play_tone(frequency, duration)
    finally:
        amp.deinit()