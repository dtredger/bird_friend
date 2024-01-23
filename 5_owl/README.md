# Owl
#### v1 Jan 2024

## Board & Hardware
This bird uses a Raspberry Pi clone called [Pico Board RP2040 Dual-Core 264KB ARM Low-Power Microcomputers High-Performance Cortex-M0+ Processor]
(https://www.aliexpress.com/item/1005005844675453.html?spm=a2g0o.order_list.order_list_main.4.58a71802wqriLi).

- Audio uses a 4ohm 3watt speaker and a max98357A amplifier.
- The neck is a standard 3-wire microservo.
- The eyes are two LEDs.
- The light sensor is a photoresistor (temp sensor is built into the board).

The bird itself is a white styrofoam-filled owl from Dollarama that has been hollowed out, and servo inserted into neck (similar to #4 "ronny"). The only difference is this bird includes a base box, since the speaker is too big to fit inside.

## Modules
This is the first bird that makes use of reusable code in the form of modules for specific types of functionality. Currently, the modules available are:
- LEDs (eyes)
- Sensors (Light Sensor, Temperature sensor)
- Servo (neck microservo)
- Speaker (4ohm speaker wired with max98357A amplifier)


## Actions
Like the others, this bird will run code every `INTERVAL_MINUTES`, which is hardcoded into `main.py`. At that instant, the light level is checked against a minimum threshold. If the light is above the minimum, it will light up eyes, rotate, and hoot. If it is too dark, it will flash its eyes twice.

The light sensor was included because previous micropython-based birds without connectivity (ie, all of them other than #1 and #3) have no ability to set time of day, so would be loud if they went off in the middle of the night. This is especially necessary, since this is the first micropython bird to include an amplifier, whereas the previous ones were generally very quiet.
