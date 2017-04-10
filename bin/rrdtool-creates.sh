#!/bin/zsh

RRDS=(
 heater-temp
 hide-near-temp
 hide-far-temp
 tank-near-temp
 tank-far-temp
)

ARGS=(
 --no-overwrite
 --step 60
 DS:temp:GAUGE:900:-10:50
 RRA:AVERAGE:0.5:1:525600
 RRA:AVERAGE:0.25:60:87600
 RRA:MIN:0.025:60:87600
 RRA:MAX:0.025:60:87600
)

for rrd in ${=RRDS[@]}; do
  rrdtool create /home/pi/sc/data/${rrd}.rrd ${=ARGS[@]}
done

RRDS=(
  hide-near-dmx
)

ARGS=(
 --no-overwrite
 --step 10
 DS:dmx:GAUGE:900:0:255
 RRA:AVERAGE:0.5:6:525600
 RRA:AVERAGE:0.25:360:87600
 RRA:MIN:0.025:360:87600
 RRA:MAX:0.025:360:87600
)

for rrd in ${=RRDS[@]}; do
  rrdtool create /home/pi/sc/data/${rrd}.rrd ${=ARGS[@]}
done
