#!/bin/bash

cd /code
SLEEP_TIME=10

while true; do
    gunicorn -k tornado -w 2 -b 0.0.0.0:1999 main:app --max-requests 10000 --timeout 7200
    echo Error, sleep $SLEEP_TIME seconds
    sleep $SLEEP_TIME
done
