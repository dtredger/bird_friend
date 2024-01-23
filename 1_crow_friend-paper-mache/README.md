# Crow Friend

crow_friend is a raspberry-pi based animatronic bird, consisting of:
- beak servo for opening/closing beak
- neck servo for rotating head
- speaker attached to headphone jack for audio out

#### Start

Unlike subsequent versions, crow_friend uses a full-size raspberry pi (running the Raspbian distro DietPi). This means it will not automatically execute anything on boot.
The `crow_friend.service` should be installed to have the Friend start on boot.
`systemctl link 1_crow_friend\ \(paper\ mache\)/crow_friend.service`

Audio (and SCP) must also be enabled in the `dietpi-config`

Start/enable the pigpiod service to reduce servo jitter: `systemctl enable pigpiod`
