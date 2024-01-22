from machine import Pin, ADC

class LightSensor:
    """
    Photoresistor that returns lower number in darkness.
    A threshold of ~10,000 seems to be the level of night-time.
    Wiring requires 3.3v into photoresistor. The other side of photoresistor
    should split, with one wire to 10k ohm resistor going to ground, and another to an analog pin (for example A0 — number 26 on some boards)
    """
    def __init__(self, sensor_pin):
        self.sensor = ADC(Pin(26))
        self.threshold = 10_000
        self.ref_voltage = 3.3

    def read(self):
        return self.sensor.read_u16()

    def voltage(self):
        return self.read() / (65535 * self.ref_voltage)

    def over_minimum(self):
        reading = self.read()
        return True if reading > self.threshold else False


class Temperature:
    """
    Internal rp2040 temperature sensor (reportedly not that accurate)
    """
    def __init__(self):
        adcpin = 4
        self.sensor = ADC(adcpin)

    def read(self):
        adc_value = self.sensor.read_u16()
        volt = (3.3/65535)*adc_value
        temperature = 27 - (volt - 0.706)/0.001721
        return round(temperature, 1)


# === CIRCUITPYTHON ===
#
# class LightSensor:
#     """
#     Light Sensor that returns higher number in darkness.
#     Around 1000+ is the level of night-time.
#     """
#     def __init__(self, sensor_pin):
#         self.threshold = 1000
#         self.sensor = analogio.AnalogIn(sensor_pin)
#
#     def get_voltage():
#         adc.value / 65535 * adc.reference_voltage
#
#     # This sensor has a range somewhere between 100-1300
#     def is_too_dark(self):
#         return True if self.sensor.value > self.threshold else False
