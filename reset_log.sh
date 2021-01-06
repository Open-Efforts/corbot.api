#!/bin/bash
LOG_DIR=/tmp
LOG_FILE_NAME=uwsgi

# copy log to dated file
cp $LOG_DIR/$LOG_FILE_NAME.log $LOG_DIR/$LOG_FILE_NAME-$(date +%Y-%m-%d-%H-%M).log
# reset cuurent log file
echo -n > $LOG_DIR/$LOG_FILE_NAME.log

# delete log files older than 30 days
find $LOG_DIR -name "*.log" -type f -mtime +14 -exec rm -f {} 2>/dev/null \;
