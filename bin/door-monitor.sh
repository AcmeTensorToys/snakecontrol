#!/usr/bin/zsh

set -e -u

I2C_ADDRESS="21"	# hex
GPIO_LEFT_OFFSET=6
GPIO_RIGHT_OFFSET=7

GPIO_IRQ=22

[ -d /sys/bus/i2c/devices/i2c-1/1-00${I2C_ADDRESS} ] || {
	echo pcf8574 0x${I2C_ADDRESS} > /sys/bus/i2c/devices/i2c-1/new_device
}

sleep 1
[ -d /sys/bus/i2c/devices/i2c-1/1-00${I2C_ADDRESS}/gpio ] || {
	echo "No GPIO chip registered.  Bailing out."
	exit 1
}

GPIOBASE=`cat /sys/bus/i2c/devices/i2c-1/1-00${I2C_ADDRESS}/gpio/gpiochip*/base`

GPIO_LEFT=$((GPIOBASE+GPIO_LEFT_OFFSET))

[ -d /sys/class/gpio/gpio${GPIO_LEFT} ] || {
	echo ${GPIO_LEFT} > /sys/class/gpio/export
}

GPIO_RIGHT=$((GPIOBASE+GPIO_RIGHT_OFFSET))

[ -d /sys/class/gpio/gpio${GPIO_RIGHT} ] || {
	echo ${GPIO_RIGHT} > /sys/class/gpio/export
}

# IRQ gpio
[ -d /sys/class/gpio/gpio${GPIO_IRQ} ] || {
	echo ${GPIO_IRQ} > /sys/class/gpio/export 
}
echo 1 > /sys/class/gpio/gpio${GPIO_IRQ}/active_low
echo rising > /sys/class/gpio/gpio${GPIO_IRQ}/edge

exec 3</sys/class/gpio/gpio${GPIO_IRQ}/value

/home/pi/sc/bin/pollfd 3 -1 | { while read i; do
	echo "DATA: door left=$(cat /sys/class/gpio/gpio${GPIO_LEFT}/value) right=$(cat /sys/class/gpio/gpio${GPIO_RIGHT}/value)"
done ; }
