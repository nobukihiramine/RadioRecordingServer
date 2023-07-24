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

# record.sh
# ラジオの録音
# Arguments
#   $1 : Frequency [MHz]
#   $2 : Recording length [minute]
#   $3 : Bit rate for mp3 file [kbps] : Optional. Default is 128[kbps].
#   $4 : Output directory path : Optional. Default is current directory.
#   $5 : Scheduled recording name : Optional.

readonly WORK_DIR_ORG=$(pwd)
cd "$(dirname "$0")"

readonly FREQUENCY_MHZ="$1"
readonly REC_LENGTH_MINUTE="$2"
readonly BITRATE_KBPS="${3:-128}"
OUTPUT_DIR="${4:-.}"
readonly SCHEDULED_RECORDING_NAME="$5"

readonly DATETIME=$(date "+%Y%m%d%H%M")

# ラジオ周波数の指定は必須
if [ "" = "${FREQUENCY_MHZ}" ]; then
    echo "Error : Frequency[MHz] is not specified."
    echo "${DATETIME}" >> debug.txt
    echo "Error : Frequency[MHz] is not specified." >> debug.txt
    exit
fi

# 録音時間の指定は必須
if [ "" = "${REC_LENGTH_MINUTE}" ]; then
    echo "Error : Record length [minute] is not specified."
    echo "${DATETIME}" >> debug.txt
    echo "Error : Record length [minute] is not specified." >> debug.txt
    exit
fi

# 出力ディレクトリの先頭が「~/」の場合は、ホームディレクトリからの相対パス指定であり、ホームディレクトリと結合する。
if [ "~" = "${OUTPUT_DIR}" ]; then
    OUTPUT_DIR="$(echo ~)"
elif [ "~/" = "${OUTPUT_DIR:0:2}" ]; then
    OUTPUT_DIR="$(echo ~)/${OUTPUT_DIR:2}"
fi

# 出力ディレクトリの先頭が「/」でない場合は、ワークディレクトリからの相対パスであり、元々のワークディレクトリと結合する。
if [ "/" != "${OUTPUT_DIR:0:1}" ]; then
    OUTPUT_DIR="${WORK_DIR_ORG}/${OUTPUT_DIR}"
fi

# 出力ディレクトリがない場合は作成する
mkdir -p "${OUTPUT_DIR}"
result=$?
if [ $result -ne 0 ]; then
    echo "Error : mkdir failed."
    echo "${DATETIME}" >> debug.txt
    echo "Error : mkdir failed." >> debug.txt
    exit
fi

# 出力ファイルパスの作成
if [ "" = "${SCHEDULED_RECORDING_NAME}" ]; then
    readonly MP3_FILE_PATH="${OUTPUT_DIR}/${FREQUENCY_MHZ}_${DATETIME}.mp3"
else
    readonly MP3_FILE_PATH="${OUTPUT_DIR}/${SCHEDULED_RECORDING_NAME}_${FREQUENCY_MHZ}_${DATETIME}.mp3"
fi

# 録音時間[秒]
readonly REC_LENGTH_SEC=$(( REC_LENGTH_MINUTE * 60 ))

# ラジオの起動(quiet modeで起動)
python3 ./pymodules/radio_on.py ${FREQUENCY_MHZ} quiet
result=$?
if [ $result -ne 0 ]; then
    echo "Error : Radio could not start."
    echo "${DATETIME}" >> debug.txt
    echo "Error : Radio could not start." >> debug.txt
    exit
fi

# 録音の開始
# デフォルトキャプチャデバイス(=USBオーディオアダプタのマイク端子)に入る音声をmp3に変換する。
ffmpeg -t "${REC_LENGTH_SEC}" \
       -f alsa -i default \
       -vn -ac 2 -ar 44100 -ab "${BITRATE_KBPS}"k -acodec libmp3lame \
       "${MP3_FILE_PATH}" \
       -loglevel error

# ラジオの終了
# 連続録音の場合はラジオ終了しない。
# 5秒待機後、ffmpegのプロセスがあるかで、連続録音か判定。
sleep 5
# ffmpegのプロセスがない場合のみ処理。プロセスがある場合は、別のラジオ録音中なのでラジオ処理なし。
# load済みのmodule-loopbackがない場合のみ処理。ある場合は、ラジオリスニング中なのでラジオ処理なし。
readonly INFO_FFMPEG_PROCESS=$(ps aux | grep [f]fmpeg)
readonly INFO_LOADED_MODULE_LOOPBACK=$(pactl list modules short | grep module-loopback)
if [ "" != "${INFO_FFMPEG_PROCESS}" ]; then
    echo "Now Recording! Skipped Radio-Off."
elif [ "" != "${INFO_LOADED_MODULE_LOOPBACK}" ]; then
    echo "Now Listening! Skipped Radio-Off."
else
    # ラジオの終了(quiet modeで終了)
    python3 ./pymodules/radio_off.py quiet
fi
