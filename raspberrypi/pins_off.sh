#!/usr/bin/bash

WHITE=24
BLACK=23

echo "pulling pins to low..."

echo $WHITE > /sys/class/gpio/export
echo $BLACK > /sys/class/gpio/export

echo "out" > /sys/class/gpio/gpio$WHITE/direction
echo "out" > /sys/class/gpio/gpio$BLACK/direction

echo "0" > /sys/class/gpio/gpio$WHITE/value
echo "0" > /sys/class/gpio/gpio$BLACK/value

echo $WHITE > /sys/class/gpio/unexport
echo $BLACK > /sys/class/gpio/unexport
