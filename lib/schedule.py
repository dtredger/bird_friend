import json
import time

from phew import logging
# phew logging automatically truncates file size at:
#   _log_truncate_at = 11 * 1024
# Logging causes audio issues, so disabled when amplifier is active

class Schedule():
    """
    Reads settings from a file (currently hardcoded to data.json). This
    file can be written by the access-point.

    The #run method takes an `action` argument, which expects a function,
    and runs it whenver run is called while the current time is within the
    set schedule window.
    """

    def __init__(self, file='data.json'):
        self.load_data(file)

    def load_data(self, data_file):
        try:
            data = open(data_file)
            json_data = json.loads(data.read())
            self.earliest = json_data.get("earliest", "23:59")
            self.latest = json_data.get("latest", "23:59")
            self.interval = json_data.get("interval", "60")
        except Exception as e:
            logging.info(f"load_data error {e}")

    # return 'earliest' or 'latest' [hr, min]
    def get_hour_minute(self, key):
        try:
            time_arr = getattr(self, key).split(":")
            hour = int(time_arr[0])
            min = int(time_arr[1])
            return [hour, min]
        except Exception as e:
            logging.info(f"get_hour_minute error {e}")
            return [24, 59]

    # return int for current hour and minute
    def get_current_hour_minute(self):
        hour_now = time.localtime()[3]
        min_now = time.localtime()[4]
        return [hour_now, min_now]

    def time_after_earliest(self):
        hour_set, min_set = self.get_hour_minute('earliest')
        hour_now, min_now = self.get_current_hour_minute()
        if hour_now > hour_set:
            return True
        elif hour_now == hour_set and min_now >= min_set:
            return True
        else:
            return False

    def time_before_latest(self):
        hour_set, min_set = self.get_hour_minute('latest')
        hour_now, min_now = self.get_current_hour_minute()
        if hour_now < hour_set:
            return True
        elif hour_now == hour_set and min_now < min_set:
            return True
        else:
            return False

    def run(self, action):
        if (self.time_after_earliest() and self.time_before_latest()):
            # logging.info('within time window')
            action()
        # elif self.time_after_earliest() == False:
        #     logging.info('time_after_earliest == FALSE')
        # elif self.time_before_latest() == False:
        #     logging.info('time_before_latest == FALSE')
        # else:
        #     logging.info('some other error')
