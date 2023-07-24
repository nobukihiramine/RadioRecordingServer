#!/bin/bash

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

# listen_on.sh
# ラジオの聴取開始
# Arguments
#   $1 : Frequency [MHz]

cd "$(dirname "$0")"

readonly FREQUENCY_MHZ="$1"

# ラジオ周波数の指定は必須
if [ "" = "${FREQUENCY_MHZ}" ]; then
    echo "Error : Frequency[MHz] is not specified."
    exit
fi

# マイク端子から入るラジオ音源を、イヤホン端子にループバックする
# load済みのmodule-loopbackがない場合のみ処理
readonly INFO_LOADED_MODULE_LOOPBACK=$(pactl list modules short | grep module-loopback)
if [ "" = "${INFO_LOADED_MODULE_LOOPBACK}" ]; then
	# 「pactl load-module」の結果、loadされたモジュールの番号が標準出力されるので、出力をnullデバイスにリダイレクト。
	pactl load-module module-loopback > /dev/null
fi

# ラジオON
# ffmpegのプロセスがない場合のみ処理。プロセスがある場合は、ラジオ録音中なのでラジオ処理なし。
readonly INFO_FFMPEG_PROCESS=$(ps aux | grep [f]fmpeg)
if [ "" != "${INFO_FFMPEG_PROCESS}" ]; then
	echo "Now Recording! Skipped Radio-On."
else
	python3 ./pymodules/radio_on.py $FREQUENCY_MHZ
fi
