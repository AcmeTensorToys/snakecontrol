#!/usr/bin/python

# Inspired by code found at http://wannabe.guru.org/scott/hobbies/temperature/

import os
import sched
import time
import serial
import rrdtool

import pidloop
import BME280

dmxdev = serial.Serial("/dev/serial/by-id/usb-DMXking.com_DMX_USB_PRO_6A0SVM7J-if00-port0", 57600);

loop_hidenear = pidloop.PIDThresh(128,26,28,0,31,33,-128)
loop_hidenear.setPoint(30)
loop_hidenear.setHardMax(128)
loop_hidenear.setHardMin(-128)
loop_hidenear.setKP(60.0)
loop_hidenear.setKI(0.004)
loop_hidenear.setKD(1000.0,0.95) 
loop_hidenear.sum_error = 7600.0 # XXX Initialize offset point a bit

loop_tanknear = pidloop.PIDThresh(128,22,23,0,26,28,-128)
loop_tanknear.setPoint(25)
loop_tanknear.setHardMax(128)
loop_tanknear.setHardMin(-128)
loop_tanknear.setKP(60.0)   # XXX These are un-tuned
loop_tanknear.setKI(0.004)
loop_tanknear.setKD(1000.0,0.95)

bmemid = BME280.BME280(port=1, address=0x77)

def log(devfn, temp, logname, rrd, kw="temp"):
    try:
        rrdtool.update(rrd, "N:" + ("%f" % temp))
    except Exception, e :
            print("WARN: Cannot log %s: %s ." % (logname, e))
    print ("DATA: %s %s=%s" % (logname, kw, temp))

def logfail(devfn, name, *arg):
    print ("FAIL: %s ; %s ; %s ." % (name, devfn, arg))

def with_ow_temp_fk_id3(devfn, loop, err, s, *arg, **kwarg):
    print("WARNING: failed to read %s" % devfn)
    return s # an ugly default

def with_ow_temp(cache, devfn, sk, fk, *arg, **kwarg):
    if devfn in cache :
        return sk(devfn, cache[devfn], *arg, **kwarg)
    try:
        with open(devfn) as devf:
            devstr = devf.read()
            devlines = devstr.split("\n")
            if devlines[0].find("YES") > 0:
                val = float((devlines[1].split(" ")[9])[2:]) / 1000
                cache[devfn] = val
                return sk(devfn, val, *arg, **kwarg)
    except Exception as e:
            fk(devfn, e, *arg, **kwarg)
    return fk(devfn, None, *arg, **kwarg)

def checkpid(devfn, temp, loop, s, offset, rrd, logname):
    desire = 128.0 + loop.update(temp, time.time())

    if desire < 0 :
        desire = 0
        loop.output = 0
    elif desire > 255 :
        desire = 255
        loop.output = 255

    rrdtool.update(rrd, "N:" + ("%f" % desire))
    dmx = int(desire+0.5)
    print("DATA: %s dmx=%s" % (logname, dmx))

    return s[:offset] + chr(dmx) + s[offset+1:]

def check_temps(sc):
    sc.enter(10, 1, check_temps, (sc,))

    cache = {}

    # BME280 atop
    try:
      top = bmemid.get_data()
      log("bme280-77", top['t'], "tank-mid", "/home/pi/sc/data/tank-mid-temp.rrd")
      log("bme280-77", top['h'], "tank-mid", "/home/pi/sc/data/tank-mid-humid.rrd", kw="humid")
      log("bme280-77", top['p'], "tank-mid", "/home/pi/sc/data/tank-mid-press.rrd", kw="press")
    except Exception, e:
      logfail("bme280-77", "hide-mid", e)

    # Log (and populate cache, while we're at it)
    with_ow_temp(cache,
                 "/sys/bus/w1/devices/28-011620f10dee/w1_slave", log, logfail,
                 "hide-near", "/home/pi/sc/data/hide-near-temp.rrd")

    with_ow_temp(cache,
                 "/sys/bus/w1/devices/28-011620c718ee/w1_slave", log, logfail,
                 "hide-far", "/home/pi/sc/data/hide-far-temp.rrd")

    with_ow_temp(cache,
                 "/sys/bus/w1/devices/28-02161e26acee/w1_slave", log, logfail,
                 "tank-far", "/home/pi/sc/data/tank-far-temp.rrd")

    with_ow_temp(cache,
                 "/sys/bus/w1/devices/28-03164712aaff/w1_slave", log, logfail,
                 "heater-near", "/home/pi/sc/data/heater-temp.rrd")

    with_ow_temp(cache,
                 "/sys/bus/w1/devices/28-011620c805ee/w1_slave", log, logfail,
                 "tank-near", "/home/pi/sc/data/tank-near-temp.rrd")

    with_ow_temp(cache,
                 "/sys/bus/w1/devices/28-0416526de6ff/w1_slave", log, logfail,
                "tank-top", "/home/pi/sc/data/tank-top-temp.rrd")

    # DMX conttrol string; initialize to all channels full off
    # 7E -- header
    # 06 -- type
    # 03 00 -- payload length
    # 00 -- channel 0 value (ignored by hardware)
    # 00 -- channel 1 value
    # nn -- channel 2 value
    # nn -- channel 3 value
    # nn -- channel 4 value
    # E7 -- footer
    #    |hdr|typ|pay len|  0|  1|  2|  3|  4|ftr
    s = "\x7E\x06\x05\x00\x00\x00\x90\x00\x00\xE7"

    # Drive loop
    s = with_ow_temp(cache, "/sys/bus/w1/devices/28-011620f10dee/w1_slave",
            checkpid, with_ow_temp_fk_id3, loop_hidenear, s, 5, "/home/pi/sc/data/hide-near-dmx.rrd", "dmx-hidenear")

    s = with_ow_temp(cache, "/sys/bus/w1/devices/28-011620c805ee/w1_slave",
            checkpid, with_ow_temp_fk_id3, loop_tanknear, s, 6, "/home/pi/sc/data/tank-near-dmx.rrd", "dmx-tanknear")

    print ("check temps fini: out=%r lhn=(%s)" % (s, loop_hidenear))
    assert(dmxdev.write(s) == len(s))

itime = time.time()
s = sched.scheduler(time.time, time.sleep)
s.enterabs(itime, 1, check_temps, (s,))

print("Monitor starting...")
s.run()
