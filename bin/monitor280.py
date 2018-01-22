#!/usr/bin/python

import sched
import time
import rrdtool
import BME280

bmemid = BME280.BME280(port=1, address=0x77)

def log(devfn, temp, logname, rrd, kw="temp"):
    try:
        rrdtool.update(rrd, "N:" + ("%f" % temp))
    except Exception, e :
            print("WARN: Cannot log %s: %s ." % (logname, e))
    print ("DATA: %s %s=%s" % (logname, kw, temp))

def logfail(devfn, name, *arg):
    print ("FAIL: %s ; %s ; %s ." % (name, devfn, arg))

def poller(sc):
    global bmemid
    sc.enter(10, 1, poller, (sc,))

    # BME280 in middle of tank
    try:
      top = bmemid.get_data()
      log("bme280-77", top['t'], "tank-mid", "/home/pi/sc/data/tank-mid-temp.rrd")
      log("bme280-77", top['h'], "tank-mid", "/home/pi/sc/data/tank-mid-humid.rrd", kw="humid")
      log("bme280-77", top['p'], "tank-mid", "/home/pi/sc/data/tank-mid-press.rrd", kw="press")
    except Exception, e:
      logfail("bme280-77", "tank-mid", e)
      bmemid = BME280.BME280(port=1, address=0x77)

itime = time.time()
s = sched.scheduler(time.time, time.sleep)
s.enterabs(itime, 1, poller, (s,))

print("Monitor starting...")
s.run()
