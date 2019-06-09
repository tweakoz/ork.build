#!/usr/bin/env bash

export PLATFORM=arty
export TARGET=base
export CPU=vexriscv
export FIRMWARE=zephyr

source ${OBT_STAGE}/builds/zephyr/zephyr-env.sh
obt.litex.env.py --cpu vexriscv --platform arty --target base --firmware zephyr --shell
