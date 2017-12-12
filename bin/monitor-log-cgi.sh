#!/bin/zsh

echo "Content-Type: text/plain"
echo
cat /run/snakecontrol/remind.out
echo "---"
tail -n 1 /run/snakecontrol/door-monitor.log/current
echo "---"
exec tail -n 40 /run/snakecontrol/monitor.log/current
