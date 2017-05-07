#!/bin/zsh

echo "Content-Type: text/plain"
echo
exec tail -n 40 /run/snakecontrol/monitor.log/current
