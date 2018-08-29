#!/usr/bin/env python3

import os, sys, pathlib, argparse
from ork import dep, host, path

parser = argparse.ArgumentParser(description='ork.build dep build')
parser.add_argument('--force', action="store_true", help='force build' )
parser.add_argument('dep' )

args = vars(parser.parse_args())

if len(sys.argv)==1 or args["dep"]==None:
    print(parser.format_usage())
    sys.exit(1)

opts = {}
if args["force"]:
	opts["force"]=True
dep.require(args["dep"],options=opts)

