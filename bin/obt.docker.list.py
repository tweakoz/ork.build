#!/usr/bin/env python3

import os, sys, pathlib, argparse
from ork import docker, host, path
import ork.pathtools
import ork._globals

##########################################
# build dep dict
##########################################

dockernodes = ork.docker.DockerNode.ALL()

##########################################

import ork.deco
deco = ork.deco.Deco()

line_index = 0
for key in sorted(dockernodes):
	odd = line_index&1
	val = str(dockernodes[key])
	if val!="???":
	  col_k = deco.rgbstr(255,255,0,key) if odd else deco.rgbstr(192,192,0,key)
	  col_v = deco.rgbstr(255,255,255,val) if odd else deco.rgbstr(192,192,192,val)
	  line = "%27s" % col_k
	  line += " " + deco.magenta(":") + " "
	  line += col_v
	  print(line)
	  line_index += 1
