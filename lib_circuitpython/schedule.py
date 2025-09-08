import json
import time

class Schedule():
    """
    Reads settings from a file (currently hardcoded to data.json). This
    file can be written by a configuration interface.

    The run method takes an `action` argument, which expects a function,
    and runs it whenever run is called while the current time is within the
    set schedule window.
    
    Note: CircuitPython doesn't have built-in logging, so logging is simplified.
    """

    def __init__(self, file='data.json'):
        self.load_data(file)

    def load_data(self, data_file):
        """Load schedule data from JSON file"""
        try:
            with open(data_file, 'r') as data:
                json_data = json.loads(data.read())
                self.earliest = json_data.get("earliest", "07:00")
                self.latest = json_data.get("latest", "23:00")
                self.interval = json_data.get("interval", "60")
        except Exception as e:
            print(f"load_data error: {e}")
            # Set defaults if file doesn't exist or is corrupted
            self.earliest = "07:00"
            self.latest = "23:00"
            self.interval = "60"

    def get_hour_minute(self, key):
        """Return 'earliest' or 'latest' as [hr, min]"""
        try:
            time_str = getattr(self, key)
            time_arr = time_str.split(":")
            hour = int(time_arr[0])
            minute = int(time_arr[1])
            return [hour, minute]
        except Exception as e:
            print(f"get_hour_minute error: {e}")
            return [0, 0] if key == 'earliest' else [23, 59]

    def get_current_hour_minute(self):
        """Return int for current hour and minute"""
        # CircuitPython time.localtime() returns struct_time
        current_time = time.localtime()
        hour_now = current_time.tm_hour
        min_now = current_time.tm_min
        return [hour_now, min_now]

    def time_after_earliest(self):
        """Check if current time is after the earliest allowed time"""
        hour_set, min_set = self.get_hour_minute('earliest')
        hour_now, min_now = self.get_current_hour_minute()
        
        if hour_now > hour_set:
            return True
        elif hour_now == hour_set and min_now >= min_set:
            return True
        else:
            return False

    def time_before_latest(self):
        """Check if current time is before the latest allowed time"""
        hour_set, min_set = self.get_hour_minute('latest')
        hour_now, min_now = self.get_current_hour_minute()
        
        if hour_now < hour_set:
            return True
        elif hour_now == hour_set and min_now < min_set:
            return True
        else:
            return False

    def is_within_schedule(self):
        """Check if current time is within the scheduled window"""
        return self.time_after_earliest() and self.time_before_latest()

    def run(self, action):
        """
        Run the provided action if current time is within schedule window
        
        Args:
            action: Function to call if within schedule
        """
        if self.is_within_schedule():
            print('Running action - within time window')
            action()
        else:
            print('Outside time window - action skipped')

    def get_status(self):
        """Get current schedule status information"""
        current_time = self.get_current_hour_minute()
        return {
            'current_time': f"{current_time[0]:02d}:{current_time[1]:02d}",
            'earliest': self.earliest,
            'latest': self.latest,
            'interval': self.interval,
            'within_schedule': self.is_within_schedule(),
            'after_earliest': self.time_after_earliest(),
            'before_latest': self.time_before_latest()
        }

    def time_until_next_window(self):
        """Calculate minutes until next valid time window"""
        if self.is_within_schedule():
            return 0
        
        current_hour, current_min = self.get_current_hour_minute()
        earliest_hour, earliest_min = self.get_hour_minute('earliest')
        
        # Calculate current time and earliest time in minutes since midnight
        current_minutes = current_hour * 60 + current_min
        earliest_minutes = earliest_hour * 60 + earliest_min
        
        if current_minutes < earliest_minutes:
            # Same day
            return earliest_minutes - current_minutes
        else:
            # Next day
            return (24 * 60) - current_minutes + earliest_minutes

    def save_data(self, data_file='data.json'):
        """Save current schedule settings to file"""
        try:
            data = {
                'earliest': self.earliest,
                'latest': self.latest,
                'interval': self.interval
            }
            with open(data_file, 'w') as f:
                f.write(json.dumps(data))
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    def update_schedule(self, earliest=None, latest=None, interval=None):
        """Update schedule parameters"""
        if earliest is not None:
            self.earliest = earliest
        if latest is not None:
            self.latest = latest
        if interval is not None:
            self.interval = interval


# Helper functions
def create_default_schedule(filename='data.json'):
    """Create a default schedule file"""
    default_data = {
        'earliest': '07:00',
        'latest': '22:00', 
        'interval': '60'
    }
    
    try:
        with open(filename, 'w') as f:
            f.write(json.dumps(default_data))
        print(f"Created default schedule file: {filename}")
        return True
    except Exception as e:
        print(f"Error creating default schedule: {e}")
        return False

def test_schedule():
    """Test the schedule functionality"""
    schedule = Schedule()
    status = schedule.get_status()
    
    print("=== Schedule Test ===")
    print(f"Current time: {status['current_time']}")
    print(f"Schedule window: {status['earliest']} - {status['latest']}")
    print(f"Within schedule: {status['within_schedule']}")
    print(f"Minutes until next window: {schedule.time_until_next_window()}")
    
    return schedule