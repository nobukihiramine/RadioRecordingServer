# radio_on.py
# ラジオを周波数を指定してオンする

# Arguments
#   argv[1] : Frequency [MHz]
#   argv[2] : Quiet mode. Suppress messages. Not radio mute. "0" is not Quiet mode.

import sys
from rda5807m.rda5807m import RDA5807M

# 引数の処理
argc = len( sys.argv )
if( 1 == argc ):
    # 周波数の指定がない場合はエラー
    print( "Error : Frequency is not specified." )
    sys.exit(254)
strFrequencyMHz = sys.argv[1]
bQuiet = True if ((3 <= argc) and ("0" != sys.argv[2])) else False  # "0"以外は、Quiet mode

# ラジオの処理
radio = RDA5807M()

# ラジオの電源を入れる
if( bQuiet ):
    radio.begin()
    radio.setFrequency( int(float(strFrequencyMHz) * 1000), False ) # 周波数はMHzをKHzに変換して渡す。サイレントモード時は、チューニング完了を待たない
else:
    radio.begin()
    radio.setFrequency( int(float(strFrequencyMHz) * 1000) )        # 周波数はMHzをKHzに変換して渡す。
    print( "Radio turned on.")
    print( "  frequency : %4.1f[MHz]" % (radio.getFrequency() / 1000.0) )   # 周波数はKHzで得られるので、MHzに変換して表示する。
