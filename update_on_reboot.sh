#!/bin/bash

# Send IP info (sleep 30 to allow IP to be configured)
sleep 30
./ip.py

# Update
./update.sh