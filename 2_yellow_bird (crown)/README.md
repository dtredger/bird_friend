### Yellow Bird

These files are for a pi pico (without wifi) that activates once every hour.
Includes Outputs:
- LED eyes
- Servo neck
- Internal speaker (chirping)

On Boot:
- flash eyes 3 x
- glow and rotate:
  - glow eyes
  - rotate neck back/forth,
  - chirp bird sound

On Hour:
- glow and rotate


#### Updates v1.1

- reduce range of neck motion to look more realistic
    (range from  3500 <> 7200 rather than 2400<>7800)
    (reduction not equal because angle rotation seemed
    to be unequal before)