#!/usr/bin/python

# Inspired by code found at http://wannabe.guru.org/scott/hobbies/temperature/

import os
import sched
import time
import serial
import pidloop
import rrdtool

dmxdev = serial.Serial("/dev/serial/by-id/usb-DMXking.com_DMX_USB_PRO_6A0SVM7J-if00-port0", 57600);

loop_hidenear = pidloop.PIDThresh(128,26,28,0,31,33,-128)
loop_hidenear.setPoint(30)
loop_hidenear.setHardMax(128)
loop_hidenear.setHardMin(-128)
loop_hidenear.setKP(60.0)
loop_hidenear.setKI(0.004)
loop_hidenear.setKD(1000.0,0.95) 
loop_hidenear.sum_error = -3000.0 # XXX Initialize offset point a bit

def with_ow_temp_fk_id(devfn, loop, s, *arg, **kwarg):
    print("WARNING: failed to read %s" % devfn)
    return s # an ugly default

def with_ow_temp(devfn, sk, fk, *arg, **kwarg):
    with open(devfn) as devf:
        devstr = devf.read()
        devlines = devstr.split("\n")
        if devlines[0].find("YES") > 0:
            return sk(devfn,float((devlines[1].split(" ")[9])[2:]) / 1000, *arg, **kwarg)
    return fk(devfn, *arg, **kwarg)

def check_temps(sc):
    sc.enter(10, 1, check_temps, (sc,))

    def check(devfn, temp, loop, s, offset, rrd):
        desire = 128.0 + loop.update(temp, time.time())

        if desire < 0 :
            desire = 0
            loop.output = 0
        elif desire > 255 :
            desire = 255
            loop.output = 255

        rrdtool.update(rrd, "N:" + ("%f" % desire))

        return s[:offset] + chr(int(desire+0.5)) + s[offset+1:]

    # DMX conttrol string; initialize to all channels full off
    # 7E -- header
    # 06 -- type
    # 03 00 -- payload length
    # 00 -- channel 0 value (ignored by hardware)
    # 00 -- channel 1 value
    # 00 -- channel 2 value
    # E7 -- footer
    s = "\x7E\x06\x03\x00\x00\x00\x00\xE7"

    # Drive loop
    s = with_ow_temp("/sys/bus/w1/devices/28-011620f10dee/w1_slave",
            check, with_ow_temp_fk_id, loop_hidenear, s, 5, "/home/pi/sc/data/hide-near-dmx.rrd")

    print ("check temps fini: out=%r lhn=(%s)" % (s, loop_hidenear))
    assert(dmxdev.write(s) == 8)

itime = time.time()
s = sched.scheduler(time.time, time.sleep)
s.enterabs(itime, 1, check_temps, (s,))

print("Monitor starting...")
s.run()
