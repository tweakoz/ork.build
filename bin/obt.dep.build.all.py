#!/usr/bin/env python3

from ork.command import Command

items =  ["yarl","pkgconfig","boost","luajit","gcode_gpr","postgresql"]
items += ["avr_binutils","avr_gcc","avr_libc","simavr"]
items += ["lm32_binutils","lm32_gcc"]

for item in items:
	Command(["obt.dep.require.py",item]).exec()
