import os
import random
import time
import audiocore
import audiobusio
import audiomixer
import pwmio
import array
import math

class Speaker:
    """
    Simple speaker class for CircuitPython that can play WAV files or tones.
    
    For I2S amplifiers (like MAX98357A), use I2S output.
    For simple PWM speakers, use PWM output.
    """
    
    def __init__(self, output_pin, mode="pwm", sample_rate=22050, audio_dir=""):
        """
        Initialize speaker.
        
        Args:
            output_pin: Pin for audio output
            mode: "pwm" for simple PWM audio, "i2s" for I2S (requires 3 pins)
            sample_rate: Audio sample rate
            audio_dir: Directory containing audio files
        """
        self.mode = mode
        self.sample_rate = sample_rate
        self.audio_dir = audio_dir
        self.output_pin = output_pin
        
        if mode == "pwm":
            self.pwm_out = pwmio.PWMOut(output_pin, variable_frequency=True)
            self.audio_out = None
        elif mode == "i2s":
            # For I2S mode, output_pin should be tuple of (bit_clock, word_select, data)
            if isinstance(output_pin, tuple) and len(output_pin) == 3:
                bit_clock, word_select, data = output_pin
                self.audio_out = audiobusio.I2SOut(bit_clock, word_select, data)
                
                # Set up mixer for better audio handling
                self.mixer = audiomixer.Mixer(
                    voice_count=1,
                    sample_rate=sample_rate,
                    channel_count=1,
                    bits_per_sample=16,
                    samples_signed=True,
                    buffer_size=32768
                )
                self.audio_out.play(self.mixer)
                self.pwm_out = None
            else:
                raise ValueError("I2S mode requires tuple of 3 pins: (bit_clock, word_select, data)")

    def play_tone(self, frequency=440, duration=1.0, volume=0.5):
        """Play a tone of specified frequency and duration"""
        if self.mode == "pwm":
            self._play_tone_pwm(frequency, duration, volume)
        elif self.mode == "i2s":
            self._play_tone_i2s(frequency, duration, volume)

    def _play_tone_pwm(self, frequency, duration, volume):
        """Play tone using PWM output"""
        self.pwm_out.frequency = int(frequency)
        duty_cycle = int(volume * 32767)  # 50% max duty cycle for volume control
        self.pwm_out.duty_cycle = duty_cycle
        time.sleep(duration)
        self.pwm_out.duty_cycle = 0

    def _play_tone_i2s(self, frequency, duration, volume):
        """Play tone using I2S output"""
        # Generate sine wave
        length = int(self.sample_rate * duration)
        sine_wave = array.array("h", [0] * length)
        
        volume_factor = int(volume * (2 ** 15 - 1))
        
        for i in range(length):
            sine_wave[i] = int(
                math.sin(2 * math.pi * frequency * i / self.sample_rate) * volume_factor
            )
        
        tone = audiocore.RawSample(sine_wave, sample_rate=self.sample_rate)
        self.mixer.voice[0].play(tone)
        
        # Wait for tone to finish
        while self.mixer.voice[0].playing:
            time.sleep(0.1)

    def play_wav(self, filename=None, volume=1.0):
        """
        Play a WAV file. If no filename specified, play random WAV from audio_dir.
        Note: PWM mode has limited WAV support. I2S mode recommended for WAV files.
        """
        if self.mode == "pwm":
            print("Warning: PWM mode has limited WAV support. Consider using I2S mode.")
            return False
            
        if filename is None:
            filename = self.random_wav()
            
        if filename is None:
            print("No WAV file to play")
            return False
        
        # Ensure full path
        if not filename.startswith('/') and self.audio_dir:
            filename = f"/{self.audio_dir}/{filename}"
        
        try:
            with open(filename, "rb") as wav_file:
                wave = audiocore.WaveFile(wav_file)
                
                # Set volume
                self.mixer.voice[0].level = volume
                
                # Play the file
                self.mixer.voice[0].play(wave)
                
                # Wait for playback to complete
                while self.mixer.voice[0].playing:
                    time.sleep(0.1)
                    
                return True
                
        except Exception as e:
            print(f"Error playing {filename}: {e}")
            return False

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

    def play_multiple_tones(self, frequencies, duration=0.5, volume=0.5):
        """Play a sequence of tones"""
        for freq in frequencies:
            self.play_tone(freq, duration, volume)

    def play_chirp(self, start_freq=1000, end_freq=2000, duration=0.5, volume=0.5):
        """Play a frequency sweep (chirp)"""
        if self.mode == "pwm":
            # Simple frequency sweep for PWM
            steps = 20
            freq_step = (end_freq - start_freq) / steps
            step_duration = duration / steps
            
            for i in range(steps):
                freq = start_freq + (i * freq_step)
                self.play_tone(freq, step_duration, volume)
        
        elif self.mode == "i2s":
            # Generate chirp using I2S
            length = int(self.sample_rate * duration)
            chirp_wave = array.array("h", [0] * length)
            
            volume_factor = int(volume * (2 ** 15 - 1))
            
            for i in range(length):
                # Linear frequency sweep
                t = i / self.sample_rate
                freq = start_freq + (end_freq - start_freq) * (t / duration)
                chirp_wave[i] = int(
                    math.sin(2 * math.pi * freq * t) * volume_factor
                )
            
            chirp = audiocore.RawSample(chirp_wave, sample_rate=self.sample_rate)
            self.mixer.voice[0].play(chirp)
            
            while self.mixer.voice[0].playing:
                time.sleep(0.1)

    def stop(self):
        """Stop current playback"""
        if self.mode == "pwm":
            self.pwm_out.duty_cycle = 0
        elif self.mode == "i2s":
            self.mixer.voice[0].stop()

    def is_playing(self):
        """Check if audio is currently playing"""
        if self.mode == "pwm":
            return self.pwm_out.duty_cycle > 0
        elif self.mode == "i2s":
            return self.mixer.voice[0].playing
        return False

    def deinit(self):
        """Clean up speaker resources"""
        self.stop()
        if self.pwm_out:
            self.pwm_out.deinit()
        if self.audio_out:
            self.audio_out.stop()
            self.audio_out.deinit()


# Helper functions for common use cases
def play_tone_simple(pin, frequency=440, duration=1.0, volume=0.5):
    """Play a simple tone using PWM"""
    speaker = Speaker(pin, mode="pwm")
    speaker.play_tone(frequency, duration, volume)
    speaker.deinit()

def play_wav_simple(i2s_pins, filename, audio_dir=""):
    """Play a WAV file using I2S"""
    speaker = Speaker(i2s_pins, mode="i2s", audio_dir=audio_dir)
    result = speaker.play_wav(filename)
    speaker.deinit()
    return result

def create_feather_speaker(audio_dir=""):
    """Create Speaker instance for Adafruit Feather with I2S"""
    import board
    
    try:
        i2s_pins = (board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)
        return Speaker(i2s_pins, mode="i2s", audio_dir=audio_dir)
    except AttributeError:
        print("This board doesn't have I2S pins. Using PWM on A0.")
        return Speaker(board.A0, mode="pwm", audio_dir=audio_dir)

def bird_chirp_sequence(speaker):
    """Play a bird-like chirp sequence"""
    # Play a series of chirps
    frequencies = [1200, 1500, 1800, 1500, 1200]
    speaker.play_multiple_tones(frequencies, duration=0.2, volume=0.7)
    
    time.sleep(0.3)
    
    # Play a trill
    speaker.play_chirp(1000, 2000, duration=0.5, volume=0.6)

def test_speaker():
    """Test speaker functionality"""
    import board
    
    print("=== Speaker Test ===")
    
    # Test PWM speaker
    print("Testing PWM speaker...")
    pwm_speaker = Speaker(board.A0, mode="pwm")
    pwm_speaker.play_tone(440, 0.5)  # A4 note
    pwm_speaker.play_tone(523, 0.5)  # C5 note
    pwm_speaker.deinit()
    
    # Test I2S speaker if available
    try:
        print("Testing I2S speaker...")
        i2s_pins = (board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)
        i2s_speaker = Speaker(i2s_pins, mode="i2s")
        i2s_speaker.play_tone(440, 0.5)
        bird_chirp_sequence(i2s_speaker)
        i2s_speaker.deinit()
    except AttributeError:
        print("No I2S pins available on this board")


if __name__ == "__main__":
    test_speaker()