import analogio
import microcontroller
import time

class LightSensor:
    """
    Photoresistor light sensor with noise reduction and averaging.
    
    With 1kΩ resistor: ~5,000-15,000 = darkness, ~30,000-50,000 = light
    With 10kΩ resistor: Higher values = more light
    With 100kΩ resistor: 0 = darkness, 500-1800 = light
    
    3.3V ── Photoresistor ── [Junction] ── A1 (analog pin)
                                │
                            10kΩ resistor
                                │
                               GND
    
    The class automatically averages multiple readings to reduce noise
    and caches recent values to prevent reading ADC too frequently.
    """
    def __init__(self, sensor_pin, num_samples=5, sample_delay=0.01):
        self.sensor = analogio.AnalogIn(sensor_pin)
        self.threshold = 25000  # Default for 1kΩ resistor - adjust in config
        self.ref_voltage = 3.3
        self.num_samples = num_samples  # Number of readings to average
        self.sample_delay = sample_delay  # Delay between readings
        self._last_reading = None
        self._last_reading_time = 0

    def read_raw(self):
        """Read single raw sensor value (0-65535) - can be noisy"""
        return self.sensor.value

    def read(self):
        """Read averaged sensor value to reduce noise"""
        # If we read too recently, return cached value to prevent noise
        current_time = time.monotonic()
        if (self._last_reading is not None and 
            current_time - self._last_reading_time < 0.1):
            return self._last_reading
        
        # Take multiple readings and average them
        total = 0
        for _ in range(self.num_samples):
            total += self.sensor.value
            if self.sample_delay > 0:
                time.sleep(self.sample_delay)
        
        averaged = total // self.num_samples
        
        # Cache the result
        self._last_reading = averaged
        self._last_reading_time = current_time
        
        return averaged

    def read_stable(self, stability_samples=3, max_attempts=10):
        """
        Read sensor value and wait for it to stabilize.
        Returns reading when consecutive readings are similar.
        """
        readings = []
        
        for attempt in range(max_attempts):
            reading = self.read()
            readings.append(reading)
            
            if len(readings) >= stability_samples:
                # Check if recent readings are stable (within 10% of each other)
                recent = readings[-stability_samples:]
                avg = sum(recent) // len(recent)
                
                # Check if all recent readings are within 10% of average
                stable = all(abs(r - avg) <= avg * 0.1 for r in recent)
                
                if stable:
                    return avg
                    
            time.sleep(0.05)  # Small delay between attempts
        
        # If we can't get stable reading, return the average of what we have
        return sum(readings) // len(readings) if readings else 0

    def calibrate_threshold(self, light_samples=10, dark_samples=10):
        """
        Helper method to calibrate threshold.
        Call this method in bright light, then in darkness to set threshold.
        """
        print("=== Light Sensor Calibration ===")
        print("Place sensor in BRIGHT LIGHT and press Enter...")
        input()
        
        print("Taking light readings...")
        light_readings = []
        for i in range(light_samples):
            reading = self.read()
            light_readings.append(reading)
            print(f"Light reading {i+1}: {reading}")
            time.sleep(0.5)
        
        light_avg = sum(light_readings) // len(light_readings)
        print(f"Average light reading: {light_avg}")
        
        print("\nPlace sensor in DARKNESS and press Enter...")
        input()
        
        print("Taking dark readings...")
        dark_readings = []
        for i in range(dark_samples):
            reading = self.read()
            dark_readings.append(reading)
            print(f"Dark reading {i+1}: {reading}")
            time.sleep(0.5)
            
        dark_avg = sum(dark_readings) // len(dark_readings)
        print(f"Average dark reading: {dark_avg}")
        
        # Set threshold halfway between dark and light
        suggested_threshold = (dark_avg + light_avg) // 2
        print(f"\nSuggested threshold: {suggested_threshold}")
        print(f"Add this to your config.json:")
        print(f'"sensors": {{ "light_threshold": {suggested_threshold} }}')
        
        return suggested_threshold

    def voltage(self):
        """Get voltage reading from sensor"""
        return (self.read() / 65535) * self.ref_voltage

    def over_minimum(self):
        """Check if light level is above minimum threshold"""
        reading = self.read()
        return reading > self.threshold  # Higher values = more light with your resistor

    def is_too_dark(self):
        """Check if it's too dark (opposite of over_minimum)"""
        return not self.over_minimum()

    def log_reading(self, log_name='sensor_log.txt'):
        """Log current sensor reading to file"""
        try:
            with open(log_name, 'a') as file:
                reading = self.read()
                timestamp = time.monotonic()
                file.write(f"{timestamp},{reading}\n")
        except Exception as e:
            print(f"Error logging sensor reading: {e}")

    def deinit(self):
        """Clean up sensor resources"""
        self.sensor.deinit()


class Temperature:
    """
    Internal temperature sensor for CircuitPython
    """
    def __init__(self):
        # CircuitPython provides built-in temperature sensor
        pass

    def read(self):
        """Read temperature in Celsius"""
        return microcontroller.cpu.temperature

    def read_fahrenheit(self):
        """Read temperature in Fahrenheit"""
        celsius = self.read()
        return (celsius * 9/5) + 32


def write_lightlevel(sensor, log_name='light_log.txt'):
    """
    Standalone function to write light level with timestamp
    """
    try:
        with open(log_name, 'a') as f:
            timestamp = str(time.monotonic())
            light_reading = str(sensor.read())
            f.write(f"{timestamp} {light_reading}\n")
        return light_reading
    except Exception as e:
        print(f"Error writing light level: {e}")
        return None