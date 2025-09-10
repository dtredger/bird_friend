import time
import analogio
import digitalio

class Battery:
    """
    Battery monitoring for Adafruit RP2040 Prop-Maker Feather.
    
    This board does NOT have built-in battery monitoring like other Feathers.
    You must add your own voltage divider circuit:
    
    Wiring:
    BAT pin → 100kΩ → [A3] → 100kΩ → GND
    
    The voltage divider makes the battery voltage safe to read (divides by 2).
    """
    
    def __init__(self, battery_pin, charging_pin=None):
        """
        Initialize battery monitoring for Prop-Maker Feather.
        
        Args:
            battery_pin: Analog pin connected to voltage divider (A0-A3)
            charging_pin: Not available on Prop-Maker Feather (set to None)
        """
        self.battery_adc = analogio.AnalogIn(battery_pin)
        self.charging_pin = None  # Not available on this board
        
        # Voltage thresholds for LiPo battery
        self.voltage_full = 4.1      
        self.voltage_nominal = 3.7   
        self.voltage_low = 3.4       
        self.voltage_critical = 3.0  
        
        # ADC reference voltage
        self.ref_voltage = 3.3
        
        # Voltage divider ratio (2 x 100kΩ resistors = 2:1 divider)
        self.voltage_divider_ratio = 2.0

    def read_raw(self):
        """Read raw ADC value (0-65535)"""
        return self.battery_adc.value

    def read_voltage(self):
        """
        Read battery voltage accounting for voltage divider.
        
        Returns:
            float: Battery voltage in volts
        """
        raw_reading = self.read_raw()
        # Convert ADC reading to voltage at the pin
        adc_voltage = (raw_reading / 65535) * self.ref_voltage
        # Account for voltage divider (multiply by 2)
        battery_voltage = adc_voltage * self.voltage_divider_ratio
        return round(battery_voltage, 2)

    def get_percentage(self):
        """
        Get battery percentage based on voltage.
        
        Returns:
            int: Battery percentage (0-100)
        """
        voltage = self.read_voltage()
        
        if voltage >= self.voltage_full:
            return 100
        elif voltage <= self.voltage_critical:
            return 0
        else:
            # Linear interpolation between critical and full
            voltage_range = self.voltage_full - self.voltage_critical
            voltage_above_critical = voltage - self.voltage_critical
            percentage = (voltage_above_critical / voltage_range) * 100
            return max(0, min(100, int(percentage)))

    def is_charging(self):
        """
        Check if battery is charging.
        
        Returns:
            None: Charging status not available on Prop-Maker Feather
        """
        # Charging status is not available on this board
        return None

    def get_status(self):
        """Get comprehensive battery status"""
        voltage = self.read_voltage()
        percentage = self.get_percentage()
        
        # Determine status level
        if voltage >= self.voltage_full:
            level = "full"
        elif voltage >= self.voltage_nominal:
            level = "good"
        elif voltage >= self.voltage_low:
            level = "low"
        else:
            level = "critical"
        
        return {
            "voltage": voltage,
            "percentage": percentage,
            "level": level,
            "charging": None,  # Not available on this board
            "raw_adc": self.read_raw()
        }

    def is_low_battery(self):
        """Check if battery is at low level"""
        return self.read_voltage() < self.voltage_low

    def is_critical_battery(self):
        """Check if battery is at critical level"""
        return self.read_voltage() < self.voltage_critical

    def log_status(self, log_name='battery_log.txt'):
        """Log current battery status to file"""
        status = self.get_status()
        try:
            with open(log_name, 'a') as file:
                timestamp = int(time.monotonic())
                log_line = f"{timestamp},{status['voltage']},{status['percentage']},{status['level']}\n"
                file.write(log_line)
        except Exception as e:
            print(f"Error logging battery status: {e}")

    def deinit(self):
        """Clean up resources"""
        self.battery_adc.deinit()


def test_battery():
    """Test battery monitoring"""
    import board
    
    print("=== Prop-Maker Feather Battery Test ===")
    print("Note: Requires voltage divider circuit on A3")
    
    try:
        battery = Battery(board.A3)
        status = battery.get_status()
        
        print(f"Raw ADC: {status['raw_adc']}")
        print(f"Voltage: {status['voltage']}V") 
        print(f"Percentage: {status['percentage']}%")
        print(f"Level: {status['level']}")
        print(f"Charging: {status['charging']} (not available on this board)")
        
        # Log status
        battery.log_status()
        
        return battery
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have the voltage divider circuit connected!")
        return None


if __name__ == "__main__":
    test_battery()