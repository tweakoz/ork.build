#!/usr/bin/env python3

import os, sys, pathlib, argparse
from obt import dep, host, path

if len(sys.argv)==2:
	dep.require(sys.argv[1])
else:
    print( "usage: dep.require.py <depname>")
    sys.exit(1)
