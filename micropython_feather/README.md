This board is `Adafruit RP2040 Prop-Maker Feather` (note the difference with a regular feather, which lacks the speaker and servo-specific pins)

With a fresh CircuitPython install, on your CIRCUITPY drive, you'll find a code.py file containing print("Hello World!") and an empty lib folder. If your CIRCUITPY drive does not contain a code.py file, you can easily create one and save it to the drive. CircuitPython looks for code.py and executes the code within the file automatically when the board starts up or resets. Following a change to the contents of CIRCUITPY, such as making a change to the code.py file, the board will reset, and the code will be run. You do not need to manually run the code.


serial console - `screen /dev/tty.usbmodem14101 115200` (last number is baud rate)

- `ctrl-c` to enter REPL


EXTERNAL_POWER in CircuitPython and PIN_EXTERNAL_POWER in Arduino.
It is disabled by default, so you will need to set the pin high to power the
external NeoPixels, servo motor header pins and I2S amplifier
```
external_power = DigitalInOut(board.EXTERNAL_POWER)
external_power.switch_to_output(value=True)
```

Amplifier requires EXTERNAL_POWER, and communicates with:
> Data - Located on GPIO16. It can be accessed via I2S_DATA in CircuitPython and PIN_I2S_DATA in Arduino.
> Clock - Located on GPIO17. It can be accessed via I2S_BIT_CLOCK in CircuitPython and PIN_I2S_BIT_CLOCK in Arduino.
> Word Select - Located on GPIO18. It can be accessed via I2S_WORD_SELECT in CircuitPython and PIN_I2S_WORD_SELECT in Arduino.
