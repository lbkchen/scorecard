#!/bin/bash

# Kill running script
ps -ef | grep "scorecard.py" | awk '{print $2}' | xargs sudo kill

# Re-pull repo
cd /home/pi/Dev/scorecard || exit
git pull origin master
pipenv install

# Start running script again
pipenv run python new.py