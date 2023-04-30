#!/usr/bin/env python3

import os, sys, pathlib, argparse
from ork import dep, host, path
import ork.pathtools
import ork._globals

##########################################
# build dep dict
##########################################

depnodes = ork.dep.DepNode.ALL()

##########################################

import ork.deco
deco = ork.deco.Deco()
subspace = os.environ["OBT_SUBSPACE"]

line_index = 0
for key in sorted(depnodes):
	odd = line_index&1
	node = depnodes[key]
	depname = str(node)
	node = node.instance
	if node and node.allowed_in_subspace(subspace):
	  col_k = deco.rgbstr(255,255,0,key) if odd else deco.rgbstr(192,192,0,key)
	  col_v = deco.rgbstr(255,255,255,depname) if odd else deco.rgbstr(192,192,192,depname)
	  line = "%27s" % col_k
	  line += " " + deco.magenta(":") + " "
	  line += col_v
	  print(line)
	  line_index += 1
