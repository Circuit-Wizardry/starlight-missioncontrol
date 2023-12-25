# STARLIGHT MissionControl
This repository contains the source code loaded onto the STARLIGHT flight computer in order to allow it to work with MissionControl.

This board uses the following repository for sensor fusion: https://github.com/micropython-IMU/micropython-fusion

# Installation
Find the latest version of the STARLIGHT MissionControl UF2 at https://github.com/Circuit-Wizardry/starlight-missioncontrol/releases.

Hold down the "BOOTSEL" button on your flight computer and plug it into USB. After a few seconds, you should notice it register as a mass storage device. Drag the UF2 into this storage device, and allow the board to reboot.

It's that simple! Then, you can launch MissionControl and connect to the board.
