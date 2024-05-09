#!/usr/bin/env python3
##########################################

from obt import subspace 
import sys

##########################################
subspaces = subspace.enumerate()
word = sys.argv[-2]
##########################################
for item in subspaces:
    if item.startswith(word):
        print(item[:-3])
