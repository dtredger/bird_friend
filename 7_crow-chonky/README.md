# Baby Crow
#### v1 Mar 2024

## Board & Hardware
This bird uses a Raspberry Pi clone called [Pico Board RP2040 Dual-Core 264KB ARM Low-Power Microcomputers High-Performance Cortex-M0+ Processor]
(https://www.aliexpress.com/item/1005005844675453.html?spm=a2g0o.order_list.order_list_main.4.58a71802wqriLi).

- Audio uses a mini 8ohm 2watt speaker and a max98357A amplifier. The 100k resistor that
makes audio louder (between gain & ground) was removed because the chosen wav file 
seems much louder than the owl sound for bird #5.
- The neck is a standard 3-wire microservo.
- The eyes are two LEDs wired in parallel with 220ohm.
- The light sensor is a photoresistor 
- (temp sensor is built into the board but not used)


## Modules
This bird uses modules from `/lib` for specific functionality. Currently, the modules available are:
- LEDs (eyes)
- Sensors (Light Sensor, Temperature sensor)
- Servo (neck microservo)
- Speaker (4ohm speaker wired with max98357A amplifier)


## Actions
Like the others, this bird will run code every `INTERVAL_MINUTES`, which is hardcoded into `main.py`. At that instant, the light level is checked against a minimum threshold. If the light is above the minimum, it will light up eyes, rotate, and make sound. If it is too dark, it will flash its eyes twice.

The light sensor was included because some previous birds had no ability to set time of day, so would be loud if they went off in the middle of the night. This is necessary since this bird includes an amplifier, whereas most previous ones did not.
