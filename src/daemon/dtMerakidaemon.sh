#!/bin/sh
DIR="$(dirname "$0")"
python3 $DIR/dtMerakiDaemon.py

# note : you can schedule the script to run every 15 minutes by 
# adding the following line in your crontab configuration
# with the command 'crontab -e' :
# */15 * * * * /usr/bin/python3 /opt/dynatrace/batch/dtmeraki/dtMerakiDaemon.py
