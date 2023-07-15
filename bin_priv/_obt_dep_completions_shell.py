#!/usr/bin/env python3
##########################################

from obt import dep 
import sys

##########################################
depnodes = dep.DepNode.ALL()
word = sys.argv[-2]
##########################################
for key in depnodes:
    if key.startswith(word):
        val = depnodes[key]
        if hasattr(val.instance,"on_build_shell") and val.instance.supports_host:
            print(key)
