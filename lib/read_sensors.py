
#   4) Light Sensor (controls when actions will happen)

# === CIRCUITPYTHON ===
# class LightSensor:
#     """
#     Light Sensor that returns higher number in darkness.
#     Around 1000+ is the level of night-time.
#     """
#     def __init__(self, sensor_pin):
#         self.threshold = 1000
#         self.sensor = analogio.AnalogIn(sensor_pin)
#
#     # This sensor has a range somewhere between 100-1300
#     def is_too_dark(self):
#         return True if self.sensor.value > self.threshold else False

# === Micropython ===


# P=ADC(Pin(26))

from machine import Pin, ADC

class LightSensor:
    """
    Light Sensor that returns higher number in darkness.
    Around 1000+ is the level of night-time.
    A0 Pin is number 26
    """
    def __init__(self, sensor_pin):
        self.threshold = 12000
        self.sensor = ADC(Pin(26))

    # This sensor has a range somewhere between 1200-14000
    def is_too_dark(self):
        return True if self.sensor.value > self.threshold else False


# internal rp2040 temperature sensor (reportedly not that accurate)
class Temperature:
    def __init__(self):
        adcpin = 4
        self.sensor = ADC(adcpin)

    def read(self):
        adc_value = self.sensor.read_u16()
        volt = (3.3/65535)*adc_value
        temperature = 27 - (volt - 0.706)/0.001721
        return round(temperature, 1)
