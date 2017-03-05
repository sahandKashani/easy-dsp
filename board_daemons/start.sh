#!/bin/bash

./stop.sh > /dev/null

log_file=logs.txt
echo > "${log_file}"

echo -n 'Starting daemons '
nohup ./browser-main-daemon >> "${log_file}" 2>&1 &
sleep 4; echo -n '.'
nohup ./browser-wsaudio     >> "${log_file}" 2>&1 &
sleep 1; echo -n '.'
nohup ./browser-wsconfig    >> "${log_file}" 2>&1 &
sleep 1; echo -n '.'
echo " done"
