#!/usr/bin/python

# Inspired by code found at http://wannabe.guru.org/scott/hobbies/temperature/

import ConfigParser
import sched
import time
import serial
import rrdtool

import pidloop

statefilename = "/home/pi/sc/data/pidmonitor.state"

dmxdev = serial.Serial("/dev/serial/by-id/usb-DMXking.com_DMX_USB_PRO_6A0SVM7J-if00-port0", 57600);

loop_hidenear = pidloop.PIDThresh(128,26,28,0,31,33,-128)
loop_hidenear.setPoint(30)
loop_hidenear.setHardMax(128)
loop_hidenear.setHardMin(-128)
loop_hidenear.setKP(60.0)
loop_hidenear.setKI(0.004)
loop_hidenear.setKD(1000.0,0.95)

loop_tanknear = pidloop.PIDThresh(128,22,23,0,26,28,-128)
loop_tanknear.setPoint(25)
loop_tanknear.setHardMax(128)
loop_tanknear.setHardMin(-128)
loop_tanknear.setKP(60.0)   # XXX These are un-tuned
loop_tanknear.setKI(0.004)
loop_tanknear.setKD(1000.0,0.95)

loop_hidefar = pidloop.PIDThresh(128,19,21,0,24,25,-128)
loop_hidefar.setPoint(23)
loop_hidefar.setHardMax(128)
loop_hidefar.setHardMin(-128)
loop_hidefar.setKP(60.0)   # XXX These are un-tuned
loop_hidefar.setKI(0.004)
loop_hidefar.setKD(1000.0,0.95)

try:
    config = ConfigParser.ConfigParser()
    config.read(statefilename)

    try:
        loop_hidenear.sum_error = config.getfloat("loop_hidenear", "sum_error")
    except Exception as e:
        pass

    try:
        loop_tanknear.sum_error = config.getfloat("loop_tanknear", "sum_error")
    except Exception as e:
        pass

    try:
        loop_hidefar.sum_error  = config.getfloat("loop_hidefar",  "sum_error")
    except Exception as e:
        pass
except Exception as e:
    pass

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
                 "/sys/bus/w1/devices/28-041652ea8bff/w1_slave", log, logfail,
                 "heater-near", "/home/pi/sc/data/heater-temp.rrd")

    with_ow_temp(cache,
                 "/sys/bus/w1/devices/28-0416526de6ff/w1_slave", log, logfail,
                 "tank-near", "/home/pi/sc/data/tank-near-temp.rrd")

    with_ow_temp(cache,
                 "/sys/bus/w1/devices/28-0316479295ff/w1_slave", log, logfail,
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
    s = "\x7E\x06\x05\x00\x00\x00\x00\x00\x00\xE7"

    # Drive loop
    s = with_ow_temp(cache, "/sys/bus/w1/devices/28-011620f10dee/w1_slave",
            checkpid, with_ow_temp_fk_id3, loop_hidenear, s, 5, "/home/pi/sc/data/hide-near-dmx.rrd", "dmx-hidenear")

    s = with_ow_temp(cache, "/sys/bus/w1/devices/28-0416526de6ff/w1_slave",
            checkpid, with_ow_temp_fk_id3, loop_tanknear, s, 6, "/home/pi/sc/data/tank-near-dmx.rrd", "dmx-tanknear")

    s = with_ow_temp(cache, "/sys/bus/w1/devices/28-011620c718ee/w1_slave",
            checkpid, with_ow_temp_fk_id3, loop_hidefar, s, 7, "/home/pi/sc/data/hide-far-dmx.rrd", "dmx-hidefar")

    assert(dmxdev.write(s) == len(s))

    print ("check temps fini: out=%r" % s)
    print ("PID: lhn=(%s)" % loop_hidenear)
    print ("PID: ltn=(%s)" % loop_tanknear)
    print ("PID: lhf=(%s)" % loop_hidefar)


def save_state(sc):
    sc.enter(600, 2, save_state, (sc,))

    config = ConfigParser.ConfigParser()
    config.add_section("loop_tanknear")
    config.set("loop_tanknear", "sum_error", loop_tanknear.sum_error)
    config.add_section("loop_hidenear")
    config.set("loop_hidenear", "sum_error", loop_hidenear.sum_error)
    config.add_section("loop_hidefar")
    config.set("loop_hidefar", "sum_error" , loop_hidefar.sum_error )

    with open(statefilename, 'w') as statefile:
        config.write(statefile)

itime = time.time()
s = sched.scheduler(time.time, time.sleep)
s.enterabs(itime, 1, check_temps, (s,))

s.enter(600, 2, save_state, (s,))

print("Monitor starting...")
s.run()
