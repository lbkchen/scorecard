#!/bin/bash

# Send IP info (sleep 30 to allow IP to be configured)
sleep 30

cd /home/pi/Dev/scorecard || exit
git pull origin master
./ip.py

# Update
./update.sh