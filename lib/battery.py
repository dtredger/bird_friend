from time import sleep
from machine import Pin, ADC

class Battery:
    """
    Battery management for PicoLipoSHIM.
    
    The PicoLipoSHIM provides:
    - Automatic charging when external power is connected
    - Automatic switching to battery when external power is removed
    - Battery voltage monitoring via ADC
    - Optional charging status detection
    
    Typical LiPo voltage ranges:
    - 4.2V: Fully charged
    - 3.7V: Nominal voltage  
    - 3.4V: Low battery warning
    - 3.0V: Critical/cutoff voltage
    
    Wiring:
    - VBAT pin to ADC-capable GPIO pin (e.g., pin 26, 27, 28, or 29)
    - Optional: CHRG pin to digital input for charging status
    """
    
    def __init__(self, battery_pin=29, charging_pin=None):
        """
        Initialize battery monitoring.
        
        Args:
            battery_pin (int): ADC pin connected to VBAT (default: 29)
            charging_pin (int): Optional digital pin connected to CHRG status
        """
        self.battery_adc = ADC(Pin(battery_pin))
        self.charging_pin = Pin(charging_pin, Pin.IN, Pin.PULL_UP) if charging_pin else None
        
        # Voltage thresholds for LiPo battery
        self.voltage_full = 4.1      # Consider full above this
        self.voltage_nominal = 3.7   # Nominal voltage
        self.voltage_low = 3.4       # Low battery warning
        self.voltage_critical = 3.0  # Critical - should shutdown soon
        
        # ADC reference voltage (usually 3.3V)
        self.ref_voltage = 3.3
        
        # Voltage divider ratio (PicoLipoSHIM typically uses 2:1 divider)
        # This means the actual battery voltage is 2x the ADC reading
        self.voltage_divider_ratio = 2.0

    def read_raw(self):
        """Read raw ADC value (0-65535)."""
        return self.battery_adc.read_u16()

    def read_voltage(self):
        """
        Read battery voltage.
        
        Returns:
            float: Battery voltage in volts
        """
        raw_reading = self.read_raw()
        # Convert ADC reading to voltage
        adc_voltage = (raw_reading / 65535) * self.ref_voltage
        # Account for voltage divider
        battery_voltage = adc_voltage * self.voltage_divider_ratio
        return round(battery_voltage, 2)

    def get_percentage(self):
        """
        Get battery percentage based on voltage.
        
        Returns:
            int: Battery percentage (0-100)
        """
        voltage = self.read_voltage()
        
        # Simple linear mapping from voltage to percentage
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
        Check if battery is currently charging.
        
        Returns:
            bool: True if charging, False if not charging, None if status unknown
        """
        if self.charging_pin is None:
            return None
        
        # CHRG pin is typically active low (pulled low when charging)
        return not self.charging_pin.value()

    def get_status(self):
        """
        Get comprehensive battery status.
        
        Returns:
            dict: Battery status information
        """
        voltage = self.read_voltage()
        percentage = self.get_percentage()
        charging = self.is_charging()
        
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
            "charging": charging,
            "raw_adc": self.read_raw()
        }

    def is_low_battery(self):
        """Check if battery is at low level."""
        return self.read_voltage() < self.voltage_low

    def is_critical_battery(self):
        """Check if battery is at critical level."""
        return self.read_voltage() < self.voltage_critical

    def log_status(self, log_name='battery_log.txt'):
        """
        Log current battery status to file.
        
        Args:
            log_name (str): Log file name
        """
        status = self.get_status()
        try:
            with open(log_name, 'a') as file:
                import time
                timestamp = time.time()
                log_line = f"{timestamp},{status['voltage']},{status['percentage']},{status['level']},{status['charging']}\n"
                file.write(log_line)
        except Exception as e:
            print(f"Error logging battery status: {e}")

    def wait_for_charge_level(self, target_percentage, check_interval=30):
        """
        Wait until battery reaches target charge level.
        
        Args:
            target_percentage (int): Target percentage to wait for
            check_interval (int): Seconds between checks
        """
        print(f"Waiting for battery to reach {target_percentage}%...")
        
        while True:
            current_percentage = self.get_percentage()
            charging = self.is_charging()
            
            print(f"Battery: {current_percentage}% (Charging: {charging})")
            
            if current_percentage >= target_percentage:
                print(f"Target {target_percentage}% reached!")
                break
                
            if not charging and current_percentage < target_percentage:
                print("Warning: Not charging and below target level")
                
            sleep(check_interval)

    def monitor_battery(self, callback=None, check_interval=60):
        """
        Continuously monitor battery and call callback on status changes.
        
        Args:
            callback: Function to call with status dict
            check_interval (int): Seconds between checks
        """
        last_level = None
        
        while True:
            status = self.get_status()
            current_level = status['level']
            
            # Call callback if provided
            if callback:
                callback(status)
            
            # Print status changes
            if current_level != last_level:
                print(f"Battery status changed: {current_level} ({status['percentage']}%)")
                last_level = current_level
            
            sleep(check_interval)


# Example usage functions
def battery_callback(status):
    """Example callback function for battery monitoring."""
    if status['level'] == 'critical':
        print("⚠️  CRITICAL BATTERY - Consider shutting down!")
    elif status['level'] == 'low':
        print("🔋 Low battery warning")
    elif status['charging'] and status['percentage'] == 100:
        print("🔋 Battery fully charged")


# Test function
def test_battery():
    """Test battery functionality."""
    battery = Battery(battery_pin=29, charging_pin=28)  # Adjust pins as needed
    
    print("=== Battery Test ===")
    status = battery.get_status()
    print(f"Voltage: {status['voltage']}V")
    print(f"Percentage: {status['percentage']}%")
    print(f"Level: {status['level']}")
    print(f"Charging: {status['charging']}")
    print(f"Raw ADC: {status['raw_adc']}")
    
    # Log status
    battery.log_status()
    
    return battery


if __name__ == "__main__":
    test_battery()