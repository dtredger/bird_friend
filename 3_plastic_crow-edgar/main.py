from machine import Timer

from src.wifi import *
from src.bird_actions import *

# phew logging automatically truncates file size at
# _log_truncate_at = 11 * 1024


# -****- ON BOOT -****-
flash_eyes(times=3)

# === Minute Timer === #
global main_timer
main_timer = Timer(-1)
interval = 60000 # every 60 seconds
main_timer.init(period=interval, mode=Timer.PERIODIC, callback=lambda t:run_bird_schedule())

# AP times out after 15 minutes
# Can also be deactivated by user in UI
global ap_timer
ap_timer = Timer(-1)
ap_timeout = 60000 * 15 # 15 minutes
ap_timer.init(period=ap_timeout, mode=Timer.ONE_SHOT, callback=lambda t:stop_access_point())

# Start Wireless Access Point
start_access_point()
