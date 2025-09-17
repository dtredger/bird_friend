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

        # Sound file configuration
        self.sound_files = {}  # Will be set by set_sound_files()
        self.chime_strategy = "intelligent"
        self.fallback_behavior = "repeat_single"

    def set_sound_files(self, sound_files_config, chime_strategy="intelligent", fallback_behavior="repeat_single"):
        """
        Configure sound files with their caw counts for intelligent selection.

        Args:
            sound_files_config: Dict mapping filename to caw count (e.g., {"crow1.wav": 2})
            chime_strategy: "intelligent", "random", or "single_file_only"
            fallback_behavior: "repeat_single", "closest_match", or "random_fill"
        """
        self.sound_files = sound_files_config or {}
        self.chime_strategy = chime_strategy
        self.fallback_behavior = fallback_behavior

        if self.sound_files:
            print(f"🎵 Configured {len(self.sound_files)} sound files for intelligent chiming")
            for filename, count in self.sound_files.items():
                print(f"   {filename}: {count} caws")
        else:
            print("⚠️ No sound files configured - using random selection")

    def select_files_for_caw_count(self, target_caws):
        """
        Intelligently select sound files that add up to the target number of caws.

        Args:
            target_caws: Number of caws needed (e.g., 12 for 12 o'clock)

        Returns:
            List of filenames to play in sequence
        """
        if not self.sound_files or self.chime_strategy == "random":
            # Fall back to random selection
            return [None] * target_caws  # Will use random_wav() for each

        if self.chime_strategy == "single_file_only":
            # Only use files with 1 caw
            single_caw_files = [f for f, count in self.sound_files.items() if count == 1]
            if single_caw_files:
                return [random.choice(single_caw_files) for _ in range(target_caws)]
            else:
                print("⚠️ No single-caw files available, using random")
                return [None] * target_caws

        # Intelligent strategy - try to get exact count
        return self._find_optimal_file_combination(target_caws)

    def _find_optimal_file_combination(self, target_caws):
        """
        Find the best combination of files to match target caw count.
        Uses a greedy algorithm to minimize the number of files played.
        """
        if target_caws <= 0:
            return []

        # Get available files sorted by caw count (descending)
        available_files = [(filename, count) for filename, count in self.sound_files.items()
                           if self._file_exists(filename)]

        if not available_files:
            print("⚠️ No configured sound files found, using random")
            return [None] * target_caws

        available_files.sort(key=lambda x: x[1], reverse=True)  # Sort by caw count, largest first

        # Greedy selection - use largest files first
        selected_files = []
        remaining_caws = target_caws

        while remaining_caws > 0:
            # Find the largest file that doesn't exceed remaining caws
            selected_file = None

            for filename, count in available_files:
                if count <= remaining_caws:
                    selected_file = (filename, count)
                    break

            if selected_file:
                filename, count = selected_file
                selected_files.append(filename)
                remaining_caws -= count
                print(f"   Selected {filename} ({count} caws), {remaining_caws} remaining")
            else:
                # Can't find a file that fits, handle with fallback behavior
                selected_files.extend(self._handle_fallback(remaining_caws, available_files))
                break

        if len(selected_files) == 0:
            print("⚠️ Could not select any files, using random")
            return [None] * target_caws

        print(
            f"🎯 Selected {len(selected_files)} files for {target_caws} caws: {[f.split('/')[-1] for f in selected_files]}")
        return selected_files

    def _handle_fallback(self, remaining_caws, available_files):
        """Handle cases where we can't make an exact match"""
        if self.fallback_behavior == "repeat_single":
            # Use single-caw files for remaining count
            single_caw_files = [f for f, count in available_files if count == 1]
            if single_caw_files:
                chosen_file = random.choice(single_caw_files)[0]
                print(f"   Fallback: Using {chosen_file} × {remaining_caws}")
                return [chosen_file] * remaining_caws
            else:
                # No single-caw files, use smallest available
                if available_files:
                    smallest_file = min(available_files, key=lambda x: x[1])[0]
                    print(f"   Fallback: Using smallest file {smallest_file}")
                    return [smallest_file]
                return []

        elif self.fallback_behavior == "closest_match":
            # Use the smallest file available (might overshoot)
            if available_files:
                smallest_file = min(available_files, key=lambda x: x[1])[0]
                print(f"   Fallback: Closest match with {smallest_file}")
                return [smallest_file]
            return []

        elif self.fallback_behavior == "random_fill":
            # Fill with random files
            print(f"   Fallback: Random files for remaining {remaining_caws}")
            return [None] * remaining_caws

        return []

    def _file_exists(self, filename):
        """Check if a sound file exists"""
        if not filename.startswith('/') and self.audio_dir:
            full_path = f"/{self.audio_dir}/{filename}"
        else:
            full_path = filename

        try:
            with open(full_path, 'rb'):
                return True
        except:
            return False

    def play_chime_sequence(self, target_caws, volume=None):
        """
        Play a sequence of sounds to achieve the target number of caws.

        Args:
            target_caws: Number of caws needed
            volume: Optional volume override

        Returns:
            List of files that were played
        """
        if target_caws <= 0:
            return []

        # Select appropriate files
        selected_files = self.select_files_for_caw_count(target_caws)

        print(f"🔔 Playing chime sequence for {target_caws} caws...")

        # Play each file in sequence
        played_files = []
        for filename in selected_files:
            if filename is None:
                # Use random file for this slot
                filename = self.random_wav()

            if filename:
                self.play_wav(filename, volume)
                played_files.append(filename)

                # Small pause between files if playing multiple
                if len(selected_files) > 1:
                    time.sleep(0.3)

        print(f"✅ Chime sequence complete - played {len(played_files)} files")
        return played_files

    # Keep existing methods unchanged
    def make_tone(self, frequency=440, duration=1.0, volume=0.5):
        """Generate a sine wave tone with lower sample rate to save memory"""
        tone_sample_rate = 8000
        length = int(tone_sample_rate * duration)
        sine_wave = array.array("h", [0] * length)

        volume_factor = int(volume * (2 ** 15 - 1))

        for i in range(length):
            sine_wave[i] = int(
                math.sin(2 * math.pi * frequency * i / tone_sample_rate) * volume_factor
            )

        return audiocore.RawSample(sine_wave, sample_rate=tone_sample_rate)

    def play_tone(self, frequency=440, duration=1.0, volume=0.5):
        """Play a tone of specified frequency and duration"""
        tone = self.make_tone(frequency, duration, volume)
        self.mixer.voice[0].play(tone)

        while self.mixer.voice[0].playing:
            time.sleep(0.1)

    def play_wav(self, filename=None, volume=None):
        """Play a WAV file. If no filename specified, play a random WAV from audio_dir."""
        if filename is None:
            filename = self.random_wav()

        if not filename.startswith('/') and self.audio_dir:
            filename = f"/{self.audio_dir}/{filename}"

        try:
            with open(filename, "rb") as wav_file:
                wave = audiocore.WaveFile(wav_file)

                if volume is not None:
                    self.mixer.voice[0].level = volume

                self.mixer.voice[0].play(wave)

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

    def get_sound_file_info(self):
        """Get information about configured sound files"""
        if not self.sound_files:
            return "No sound files configured"

        total_files = len(self.sound_files)
        total_caws = sum(self.sound_files.values())
        max_caws = max(self.sound_files.values()) if self.sound_files else 0

        return {
            "total_files": total_files,
            "total_possible_caws": total_caws,
            "max_single_file_caws": max_caws,
            "strategy": self.chime_strategy,
            "fallback": self.fallback_behavior,
            "files": self.sound_files
        }

    def deinit(self):
        """Clean up audio resources"""
        self.stop()
        self.audio.stop()
        self.audio.deinit()


# Helper functions for playing specific files
def play_file(filename, audio_dir=""):
    """Play a single WAV file using temporary Amplifier instance"""
    import board

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


def play_chime_for_hour(hour, audio_dir="", sound_files_config=None):
    """Helper function to play appropriate chimes for an hour"""
    import board

    amp = Amplifier(
        board.I2S_WORD_SELECT,
        board.I2S_BIT_CLOCK,
        board.I2S_DATA,
        audio_dir=audio_dir
    )

    try:
        if sound_files_config:
            amp.set_sound_files(sound_files_config)

        return amp.play_chime_sequence(hour)
    finally:
        amp.deinit()