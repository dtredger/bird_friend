# CircuitPython Bird Libraries Installation

## 1. Install CircuitPython

First, install CircuitPython on your board:

1. Download the latest CircuitPython UF2 file for your board from [circuitpython.org](https://circuitpython.org/downloads)
2. Put your board in bootloader mode (usually double-tap reset button)
3. Copy the UF2 file to the board's USB drive
4. The board will restart with CircuitPython

## 2. Required CircuitPython Libraries

Download the CircuitPython Library Bundle from [circuitpython.org/libraries](https://circuitpython.org/libraries) and copy these libraries to your board's `lib/` directory:

### Core Libraries (Required)
```
adafruit_motor/         # For servo control
```

### Built-in Modules (Usually Included)
These should be available in CircuitPython by default:
- `analogio`           # ADC input
- `audiobusio`         # I2S audio
- `audiocore`          # Audio file handling  
- `audiomixer`         # Audio mixing
- `board`              # Pin definitions
- `digitalio`          # Digital I/O
- `microcontroller`    # CPU info/control
- `pwmio`              # PWM output
- `time`               # Time functions
- `alarm`              # Deep sleep (on supported boards)

## 3. File Structure

Your CircuitPython device should have this structure:

```
/
├── code.py                    # Your main program
├── lib/
│   ├── adafruit_motor/        # Downloaded library
│   ├── servos.py             # Bird library
│   ├── leds.py               # Bird library
│   ├── sensors.py            # Bird library
│   ├── speaker.py            # Bird library
│   ├── battery.py            # Bird library
│   └── schedule.py           # Bird library
├── sounds/                   # Audio files (optional)
│   ├── chirp1.wav
│   └── chirp2.wav
└── data.json                 # Configuration file
```

## 4. Installation Steps

### Step 1: Copy Bird Libraries
Copy all the `.py` files from this directory to your board's `lib/` folder:
- `servos.py`
- `leds.py` 
- `sensors.py`
- `speaker.py`
- `battery.py`
- `schedule.py`

### Step 2: Install Dependencies
Copy the `adafruit_motor` folder from the CircuitPython Library Bundle to your board's `lib/` folder.

### Step 3: Copy Example Code
Copy `example_main.py` to your board as `code.py` (or create your own main program).

### Step 4: Copy Configuration
Copy `data.json` to your board's root directory and modify settings as needed.

### Step 5: Add Audio Files (Optional)
If using audio features, create a `sounds/` directory and add WAV files.

## 5. Board-Specific Setup

### Adafruit Feather RP2040
- Built-in I2S audio support
- Built-in battery monitoring via `VOLTAGE_MONITOR`
- Use these pin assignments:
  ```python
  import board
  servo_pin = board.A0
  led_pin = board.A1
  light_sensor_pin = board.A2
  i2s_pins = (board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)
  battery_pin = board.VOLTAGE_MONITOR
  ```

### Raspberry Pi Pico W
- No built-in I2S (use PWM audio)
- No built-in battery monitoring
- Use these pin assignments:
  ```python
  import board
  servo_pin = board.GP0
  led_pin = board.GP1
  light_sensor_pin = board.GP26  # ADC pin
  speaker_pin = board.GP2        # PWM audio
  ```

## 6. Advanced Features

### Deep Sleep Mode
For battery-powered projects:
```python
import alarm
import time

# Sleep for 1 hour
time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 3600)
alarm.exit_and_deep_sleep_until_alarms(time_alarm)
```

### WiFi Integration (Pico W)
```python
import wifi
import socketpool

wifi.radio.connect("SSID", "password")
pool = socketpool.SocketPool(wifi.radio)
# Add web server or IoT features
```

### Custom Scheduling
Modify `data.json` to change behavior:
```json
{
    "earliest": "06:30",
    "latest": "23:30", 
    "interval": "30",
    "volume": 0.5,
    "debug": false
}
```
