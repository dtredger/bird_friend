# Chonky Crow
#### v1 Sep 2025

## Board & Hardware
This bird uses a Adafruit Propmaker Feather

- Audio uses a small 8ohm 2watt speaker and amplifier built into the propmaker feather
- The neck is a standard 3-wire microservo.
- The eyes are two LEDs wired in parallel with 200ohm resistor.
- The light sensor is a photoresistor 
- (temp sensor is built into the board but not used)
- Button for mode-switch and time setting


## Modules
This bird uses modules from `/lib` for specific functionality. Currently, the modules available are:
- LEDs (eyes)
- Sensors (Light Sensor, Temperature sensor)
- Servo (neck microservo)
- Amplifier (8ohm speaker wired with built-in amplifier)


## Actions
Like the others, this bird will run code every `INTERVAL_MINUTES`, which is hardcoded into `main.py`. At that instant, the light level is checked against a minimum threshold. If the light is above the minimum, it will light up eyes, rotate, and make sound. If it is too dark, it will flash its eyes twice.

The light sensor was included because some previous birds had no ability to set time of day, so would be loud if they went off in the middle of the night. This is necessary since this bird includes an amplifier, whereas most previous ones did not.


------

# Prop-Maker Feather Crow Bird Wiring Guide

## Required Components

1. **Adafruit RP2040 Prop-Maker Feather**
2. **Standard hobby servo** (3-wire: red=5V, black=GND, yellow/white=signal)
3. **4-8Ω speaker** (3W max) 
4. **2x LEDs** (for eyes)
5. **1x 200Ω resistor** (for LEDs)
6. **1x Photoresistor** (light sensor)
7. **1x 10kΩ resistor** (pulldown for light sensor)
8. **Jumper wires and breadboard** (optional for prototyping)

## Prop-Maker Feather Built-in Features Used

- **Servo header**: 3-pin connector (no wiring needed!)
- **I2S amplifier**: Built-in MAX98357 with speaker terminals
- **External power control**: Enables/disables servo and audio
- **Battery connector**: Optional LiPo battery support

## Wiring Connections

### 1. Servo
```
Servo → Built-in 3-pin header on Feather
```
### 2. Speaker (EASY - Screw terminals)
```
Speaker → Built-in amplifier terminals
```
**Use the screw terminals - no soldering needed!**

### 3. LEDs (Eyes)
```
For dual LEDs (both eyes):
LED1 Cathode → A0 → 200Ω resistor → GND
LED2 Cathode → A0 → 200Ω resistor → GND
(Wire LEDs in parallel)
```

### 4. Light Sensor (Photoresistor)
```
3.3V → Photoresistor → A1 (analog input)
A1 → 10kΩ resistor → GND

Voltage divider circuit:
3.3V ──┬── Photoresistor ──┬── A1
       │                   │
       └── 10kΩ resistor ──┴── GND
```

## Detailed Pin Assignments

| Component | Feather Pin | Notes |
|-----------|-------------|-------|
| Servo | Built-in header | Uses `board.EXTERNAL_SERVO` |
| Speaker | Built-in terminals | I2S amplifier (GPIO16,17,18) |
| LEDs | A0 | Through 200Ω resistor |
| Light Sensor | A1 | With 10kΩ pulldown resistor |
| External Power | GPIO23 | **MUST be enabled in code** |

## Power Requirements

### External Power Control ⚠️ IMPORTANT
The Prop-Maker Feather requires enabling external power for servo and audio:
```python
external_power = digitalio.DigitalInOut(board.EXTERNAL_POWER)
external_power.direction = digitalio.Direction.OUTPUT
external_power.value = True  # Enable servo and audio power
```

### Power Options
1. **USB-C**: 5V from computer/wall adapter
2. **LiPo Battery**: 3.7V battery in JST connector (automatically charges when USB connected)
3. **External 5V**: Via VBUS pin (advanced)

## Breadboard Layout Example

```
     Feather RP2040 Prop-Maker
    ┌─────────────────────────┐
    │ USB-C            3.3V ○ │
    │                       ○ │
    │ A0 ○                  ○ │──── LED + (via 200Ω resistor)
    │ A1 ○                  ○ │
    │ A2 ○              GND ○ │──── LED -, 10kΩ resistor
    │                         │
    │ Built-in servo header:  │
    │ [V+][G][Signal]         │──── Servo plugs directly in
    │                         │
    │ Speaker terminals:      │
    │ [+] [-]                 │──── Speaker wires screw in
    └─────────────────────────┘
             │
             │ Light sensor circuit:
             ○ 3.3V ── Photoresistor ── A1 ── 10kΩ ── GND
```

## Audio Files Setup

1. Create an `audio/` folder on the CIRCUITPY drive
2. Add WAV files (11,000kHz, 16-bit, mono recommended)
3. Files will be played randomly, or caws counted in Clock mode based on the configuration in `config.json`.

Example audio folder:
```
CIRCUITPY/
├── code.py
├── audio/
│   ├── crow_single.wav
│   ├── crow_double_.wav
│   └── crow_quadruple.wav
```

## Troubleshooting

### Servo doesn't move
- ✅ Check external power is enabled in code
- ✅ Verify servo is plugged into built-in header correctly
- ✅ Ensure USB/battery provides enough power

### No audio
- ✅ Check external power is enabled in code  
- ✅ Verify speaker connections to terminals
- ✅ Check audio files exist in `/audio/` folder
- ✅ Try a different speaker (4-8Ω, up to 3W)

### LEDs don't light
- ✅ Check LED polarity (cathode to pin, anode to GND)
- ✅ Verify 200Ω resistor is in circuit
- ✅ Test with multimeter for continuity

### Light sensor not responding
- ✅ Check voltage divider wiring
- ✅ Verify 10kΩ pulldown resistor
- ✅ Test sensor values in REPL: `light_sensor.value`
- ✅ Adjust `LIGHT_THRESHOLD` in code as needed

### Board not responding
- ✅ Check power supply (USB-C or battery)
- ✅ Try soft reset: Ctrl+C then Ctrl+D in serial console
- ✅ Hard reset: Press reset button on board

## Testing Individual Components

### Test Servo
```python
import board
import pwmio
from adafruit_motor import servo

# Enable external power first!
external_power = digitalio.DigitalInOut(board.EXTERNAL_POWER)
external_power.direction = digitalio.Direction.OUTPUT  
external_power.value = True

servo_pwm = pwmio.PWMOut(board.EXTERNAL_SERVO, duty_cycle=2**15, frequency=50)
my_servo = servo.Servo(servo_pwm)
my_servo.angle = 90  # Center
```

### Test Audio
```python
import board
import audiocore
import audiobusio

audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)
with open("audio/test.wav", "rb") as wave_file:
    wave = audiocore.WaveFile(wave_file)
    audio.play(wave)
```

### Test Light Sensor
```python
import board
import analogio

light = analogio.AnalogIn(board.A1)
print(f"Light reading: {light.value}")  # 0-65535
```
