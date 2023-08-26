# Copyright 2023 Nobuki HIRAMINE
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# RDA5807M.py
#
# Class to control RDA5807M
#
# Author : Nobuki HIRAMINE, http://www.hiramine.com
# History :
#   2020/06/27 Created for use with Arduino/ATmega328.
#   2023/05/06 Modified for use with Raspberry Pi 3

import smbus
import time

# --- 定数定義 ---

# RDA5807Mのレジスタ定義に基づく定数

# REG 00H
REG_00H_CHIPID_MASK             = 0b1111111111111111    # Chip ID.(Default 0x5804)
REG_00H_CHIPID_SHIFT            = 0

# REG 02H
REG_02H_DHIZ                    = 0b1000000000000000    # 0 = High impedance. Audio output を High Z (=High Impedance) にする。結果として、Audio output は駆動していない状態になる。
                                                        # 1 = Normal operation. Audio output の High Z (=High Impedance) を解除にする。結果として、Audio output は駆動状態になる。
REG_02H_DMUTE                   = 0b0100000000000000    # 0 = Mute. 1 = Normal operation
REG_02H_MONO                    = 0b0010000000000000    # 0 = Stereo. 1 = Force mono
REG_02H_BASS                    = 0b0001000000000000    # 0 = Bass Boost disabled. 1 = Bass Boost enabled.
REG_02H_RCLK_NON_CALIBRATE_MODE = 0b0000100000000000    # 0 = Reference clock is always supply.
                                                        # 1 = Reference clock is not always supply when FM work.
REG_02H_RCLK_DIRECT_INPUT_MODE  = 0b0000010000000000    # 1 = Reference clock use the directly input mode.
REG_02H_SEEKUP                  = 0b0000001000000000    # 0 = Seek down. 1 = Seek up.
REG_02H_SEEK                    = 0b0000000100000000    # 0 = Disable stop seek.
                                                        # 1 = Enable Seek begins in the direction specified by SEEKUP
                                                        #     and ends when a channel is found, or the entire band has been searched.
                                                        #     The SEEK bit is set low and the STC bit is set high when the seek operation completes.
REG_02H_SKMODE                  = 0b0000000010000000    # Seek Mode
                                                        # 0 = wrap at the upper or lower band limit and continue seeking.
                                                        #     上限や下限に達したら下限や上限からシークを続ける。
                                                        # 1 = stop seeking at the upper or lower band limit.
                                                        #     上限や下限に達したらシークを終える。
REG_02H_CLK_MODE_MASK           = 0b0000000001110000    # Clock Mode
REG_02H_CLK_MODE_SHIFT          = 4                     # 000 = 32.768kHz, 001 = 12Mhz, 101 = 24Mhz, 010 = 13Mhz,
                                                        # 110 = 26Mhz, 011 = 19.2Mhz, 111 = 38.4Mhz
REG_02H_RDS_EN                  = 0b0000000000001000    # RDS/RBDS
                                                        # （Radio Data System（ラジオ・データ・システム、RDS）とは、
                                                        # 　従来のFMラジオ放送に少量のデジタル情報を埋め込むための通信プロトコル規格である。
                                                        # 　RDSは、時間、放送局、番組情報を含め、複数種類の送信情報を規格化している。
                                                        # 　この規格は欧州放送連合(EBU)の事業として始まり、やがて国際電気標準会議(IEC)の国際標準規格となった。
                                                        # 　米国版のRDSは正式名称がRadio Broadcast Data System(RBDS)で、両者の規格には僅かばかりの差異がある。
                                                        # 　日本では、RDSに類似したデジタルデータ放送規格Data Radio Channel(DARC)をほぼ同時期に開発、実用化した経緯から、RDSには未対応である。
                                                        # 　出展 : https:#ja.wikipedia.org/wiki/Radio_Data_System）
REG_02H_NEW_METHOD              = 0b0000000000000100    # New Demodulate Method Enable, can improve the receive sensitivity about 1dB.
REG_02H_SOFT_RESET              = 0b0000000000000010    # Soft reset. 0 = not reset. 1 = reset.
REG_02H_ENABLE                  = 0b0000000000000001    # Power Up. 0 = Disabled. 電源オフ。 1 = Enabled. 電源オン。

# REG 03H
REG_03H_CHAN_MASK               = 0b1111111111000000    # Channel Select.
REG_03H_CHAN_SHIFT              = 6                     # BAND = 0.      Frequency = Channel Spacing (kHz) x CHAN + 87.0 MHz
                                                        # BAND = 1 or 2. Frequency = Channel Spacing (kHz) x CHAN + 76.0 MHz
                                                        # BAND = 3.      Frequency = Channel Spacing (kHz) x CHAN + 65.0 MHz
                                                        # CHAN is updated after a seek operation.
REG_03H_TUNE                    = 0b0000000000010000    # Tune. 0 = Disable. 1 = Enable.
REG_03H_BAND_MASK               = 0b0000000000001100    # Band Select
REG_03H_BAND_SHIFT              = 2                     # 00 = 87～108MHz(US/Europe), 01 = 76～91MHz(Japan), 10 = 76～108MHz(World Wide), 11 = 65～76MHz(East Europe) or 50～65MHz
REG_03H_SPACE_MASK              = 0b0000000000000011    # Channel Spacing
REG_03H_SPACE_SHIFT             = 0                     # 00 = 100kHz, 01 = 200kHz, 10 = 50kHz, 11 = 25kHz

# REG 04H
REG_04H_DE                      = 0b0000100000000000    # De-emphasis. 0 = 75 μs. 1 = 50 μs.
                                                        # 日本の放送の場合、FM放送は50μs。
                                                        # （ＦＭ変復調の過程において、高い周波数でのノイズレベルが高くなる性質がある。
                                                        # 　そこで、送信時に高域を強調し、受信時に高域を減衰する操作を行うことでノイズを低減するようになっている。
                                                        # 　これをエンファシス処理と言い、送信時の処理をプリエンファシス，受信時の処理をディエンファシスと言う。
                                                        # 　エンファシス処理を行う周波数特性は放送方式により規格化されており、
                                                        # 　日本の放送の場合、ＦＭ放送は５０μＳ，テレビの音声は７５μＳとなっている。
                                                        # 　この数字はエンファシス処理を行う部品（コンデンサ及び抵抗）の値の積により定義されている。
                                                        # 　　アメリカのFM放送は、ステレオ変調の方式は日本と同じであるが、ディエンファシスの定数は日本とは違い７５μＳである。
                                                        # 　出典 : http:#www2.jan.ne.jp/~jr7cwk/electro/aki_lcdtv/de_emp1.html）
REG_04H_SOFTMUTE_EN             = 0b0000001000000000    # 0 = Soft Mute Disable. 1 = Soft Mute Enable.
REG_04H_AFCD                    = 0b0000000100000000    # 0 = AFC work. 1 = AFC disabled.
                                                        # AFC(Automatic frequency control : 自動周波数制御) 
                                                        # （アナログチューニング方式の受信機でよくみられたもので、
                                                        # 　受信周波数と放送周波数のずれをフィードバックして、自動的に放送周波数に合わせる回路である。
                                                        # 　出典 : https:#ja.wikipedia.org/wiki/自動周波数制御）

# REG 05H
REG_05H_SEEKTH_MASK             = 0b0000111100000000    # Seek SNR threshold value. Seek SNR 閾値.
REG_05H_SEEKTH_SHIFT            = 8                     # SNR : Signal-Noise Ratio. 信号雑音比. SN比.
                                                        # 値を大きくするとクリアな局のみシーク選局される。値を小さくするとノイジーな局もシーク選局される。
REG_05H_VOLUME_MASK             = 0b0000000000001111    # DAC Gain Control Bits(Volume).
REG_05H_VOLUME_SHIFT            = 0                     # 0000 = min, 1111 = max.

# REG 07H
REG_07H_TH_SOFTBLEND_MASK       = 0b0111110000000000    # Threshold for noise soft blend setting, unit 2dB
REG_07H_TH_SOFTBLEND_SHIFT      = 10                    # default : 0b10000
REG_07H_65M_50M_MODE            = 0b0000001000000000    # 65M_50M_MODE値の設定/取得用のマスク
REG_07H_SOFTBLEND_EN            = 0b0000000000000010    # 1, Softblend enable

# REG 0AH
REG_0AH_READCHAN_MASK           = 0b0000001111111111    # Read Channel.
REG_0AH_READCHAN_SHIFT          = 0                     # BAND = 0.      Frequency = Channel Spacing (kHz) x READCHAN[9:0]+ 87.0 MHz
                                                        # BAND = 1 or 2. Frequency = Channel Spacing (kHz) x READCHAN[9:0]+ 76.0 MHz
                                                        # BAND = 3.      Frequency = Channel Spacing (kHz) x READCHAN[9:0]+ 65.0 MHz
                                                        # READCHAN[9:0] is updated after a tune or seek operation.

# REG 0BH
REG_0BH_RSSI_MASK               = 0b1111111000000000    # RSSI.(Received Signal Strength Indicator : 受信信号強度指標)
REG_0BH_RSSI_SHIFT              = 9                     # 000000 = min
                                                        # 111111 = max
                                                        # RSSI scale is logarithmic.

# レジスタ定義から求まる最大値
CHAN_MAX   = REG_03H_CHAN_MASK >> REG_03H_CHAN_SHIFT        # CHAN最大値は、CHANビットを全部立てた値を、シフト量シフトした値。0b1111111111 = 1023。
VOLUME_MAX = REG_05H_VOLUME_MASK >> REG_05H_VOLUME_SHIFT    # VOLUME最大値は、VOLUMEビットを全部立てた値を、シフト量シフトした値。0b1111 = 15。
SEEKTH_MAX = REG_05H_SEEKTH_MASK >> REG_05H_SEEKTH_SHIFT    # SEEKTH最大値は、SEEKTHビットを全部立てた値を、シフト量シフトした値。0b1111 = 15。
SOFTBLENDTH_MAX = REG_07H_TH_SOFTBLEND_MASK >> REG_07H_TH_SOFTBLEND_SHIFT   # SOFTBLENDTH最大値は、SOFTBLENDTHビットを全部立てた値を、シフト量シフトした値。0b111111 = 31。

# デバイスのI2Cアドレス
I2C_ADDR_RDA5807M = 0x11    # RDA5807MのI2Cアドレス

# 読み書き可能なレジスタのサイズ
READABLE_REGISTER_SIZE = 16
WRITABLE_REGISTER_SIZE =  8

# MUTE処理の実現方法
MUTE_METHOD = 2 # MUTEの実現方法は３種類ある（「Volumeを0にする」は除く。実際、Volumeをゼロにしても無音にはならない）
                # ① SOFT_MUTEビット（REG 04H の BITS 9）を立てることでMuteする。
                # ② DMUTEビット（REG 02H の BITS 14）を倒すことでMuteする。
                # ③ DHIZビット（REG 02H の BITS 15）を倒すことでMuteする。

# --- クラス定義 ---

class RDA5807M:
    _i2c = None
    _i2c_addr = None

    # コンストラクタ
    def __init__( self ):
        # クラスメンバーへのセット
        self._i2c_addr = I2C_ADDR_RDA5807M
        self._i2c = smbus.SMBus(1)

    # デストラクタ
    def __del__( self ):
        # I2C接続のクローズ
        self._i2c.close()

    # チップIDの取得
    def getChipID( self ):
        uiChipID = self._decodeRegister( 0x00, REG_00H_CHIPID_MASK, REG_00H_CHIPID_SHIFT )
        return format( uiChipID, "x" ) # 16進数表現文字列に変換して返却

    # - 開始・終了 -

    def isPoweredUp( self ) :
        return True if self._decodeRegister( 0x02, REG_02H_ENABLE, 0 ) else False
    
    def begin( self ):
        # Power-On : 電源ビットを立てる
        self._updateRegister( 0x02, REG_02H_ENABLE, 0, REG_02H_ENABLE )

        # Register 02H の初期化
        uiRegister = self._readRegister( 0x02 )
        uiRegister |= REG_02H_DHIZ      # 立てて、Audioオン。(デフォルト値は0)
        uiRegister |= REG_02H_DMUTE     # 立てて、Audioオン。(デフォルト値は0)
        uiRegister &= ~REG_02H_MONO     # モノラルではなくステレオとするので、倒す。(デフォルト値は0)
        uiRegister &= ~REG_02H_BASS     # Bass boost機能は使用しないので倒す。(デフォルト値は0)
        uiRegister &= ~REG_02H_RCLK_NON_CALIBRATE_MODE  # Reference clockは常に供給されるので倒す。(デフォルト値は0)
        uiRegister &= ~REG_02H_RCLK_DIRECT_INPUT_MODE   # Rrefernce clock directly input mode ではないので倒す。(デフォルト値は0)
        uiRegister &= ~REG_02H_SEEKUP   # Seekの方向は、Seek開始時に指定するので、どちらでもよく倒す。(デフォルト値は0)
        uiRegister &= ~REG_02H_SEEK     # Seek開始時に立てるので、初期化時は倒す。(デフォルト値は0)
        uiRegister &= ~REG_02H_SKMODE   # バンド境界でSeekを継続するかは、Seek開始時に指定するので、どちらでもよく倒す。(デフォルト値は0)
        uiRegister &= ~REG_02H_CLK_MODE_MASK    # 32.768kHz(=0b000)に設定する。(デフォルト値は0)
        uiRegister &= ~REG_02H_RDS_EN   # RDS/RBDS機能は使用しないので倒す。(デフォルト値は0)
        uiRegister &= ~REG_02H_NEW_METHOD    # New Demodulate Methodは使用しないので倒す。(デフォルト値は0)
        self._writeRegister( 0x02, uiRegister )

        # Register 03H の初期化
        uiRegister = self._readRegister( 0x03 )
        uiRegister &= ~REG_03H_CHAN_MASK    # 周波数を下限値にする(=0000000000)。(デフォルト値は0x13f)
        uiRegister &= ~REG_03H_TUNE         # Tune開始時に立てるので、初期化時は倒す。(デフォルト値は0)
        uiRegister &= ~REG_03H_BAND_MASK    # AMも聞くためにワイドFMが聴けるWorld Wide(=0b10)(76～108MHz)に設定する。(デフォルト値は0)
        uiRegister |= ( (0b10 << REG_03H_BAND_SHIFT) & REG_03H_BAND_MASK )
        uiRegister &= ~REG_03H_SPACE_MASK   # 0.1MHz単位で指定できるように、100kHz(=0b00)に設定する。(デフォルト値は0)
        self._writeRegister( 0x03, uiRegister )
        
        # Register 04H の初期化
        uiRegister = self._readRegister( 0x04 )
        uiRegister |= REG_04H_DE            # 日本のFM放送のDe-emphasisは、50μsなので、立てる。(デフォルト値は0)
        uiRegister &= ~REG_04H_SOFTMUTE_EN  # 倒して、Audioオン。(デフォルト値は0)
        uiRegister &= ~REG_04H_AFCD         # 自動周波数制御機能を使用するので倒す。(デフォルト値は0)
        self._writeRegister( 0x04, uiRegister )

        # Register 05H の初期化
        uiRegister = self._readRegister( 0x05 )
        uiRegister &= ~REG_05H_SEEKTH_MASK  # シーク閾値として、8(=0b1000)に設定する。(デフォルト値は0b1000)
        uiRegister |= ( (0b1000 << REG_05H_SEEKTH_SHIFT) & REG_05H_SEEKTH_MASK )
        uiRegister &= ~REG_05H_VOLUME_MASK  # ボリューム値を、11(=0b1011)に設定する。(デフォルト値は0b1011)
        uiRegister |= ( (0b1011 << REG_05H_VOLUME_SHIFT) & REG_05H_VOLUME_MASK )
        self._writeRegister( 0x05, uiRegister )

        # Register 07H の初期化
        uiRegister = self._readRegister( 0x07 )
        uiRegister &= ~REG_07H_TH_SOFTBLEND_MASK    # ソフトブレンド閾値として、16(=0b10000)に設定する。(デフォルト値は0b10000)
        uiRegister |= ( (0b10000 << REG_07H_TH_SOFTBLEND_SHIFT) & REG_07H_TH_SOFTBLEND_MASK )
        uiRegister |= REG_07H_65M_50M_MODE  # BANDが0b11のときにのみ意味がある。デフォルト値として立てる。(デフォルト値は1)
        uiRegister |= REG_07H_SOFTBLEND_EN  # ソフトブレンド機能を使用するので立てる。(デフォルト値は1)
        self._writeRegister( 0x07, uiRegister )

    # 終了
    def end( self ):
        # Power-off : 電源ビットを倒す
        self._updateRegister( 0x02, REG_02H_ENABLE, 0, 0 )

    # - 周波数関連 -

    # チャンネルスペーシングの取得
    # ChannelSpacing[kHz]。00 = 100kHz, 01 = 200kHz, 10 = 50kHz, 11 = 25kHz
    def getChannelSpacing( self ):
        # ChannelSpacingのレジスタ値の取得
        byChannelSpacingType = self._decodeRegister( 0x03, REG_03H_SPACE_MASK, REG_03H_SPACE_SHIFT )

        # ChannelSpacingのレジスタ値に対応するチャンネルスペーシングの値を返す。
        if(   0 == byChannelSpacingType ):
            return 100
        elif( 1 == byChannelSpacingType ):
            return 200
        elif( 2 == byChannelSpacingType ):
            return 50
        elif( 3 == byChannelSpacingType ):
            return 25

        # ChannelSpacingのレジスタ値が仕様範囲外の場合は、ゼロを返す。
        return 0

    # READCHAN値の取得
    def getREADCHAN( self ):
        return self._decodeRegister( 0x0A, REG_0AH_READCHAN_MASK, REG_0AH_READCHAN_SHIFT )

    # BAND値の取得
    # 00 = 87～108MHz(US/Europe), 01 = 76～91MHz(Japan), 10 = 76～108MHz(World Wide), 11 = 65～76MHz(East Europe) or 50～65MHz
    def getBand( self ):
        return self._decodeRegister( 0x03, REG_03H_BAND_MASK, REG_03H_BAND_SHIFT )

    # 周波数の最小値の取得
    def getFrequencyMin( self ):
        # BAND値の取得
        byBand = self.getBand()

        # BAND値から周波数の最小値が決まる
        # 00 = 87～108MHz(US/Europe), 01 = 76～91MHz(Japan), 10 = 76～108MHz(World Wide), 11 = 65～76MHz(East Europe) or 50～65MHz
        if(   0 == byBand ):
            return 87000
        elif( 1 == byBand ):
            return 76000
        elif( 2 == byBand ):
            return 76000
        elif( 3 == byBand ):
            if( self._readRegister( 0x07 ) & REG_07H_65M_50M_MODE ):
                # 「バンド値が3(=0b11)」かつ「65M_50M_MODEビットが立っている」場合は、65～76MHz(East Europe)
                return 65000
            return 50000

        # BAND値が仕様範囲外の場合は、ゼロを返す。
        return 0

    # 現在の周波数の取得
    def getFrequency( self ):
        #ulFrequencyMin = self.getFrequencyMin()
        ulFrequencyMin = 76000  # 処理効率化（レジスタの値の読み込みを省略）
        #byChannelSpacing = self.getChannelSpacing()
        byChannelSpacing = 100  # 処理効率化（レジスタの値の読み込みを省略）

        # Frequency[kHz] = ChannelSpacing[kHz] x CHAN + FrequencyMin[kHz]
        return byChannelSpacing * self.getREADCHAN() + ulFrequencyMin

    # 周波数の設定
    def setFrequency( self, ulFrequency, bWaitTuningComplete = True ):
        #ulFrequencyMin = self.getFrequencyMin()
        ulFrequencyMin = 76000  # 処理効率化（レジスタの値の読み込みを省略）
        #byChannelSpacing = self.getChannelSpacing()
        byChannelSpacing = 100  # 処理効率化（レジスタの値の読み込みを省略）

        # 下限値を下まわる場合は、下限値に。
        if( ulFrequencyMin > ulFrequency ):
            ulFrequency = ulFrequencyMin

        # Frequency[kHz] = ChannelSpacing[kHz] x CHAN + FrequencyMin[kHz]
        # CHAN = (Frequency[kHz] - FrequencyMin[kHz]) / ChannelSpacing[kHz]
        uiCHAN = int( (ulFrequency - ulFrequencyMin) / byChannelSpacing )
        
        # 上限値を超える場合は、上限値に。
        if( CHAN_MAX < uiCHAN ):
            uiCHAN = CHAN_MAX

        # チューニングする周波数の設定と、Tune開始
        # 補足）CHANの書き込みは、TUNEビットを立てないと無視される。
        #       TUNEビットは、Tuneオペレーション完了後に倒れる。
        self._updateRegister( 0x03, REG_03H_CHAN_MASK | REG_03H_TUNE, 0, (uiCHAN << REG_03H_CHAN_SHIFT) | REG_03H_TUNE )

        # チューニング完了を待つ
        if bWaitTuningComplete:
            # TUNEビットが立っている場合は、Tune中なので、ビットが倒れるまで待つ。
            while( self._readRegister( 0x03 ) & REG_03H_TUNE ):
                # TUNEビットが倒れるまで待つ。
                time.sleep(0.001) # 1msec

    # RSSI値の取得
    # Received Signal Strength Indicator : 受信強度
    def getRSSI( self ):
        return self._decodeRegister( 0x0B, REG_0BH_RSSI_MASK, REG_0BH_RSSI_SHIFT )

    def getRssiMax( self ):
        return (REG_0BH_RSSI_MASK >> REG_0BH_RSSI_SHIFT)

    # - シーク関連 -

    # Seek操作
    def seek( self, bUp, bWrap = True ):
        # シーク方向。REG_02H_SEEKUPのビットの更新
        self._updateRegister( 0x02, REG_02H_SEEKUP, 0, REG_02H_SEEKUP if bUp else 0 )

        # 周波数終端での挙動。REG_02H_SKMODEビットの更新
        # 0 = wrap at the upper or lower band limit and continue seeking.
        # 1 = stop seeking at the upper or lower band limit.
        self._updateRegister( 0x02, REG_02H_SKMODE, 0, 0 if bWrap else REG_02H_SKMODE )

        # Seek開始
        # 補足）SEEKビットは、Seekオペレーション完了後に倒れる
        self._updateRegister( 0x02, REG_02H_SEEK, 0, REG_02H_SEEK )

        # SEEKビットが立っている場合は、Seek中なので、ビットが倒れるまで待つ。
        while( self._readRegister( 0x02 ) & REG_02H_SEEK ):
            # SEEKビットが倒れるまで待つ。
            time.sleep(0.001) # 1msec

    # SeekTh値の取得
    # SeekThreshold : シーク閾値。値を大きくするとよりクリアな局のみシークし、値を小さくするとよりノイジーな局もシークするようになる。
    def getSeekTh( self ):
        return self._decodeRegister( 0x05, REG_05H_SEEKTH_MASK, REG_05H_SEEKTH_SHIFT )
    
    # SeekTh値の設定
    def setSeekTh( self, bySeekTh ):
        # 上限値を超える場合は、上限値に。
        if( SEEKTH_MAX < bySeekTh ):
            bySeekTh = SEEKTH_MAX

        self._updateRegister( 0x05, REG_05H_SEEKTH_MASK, REG_05H_SEEKTH_SHIFT, bySeekTh )

    def getSeekThMax( self ):
        return SEEKTH_MAX

    # - サウンド関連 -

    # Voluem値の取得
    def getVolume( self ):
        return self._decodeRegister( 0x05, REG_05H_VOLUME_MASK, REG_05H_VOLUME_SHIFT )

    # Volume値の設定
    def setVolume( self, byVolume ):
    	# 上限値を超える場合は、上限値に。
        if( VOLUME_MAX < byVolume ):
            byVolume = VOLUME_MAX

        self._updateRegister( 0x05, REG_05H_VOLUME_MASK, REG_05H_VOLUME_SHIFT, byVolume )

        #self.setMute( False )    # Mute解除

    def getVolumeMax( self ):
        return VOLUME_MAX

    # Mute
    def isMuted( self ):
        if(   1 == MUTE_METHOD ):     # ① SOFT_MUTEビット（REG 04H の BITS 9）が立っていたらMuteしている。
            return True if self._decodeRegister( 0x04, REG_04H_SOFTMUTE_EN, 0 ) else False
        elif( 2 == MUTE_METHOD ):   # ② DMUTEビット（REG 02H の BITS 14）が倒れていたらMuteしている。立っていたらMuteしてない。
            return False if self._decodeRegister( 0x02, REG_02H_DMUTE, 0 ) else True
        elif( 3 == MUTE_METHOD ):   # ③ DHIZビット（REG 02H の BITS 15）が倒れていたらMuteしている。立っていたらMuteしてない。
            return False if self._decodeRegister( 0x02, REG_02H_DHIZ, 0 ) else True

    def setMute( self, bMute ):
        if(   1 == MUTE_METHOD ):     # ① SOFT_MUTEビット（REG 04H の BITS 9）を立てることでMuteする。
            self._updateRegister( 0x04, REG_04H_SOFTMUTE_EN, 0, REG_04H_SOFTMUTE_EN if bMute else 0 )
        elif( 2 == MUTE_METHOD ):   # ② DMUTEビット（REG 02H の BITS 14）を倒すことでMuteする。
            self._updateRegister( 0x02, REG_02H_DMUTE, 0, 0 if bMute else REG_02H_DMUTE )
        elif( 3 == MUTE_METHOD ):   # ③ DHIZビット（REG 02H の BITS 15）を倒すことでMuteする。
            self._updateRegister( 0x02, REG_02H_DHIZ, 0, 0 if bMute else REG_02H_DHIZ )

    # ソフトブレンド（によるノイズ軽減機能）が有効化どうか
    def isSoftBlendEnabled( self ):
        return True if ( self._readRegister( 0x07 ) & REG_07H_SOFTBLEND_EN ) else False
    
    # ソフトブレンド（によるノイズ軽減機能）の有効化/無効化
    def enableSoftBlend( self, bEnable ):
        self._updateRegister( 0x07, REG_07H_SOFTBLEND_EN, 0, REG_07H_SOFTBLEND_EN if bEnable else 0 )

    # ソフトブレンド閾値の取得
    def getSoftBlendTh( self ):
        return self._decodeRegister( 0x07, REG_07H_TH_SOFTBLEND_MASK, REG_07H_TH_SOFTBLEND_SHIFT )
    
    # ソフトブレンド閾値の設定
    def setSoftBlendTh( self, bySoftBlendTh ):
        # 上限値を超える場合は、上限値に。
        if( SOFTBLENDTH_MAX < bySoftBlendTh ):
            bySoftBlendTh = SOFTBLENDTH_MAX

        self._updateRegister( 0x07, REG_07H_TH_SOFTBLEND_MASK, REG_07H_TH_SOFTBLEND_SHIFT, bySoftBlendTh )

    def getSoftBlendThMax( self ):
        return SOFTBLENDTH_MAX

    # - デバッグ関連 -

    # レジスタ列の読み込み
    def readRegisters( self ):
        # アウトプットの初期化
        auiRegister = []

        for i in range(0, READABLE_REGISTER_SIZE):
            auiRegister.append( self._readRegister( i ) )

        return auiRegister

    # - レジスタの読み書き -

    # レジスタからの値の解読
    def _decodeRegister( self, byRegAddr, uiMask, byShift ):
        return ( self._readRegister( byRegAddr ) & uiMask ) >> byShift

    # レジスタの値の更新
    def _updateRegister( self, byRegAddr, uiMask, byShift, uiValue  ):
        # uiMaskのビットを倒し、その後、value値をシフトした値のビットを立てる。
        # uiMask以外のビットが更新されないよう、value値はuiMaskでマスクする。
        self._writeRegister( byRegAddr, ( self._readRegister(byRegAddr) & ~uiMask ) | ( (uiValue << byShift) & uiMask ) )

    # レジスタの値の読み込み
    def _readRegister( self, byRegAddr ):
        # 読み込み可能バッファーサイズを超えている場合は、無処理、ゼロを返す。
        if( READABLE_REGISTER_SIZE <= byRegAddr ):
            return 0

        (byHigh, byLow) = self._i2c.read_i2c_block_data( self._i2c_addr, byRegAddr, 2 )
        time.sleep( 0.00001 )    # 10μs(STOP to START Time : Min 1.3[μs]のウェイトを設ける。)

        return ((byHigh & 0xFF) << 8) + (byLow & 0xFF)

    # レジスタの値の書き込み
    def _writeRegister( self, byRegAddr, uiRegister ):
        # 書き込み可能バッファーサイズを超えている場合は、無処理。
        if( WRITABLE_REGISTER_SIZE <= byRegAddr ):
            return

        byHigh = (uiRegister >> 8) & 0xFF
        byLow  = uiRegister & 0xFF

        self._i2c.write_i2c_block_data( self._i2c_addr, byRegAddr, [byHigh, byLow] )
        time.sleep( 0.00001 )    # 10μs(STOP to START Time : Min 1.3[μs]のウェイトを設ける。)
