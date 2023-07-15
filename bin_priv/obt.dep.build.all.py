#!/usr/bin/env python3

from obt.command import Command

items =  ["yarl","pkgconfig","boost","luajit","gcode_gpr","postgresql"]
items += ["avr_binutils","avr_gcc","avr_libc","simavr"]
items += ["lm32_binutils","lm32_gcc"]

assert(os.environ["OBT_SUBSPACE"]=="host")

for item in items:
	Command(["obt.dep.require.py",item]).exec()
