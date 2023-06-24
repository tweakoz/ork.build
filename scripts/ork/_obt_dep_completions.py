#!/usr/bin/env python3
##########################################

from ork import dep 
import sys

##########################################
depnodes = dep.DepNode.ALL()
word = sys.argv[-2]
##########################################
for item in depnodes:
    if item.startswith(word):
        print(item)
