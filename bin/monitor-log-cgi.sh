#!/bin/zsh

echo "Content-Type: text/plain"
echo
cat /run/snakecontrol/remind.out
echo
echo "---"
echo
exec tail -n 40 /run/snakecontrol/monitor.log/current
