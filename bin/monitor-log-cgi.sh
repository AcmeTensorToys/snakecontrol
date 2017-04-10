#!/bin/zsh

echo "Content-Type: text/plain"
echo
exec tail -n 40 /home/pi/sc/data/monitor.log/current
