# Wave.py guide

If you are not using the I2S to play audio (for example with an amplifier),
you can use wave.py library to play audio (with one (or two) pins and GND).
```
import wave
from wavePlayer import wavePlayer

audio_file = wave.open(path)
length_s = audio_file.getnframes() / audio_file.getframerate()

player = wavePlayer(leftPin=Pin(SPEAKER_PIN), rightPin=Pin(SPEAKER_PIN))
player.play(audio_file)

```
