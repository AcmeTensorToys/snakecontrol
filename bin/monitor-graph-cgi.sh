#!/bin/zsh

DATA_DIR=/home/pi/sc/data
OUTDIR=/home/pi/public_html/genimg

#DMX_SCALE=5
#DMX_SHIFT=20

TEMP_SCALE_UPPER=32
TEMP_SCALE_LOWER=19

# In index.html, add 97 to width and 73 to height.
COMMON_ARGS=(
	--end now
        --width=512 --height=320
        --lazy
)

DMX_ARGS=(
	--step=60 -v "DMX" --upper-limit 255 --lower-limit 0
	--right-axis-label "DMX" --right-axis 1:0
        DEF:dmxTN=${DATA_DIR}/tank-near-dmx.rrd:dmx:AVERAGE
        DEF:dmxHN=${DATA_DIR}/hide-near-dmx.rrd:dmx:AVERAGE
	LINE:dmxTN\#800000:"left side"
	LINE:dmxHN\#008000:"left hide"
)

NEAR_ARGS=(
        --step=60 -v "degrees C" --upper-limit ${TEMP_SCALE_UPPER} --lower-limit ${TEMP_SCALE_LOWER} --rigid
	--right-axis-label "degrees C" --right-axis 1:0
	# --right-axis-label "DMX"
	# --right-axis ${DMX_SCALE}:-${DMX_SHIFT}
        DEF:tempH=${DATA_DIR}/heater-temp.rrd:temp:AVERAGE
        DEF:tempHN=${DATA_DIR}/hide-near-temp.rrd:temp:AVERAGE
        DEF:tempTN=${DATA_DIR}/tank-near-temp.rrd:temp:AVERAGE
	# CDEF:scaled_dmxHN=dmxHN,${DMX_SHIFT},+,${DMX_SCALE},/
	# LINE:scaled_dmxHN\#000000:"dmx left"
        LINE2:tempH\#FF0000:"heater"
        LINE2:tempHN\#808000:"hide left"
        LINE2:tempTN\#00FF00:"tank left"
        HRULE:30#800000
)

HUMID_SCALE=$(( 100.0/(TEMP_SCALE_UPPER-TEMP_SCALE_LOWER) ))
HUMID_SHIFT=$(( TEMP_SCALE_LOWER * HUMID_SCALE ))

MID_ARGS=(
        --step=60 -v "degrees C" --upper-limit ${TEMP_SCALE_UPPER} --lower-limit ${TEMP_SCALE_LOWER} --rigid
	--right-axis-label "Humidity"
	--right-axis ${HUMID_SCALE}:-${HUMID_SHIFT}
	DEF:tempT=${DATA_DIR}/tank-top-temp.rrd:temp:AVERAGE
        DEF:temp=${DATA_DIR}/tank-mid-temp.rrd:temp:AVERAGE
        DEF:humid=${DATA_DIR}/tank-mid-humid.rrd:humid:AVERAGE
	CDEF:scaled_humid=humid,${HUMID_SHIFT},+,${HUMID_SCALE},/
	LINE2:scaled_humid\#0000FF:"humidity"
        LINE2:temp\#FF0000:"temp"
        LINE2:tempT\#808000:"top temp"
)

FAR_ARGS=(
        --step=60 -v "degrees C" --upper-limit ${TEMP_SCALE_UPPER} --lower-limit ${TEMP_SCALE_LOWER} --rigid
	--right-axis-label "degrees C" --right-axis 1:0
        DEF:tempHF=${DATA_DIR}/hide-far-temp.rrd:temp:AVERAGE
        DEF:tempTF=${DATA_DIR}/tank-far-temp.rrd:temp:AVERAGE
        LINE2:tempHF\#FF8000:"hide right"
        LINE2:tempTF\#00FFFF:"tank right"
)


OUTFILE="${QUERY_STRING}.png"
case "$QUERY_STRING" in
	dmx-4h)		PARAMS=(--start now-4h  --title "Melman Vivarium DMX Outputs 4h"	${DMX_ARGS[@]}) ;;
	dmx-24h)	PARAMS=(--start now-24h --title "Melman Vivarium DMX Outputs 24h"	${DMX_ARGS[@]}) ;;
	dmx-7d)		PARAMS=(--start now-7d  --title "Melman Vivarium DMX Outputs 7d"	${DMX_ARGS[@]}) ;;
	near-4h)	PARAMS=(--start now-4h  --title "Melman Vivarium Left Sensor Data 4h"	${NEAR_ARGS[@]}) ;;
	near-24h)	PARAMS=(--start now-24h --title "Melman Vivarium Left Sensor Data 24h"	${NEAR_ARGS[@]}) ;;
	near-7d)	PARAMS=(--start now-7d  --title "Melman Vivarium Left Sensor Data 7d"	${NEAR_ARGS[@]}) ;;
	mid-4h)		PARAMS=(--start now-4h  --title "Melman Vivarium Mid Sensor Data 4h"	${MID_ARGS[@]})  ;;
	mid-24h)	PARAMS=(--start now-24h --title "Melman Vivarium Mid Sensor Data 24h"	${MID_ARGS[@]})  ;;
	mid-7d)		PARAMS=(--start now-7d  --title "Melman Vivarium Mid Sensor Data 7d"	${MID_ARGS[@]})  ;;
	far-4h)		PARAMS=(--start now-4h  --title "Melman Vivarium Right Sensor Data 4h"	${FAR_ARGS[@]})  ;;
	far-24h)	PARAMS=(--start now-24h --title "Melman Vivarium Right Sensor Data 24h"	${FAR_ARGS[@]})  ;;
	far-7d)		PARAMS=(--start now-7d  --title "Melman Vivarium Right Sensor Data 7d"	${FAR_ARGS[@]})  ;;
	*)
		cat <<HERE
Content-Type: text/html
Status: 404 Not Found

<html><body>Invalid query parameter '${QUERY_STRING}'</body></html>
HERE
	exit 1
esac

CMD=(
  rrdtool graph ${OUTDIR}/${OUTFILE}
  ${PARAMS[@]}
  ${COMMON_ARGS[@]}
)

touch ${OUTDIR}/.rrdlock
flock --exclusive ${OUTDIR}/.rrdlock "${CMD[@]}" >&2

cat <<HERE
Location: /~pi/genimg/${OUTFILE}

HERE

