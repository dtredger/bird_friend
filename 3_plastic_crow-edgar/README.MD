# CROW Friend ('edgar') for Pico W
#### v1 Jan 2024
#### v2 Mar 2024
The original version of this bird used its own unique code (including at least one
breaking bug). This update replaces that old code with the shared code in /lib,
which has been used in #5 Owl and #6 Baby Crow.

## Board & Hardware
This board is a Raspberry Pi Pico W, which includes wifi. A max98357A amplifier
has been added, to get more sound from the 8ohm 0.5W speaker.
Because it is possible to set a time manually for this bird, it does not have a
light sensor.

## Modules
The code for creating a hotspot has been moved to the shared /lib directory,
although this bird is currently the only one that uses it. On startup, this bird
creates an access point to set up with these default details:
```
  DOMAIN = "🐦.friend"
  DEFAULT_HOSTNAME = "🐦"
  DEFAULT_PASSWORD = "birdfriend"
```
Creating the access-point relies on the 'phew' library (thonny can install),
currently on v0.3

## Actions
On Boot, this bird does the following:
- starts access-point (with the details above)
- Runs default animations
- Starts a timer that will animate on the hour
