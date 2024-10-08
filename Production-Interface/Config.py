########################################
# ***** CONSTANTS *****
OUTPUT_FORMATS			= ["PDF", "PNG", "SVG"]
PDF						= "PDF"
PNG						= "PNG"
SVG						= "SVG"

BUFFER_SIZE				= 1024
MIN_PORT				= 1024
MAX_PORT				= 65535

MIN_INTERVAL			= 10		# Milliseconds
MAX_INTERVAL			= 10000		# Milliseconds
LIVE_DISPLAY_FREQENCY	= 100		# Milliseconds

MSG_TYPE_DISCOVERY		= "ID"
MSG_TYPE_STATUS			= "STATUS"
MSG_TYPE_TEST			= "TEST"
MSG_RESULT_STARTED		= "STARTED"
MSG_RESULT_STOPPED		= "STOPPED"
MSG_RESULT_ERROR		= "ERROR"
MSG_FULL_STARTED		= "TEST;RESULT=STARTED"
MSG_FULL_STOPPED		= "TEST;RESULT=STOPPED"
MSG_FULL_STOP			= "TEST;CMD=STOP;"
########################################