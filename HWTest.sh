#!/bin/sh

export SDL_AUDIODRIVER=dsp
export SDL_NOMOUSE=1
export HOME=/mnt/int_sd
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$HOME/local/python/usr/lib
export PATH=$PATH:$HOME/local/python/usr/bin

cd "$(dirname "$0")"

python hardware_test.py >> $HOME/log

