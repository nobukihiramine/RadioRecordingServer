# radio_off.py
# ラジオをオフする

# Arguments
#   argv[1] : Quiet mode. Suppress messages. Not radio mute. "0" is not Quiet mode.

import sys
from rda5807m.rda5807m import RDA5807M

# 引数の処理
argc = len( sys.argv )
bQuiet = True if ((2 <= argc) and ("0" != sys.argv[1])) else False  # "0"以外は、Quiet mode

# ラジオの処理
radio = RDA5807M()

if( not radio.isPoweredUp() ):
    # ラジオが電源が既に切れている
    if( not bQuiet ):
        print( "Radio is already turned off." )
    sys.exit(0)

# ラジオの電源を切る
radio.end()
if( not bQuiet ):
    print( "Radio turned off." )
