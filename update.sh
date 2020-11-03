#!/bin/bash

# Kill running script
ps -ef | grep "scorecard.py" | awk '{print $2}' | xargs sudo kill

# Re-pull repo
git pull origin master

# Start running script again
python3 scorecard.py

