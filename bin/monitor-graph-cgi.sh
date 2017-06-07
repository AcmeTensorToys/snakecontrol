#!/bin/zsh

DMX_SCALE=5
DMX_SHIFT=20

TEMP_SCALE_UPPER=32
TEMP_SCALE_LOWER=19

COMMON_ARGS=(
	--end now
        --width=960 --height=480
        --lazy
)

TEMP_ARGS=(
        --step=60 -v "degrees C" --upper-limit ${TEMP_SCALE_UPPER} --lower-limit ${TEMP_SCALE_LOWER} --rigid
	--right-axis-label "DMX"
	--right-axis ${DMX_SCALE}:-${DMX_SHIFT}
        DEF:tempH=/home/pi/sc/data/heater-temp.rrd:temp:AVERAGE
        DEF:tempHN=/home/pi/sc/data/hide-near-temp.rrd:temp:AVERAGE
        DEF:dmxHN=/home/pi/sc/data/hide-near-dmx.rrd:dmx:AVERAGE
        DEF:tempHF=/home/pi/sc/data/hide-far-temp.rrd:temp:AVERAGE
        DEF:tempTN=/home/pi/sc/data/tank-near-temp.rrd:temp:AVERAGE
        DEF:tempTF=/home/pi/sc/data/tank-far-temp.rrd:temp:AVERAGE
	CDEF:scaled_dmxHN=dmxHN,${DMX_SHIFT},+,${DMX_SCALE},/
	LINE:scaled_dmxHN\#000000:"dmx left"
        LINE2:tempH\#FF0000:"heater"
        LINE2:tempHN\#808000:"hide left"
        LINE2:tempHF\#FF8000:"hide right"
        LINE2:tempTN\#00FF00:"tank left"
        LINE2:tempTF\#00FFFF:"tank right"
        HRULE:30#800000
)

HUMID_SCALE=$(( 100.0/(TEMP_SCALE_UPPER-TEMP_SCALE_LOWER) ))
HUMID_SHIFT=$(( TEMP_SCALE_LOWER * HUMID_SCALE ))

TOP_ARGS=(
        --step=60 -v "degrees C" --upper-limit ${TEMP_SCALE_UPPER} --lower-limit ${TEMP_SCALE_LOWER} --rigid
	--right-axis-label "Humidity"
	--right-axis ${HUMID_SCALE}:-${HUMID_SHIFT}
        DEF:temp=/home/pi/sc/data/tank-top-temp.rrd:temp:AVERAGE
        DEF:humid=/home/pi/sc/data/tank-top-humid.rrd:humid:AVERAGE
	CDEF:scaled_humid=humid,${HUMID_SHIFT},+,${HUMID_SCALE},/
	LINE2:scaled_humid\#0000FF:"humidity"
        LINE2:temp\#FF0000:"temp"
)

case "$QUERY_STRING" in
	t-4h)    OUTFILE="4h.png";      PARAMS=(--start now-4h  --title "Melman Vivarium Sensor Data 4h"      ${TEMP_ARGS[@]}) ;;
	t-24h)   OUTFILE="24h.png";     PARAMS=(--start now-24h --title "Melman Vivarium Sensor Data 24h"     ${TEMP_ARGS[@]}) ;;
	t-7d)    OUTFILE="7d.png";      PARAMS=(--start now-7d  --title "Melman Vivarium Sensor Data 7d"      ${TEMP_ARGS[@]}) ;;
	t-30d)   OUTFILE="30d.png";     PARAMS=(--start now-30d --title "Melman Vivarium Sensor Data 30d"     ${TEMP_ARGS[@]}) ;;
	top-4h)  OUTFILE="top-4h.png";  PARAMS=(--start now-4h  --title "Melman Vivarium Top Sensor Data 4h"  ${TOP_ARGS[@]})  ;;
	top-24h) OUTFILE="top-24h.png"; PARAMS=(--start now-24h --title "Melman Vivarium Top Sensor Data 24h" ${TOP_ARGS[@]})  ;;
	top-7d)  OUTFILE="top-7d.png";  PARAMS=(--start now-7d  --title "Melman Vivarium Top Sensor Data 7d"  ${TOP_ARGS[@]})  ;;
	*)
		cat <<HERE
Content-Type: text/html
Status: 404 Not Found

<html><body>Invalid query parameter '${QUERY_STRING}'</body></html>
HERE
	exit 1
esac

rrdtool graph /home/pi/public_html/${OUTFILE} ${PARAMS[@]} ${COMMON_ARGS[@]} >&2

cat <<HERE
Location: /~pi/${OUTFILE}

HERE

