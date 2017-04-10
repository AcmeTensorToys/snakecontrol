#!/bin/zsh

DMX_SCALE=5
DMX_SHIFT=20

COMMON_ARGS=(
	--end now
        --width=960 --height=480
        --lazy
        --step=60 -v "degrees C" --upper-limit 32 --lower-limit 19 --rigid
	--right-axis-label "DMX"
	--right-axis ${DMX_SCALE}:-${DMX_SHIFT}
        DEF:tempH=/home/pi/sc/data/heater-temp.rrd:temp:AVERAGE
        DEF:tempHN=/home/pi/sc/data/hide-near-temp.rrd:temp:AVERAGE
        DEF:dmxHN=/home/pi/sc/data/hide-near-dmx.rrd:dmx:AVERAGE
        DEF:tempHF=/home/pi/sc/data/hide-far-temp.rrd:temp:AVERAGE
        DEF:tempTN=/home/pi/sc/data/tank-near-temp.rrd:temp:AVERAGE
        DEF:tempTF=/home/pi/sc/data/tank-far-temp.rrd:temp:AVERAGE
	CDEF:scaled_dmxHN=dmxHN,${DMX_SHIFT},+,${DMX_SCALE},/
	LINE:scaled_dmxHN\#000000:"dmx near"
        LINE2:tempH\#FF0000:"heater"
        LINE2:tempHN\#808000:"hide near"
        LINE2:tempHF\#FF8000:"hide far"
        LINE2:tempTN\#00FF00:"tank near"
        LINE2:tempTF\#00FFFF:"tank far"
        HRULE:30#800000
        HRULE:25#8000FF
        HRULE:21#0000FF
)

case "$QUERY_STRING" in
	4h)  OUTFILE="4h.png";  PARAMS=(--start now-4h  --title "Melman Vivarium Sensor Data 4h" ) ;;
	24h) OUTFILE="24h.png"; PARAMS=(--start now-24h --title "Melman Vivarium Sensor Data 24h") ;;
	7d)  OUTFILE="7d.png";  PARAMS=(--start now-7d  --title "Melman Vivarium Sensor Data 7d" ) ;;
	30d) OUTFILE="30d.png"; PARAMS=(--start now-30d --title "Melman Vivarium Sensor Data 30d") ;;
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

