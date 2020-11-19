#!/bin/bash

# Kill running script
ps -ef | grep "scorecard.py" | awk '{print $2}' | xargs sudo kill

# Re-pull repo
cd /home/pi/Dev/scorecard || exit
git pull origin master

# Install dependencies
# TODO: Get pipenv working again?
sudo apt-get install libopenjp2-7
# pip3 install google-api-python-client
# pip3 install PyGithub
# pip3 install python-dotenv
# pip3 install Pillow

# Start running script again
python3 new.py