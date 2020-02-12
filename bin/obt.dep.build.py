#!/usr/bin/env python3

import os, sys, pathlib, argparse
from ork import dep, host, path

parser = argparse.ArgumentParser(description='ork.build dep builder')
parser.add_argument('dependency', metavar='D', type=str, help='a dependency to build')
parser.add_argument('--force', action="store_true", help='force rebuild' )
parser.add_argument('--wipe', action="store_true", help='wipe and redownload' )
parser.add_argument('--incremental', action="store_true", help='incremental rebuild' )

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

_options = {
    "force": (_args["force"]==True),
    "wipe": (_args["wipe"]==True),
    "incremental": (_args["incremental"]==True)
}

dep.require(_args["dependency"],options=_options)
