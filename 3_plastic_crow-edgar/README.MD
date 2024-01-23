### CROW Friend (v4) for Pico W

Creates an access point to set up with these default details:
```
  DOMAIN = "🐦.friend"
  DEFAULT_HOSTNAME = "🐦"
  DEFAULT_PASSWORD = "birdfriend"
```
- Relies on the 'phew' library (thonny can install) for access-point
  - currently v0.3
- Uses (chunk, myDMA, myPWM, wave, and wavePlayer) for sounds

  ### Yellow Bird
  These files are for a pi pico with controllable activation time.
  Includes Outputs:
  - WIFI to create access-point (or connect to network)
  - LED eyes
  - Servo neck
  - Internal speaker (chirping)

  On Boot:
  - flash eyes 3 x
  - start Access Point
