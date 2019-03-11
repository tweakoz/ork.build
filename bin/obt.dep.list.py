#!/usr/bin/env python3

import os, sys, pathlib, argparse
from ork import dep, host, path
import ork.pathtools

##########################################
# build dep dict
##########################################

deps = ork.pathtools.patglob(ork.path.deps(),"*.py")

depnames = set()
depnodes = dict()
for item in deps:
	d = os.path.basename(item)
	d = os.path.splitext(d)[0]
	depnames.add(d)
	#print(d)
	dn = ork.dep.DepNode(d)
	if dn:
		depnodes[d] = dn

##########################################

import ork.deco
deco = ork.deco.Deco()

line_index = 0
for key in sorted(depnodes):
	odd = line_index&1
	val = str(depnodes[key])
	if val!="???":
	  col_k = deco.rgbstr(255,255,0,key) if odd else deco.rgbstr(192,192,0,key)
	  col_v = deco.rgbstr(255,255,255,val) if odd else deco.rgbstr(192,192,192,val)
	  line = "%27s" % col_k
	  line += " " + deco.magenta(":") + " "
	  line += col_v
	  print(line)
	  line_index += 1

