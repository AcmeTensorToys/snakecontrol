#!/usr/bin/python

# Inspired by code found at http://wannabe.guru.org/scott/hobbies/temperature/

import os
import rrdtool
import sched
import time

owdev_logname = {
    "/sys/bus/w1/devices/28-011620c718ee/w1_slave" : "/home/pi/sc/data/hide-far-temp.rrd",
    "/sys/bus/w1/devices/28-011620f10dee/w1_slave" : "/home/pi/sc/data/hide-near-temp.rrd",
    "/sys/bus/w1/devices/28-02161e26acee/w1_slave" : "/home/pi/sc/data/tank-far-temp.rrd",
    "/sys/bus/w1/devices/28-03164712aaff/w1_slave" : "/home/pi/sc/data/heater-temp.rrd",
    "/sys/bus/w1/devices/28-0416526de6ff/w1_slave" : "/home/pi/sc/data/tank-near-temp.rrd",
}

owdev_thresholds_heater1 = {
     "/sys/bus/w1/devices/28-011620c718ee/w1_slave" : (23.0, 25.0), # hide far
     "/sys/bus/w1/devices/28-02161e26acee/w1_slave" : (21.0, 25.0), # tank air far
     "/sys/bus/w1/devices/28-0416526de6ff/w1_slave" : (23.0, 27.0), # tank air near
}

# owdev_thresholds_heater2 = {
#     "/sys/bus/w1/devices/28-011620f10dee/w1_slave" : (29.0, 29.5), # hide near
# }

def nop (*arg, **kwarg):
    pass

def with_ow_temp_fk_id(devfn, x, *arg, **kwarg):
    print("WARNING: failed to read %s" % devfn)
    return x

def with_ow_temp(devfn, sk, fk, *arg, **kwarg):
    with open(devfn) as devf:
        devstr = devf.read()
        devlines = devstr.split("\n")
        if devlines[0].find("YES") > 0:
            return sk(devfn,float((devlines[1].split(" ")[9])[2:]) / 1000, *arg, **kwarg)
    return fk(devfn, *arg, **kwarg)


def check_temps(sc):
    print ("check temps init")
    def check(devfn, temp, threshs, desire):
        # Anything too hot: turn off the heater
        if (temp > threshs[devfn][1]): desire = "OFF"
        # No stated preference and something too cold, turn on the heater
        elif (temp <= threshs[devfn][0] and desire == None): desire = "ON"
        return desire

    did_interact = False
    desire = None
    for devfn in owdev_thresholds_heater1:
        desire = with_ow_temp(devfn, check, with_ow_temp_fk_id, owdev_thresholds_heater1, desire)
    if desire is not None:
        did_interact = True
        print("Set heater 1 %s" % desire)
        os.system("/home/pi/sc/bin/rpb.expect 4 %s | grep -A 5 -e 'Plug ' | tr -d '\015'" % desire)

    # desire = None
    # for devfn in owdev_thresholds_heater2:
    #     desire = with_ow_temp(devfn, check, with_ow_temp_fk_id, owdev_thresholds_heater2, desire)
    # if desire is not None:
    #     did_interact = True
    #     print("Set heater 2 %s" % desire)
    #     os.system("/home/pi/sc/bin/rpb.expect 5 %s | grep -A 5 -e 'Plug ' | tr -d '\015'" % desire)

    if not did_interact:
        os.system("/home/pi/sc/bin/rpb.expect | grep -A 5 -e 'Plug ' | tr -d '\015'")

    sc.enter(300, 1, check_temps, (sc,))
    print ("check temps fini")

def do_log_temp(devfn, temp):
    print("temp log: %s => %f" % (devfn, temp))
    rrdtool.update(owdev_logname[devfn], "N:" + ("%f" % temp))

def read_temps(sc,itime): 
    for devfn in owdev_logname: with_ow_temp(devfn, do_log_temp, nop)
    itime = itime + 60
    sc.enterabs(itime, 2, read_temps, (sc,itime))

itime = time.time()
s = sched.scheduler(time.time, time.sleep)
s.enterabs(itime, 1, check_temps, (s,))
s.enterabs(itime, 2, read_temps, (s,itime))

print("Monitor starting...")
s.run()
