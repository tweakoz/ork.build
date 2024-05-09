#!/usr/bin/env python3

import os, sys, pathlib, argparse
from obt import docker, host, path
import obt.pathtools
import obt._globals

##########################################
# build dep dict
##########################################

dockermodules = docker.enumerate()

##########################################

import obt.deco
deco = obt.deco.Deco()

#print(dockermodules)

line_index = 0
for key in dockermodules:
	odd = line_index&1
	val = str(dockermodules[key]._module.info())
	if val!="???":
	  col_k = deco.rgbstr(255,255,0,key) if odd else deco.rgbstr(192,192,0,key)
	  col_v = deco.rgbstr(255,255,255,val) if odd else deco.rgbstr(192,192,192,val)
	  line = "%27s" % col_k
	  line += " " + deco.magenta(":") + " "
	  line += col_v
	  print(line)
	  line_index += 1
