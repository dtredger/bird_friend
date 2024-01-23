# The boot.py file is special - the code within it is executed when
# CircuitPython starts up, either from a hard reset or powering up the board.
# It is not run on soft reset, for example, if you reload the board from the
# serial console or the REPL. This is in contrast to the code within code.py,
# which is executed after CircuitPython is already running.
import board
import digitalio
import storage

try:
    storage.remount("/", readonly=True)
except RuntimeError as e:
    print(e)
    print("not making the FS writeable")
