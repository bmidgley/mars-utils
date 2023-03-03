#!/bin/bash
# for this to work, do this in advance
# sudo pip3 install meshtastic
ping -c 1 meshtastic.local && exit
ping -c 1 meshtastic.local && exit
exec 2>&1 >>/home/pi/cronlog
date
meshtastic --reboot
