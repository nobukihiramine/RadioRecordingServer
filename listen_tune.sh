#!/bin/bash

# listen_tune.sh
# 周波数の変更
# Arguments
#   $1 : Frequency [MHz]

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

cd "$(dirname "$0")"

readonly FREQUENCY_MHZ="$1"

# ラジオ周波数の指定は必須
if [ "" = "${FREQUENCY_MHZ}" ]; then
    echo "Error : Frequency[MHz] is not specified."
    exit
fi

# load済みのmodule-loopbackがない場合はリスニング中でない
readonly INFO_LOADED_MODULE_LOOPBACK=$(pactl list modules short | grep module-loopback)
if [ "" = "${INFO_LOADED_MODULE_LOOPBACK}" ]; then
    echo "Error : Not listening to radio."
    exit
fi

# 周波数の設定
# ffmpegのプロセスがない場合のみ処理。プロセスがある場合は、ラジオ録音中なのでラジオ処理なし。
readonly INFO_FFMPEG_PROCESS=$(ps aux | grep [f]fmpeg)
if [ "" != "${INFO_FFMPEG_PROCESS}" ]; then
	echo "Now Recording! Skipped Radio tuning."
else
	python3 ./pymodules/radio_tune.py $FREQUENCY_MHZ
fi
