#!/usr/bin/env python3

import os, sys, pathlib, argparse
from ork import dep, host, path

parser = argparse.ArgumentParser(description='ork.build dep builder')
parser.add_argument('dependency', metavar='D', type=str, help='a dependency to build')
parser.add_argument('--force', action="store_true", help='force rebuild' )
parser.add_argument('--wipe', action="store_true", help='wipe and redownload' )
parser.add_argument('--nofetch', action="store_true", help='do not run download/extract/fetch step' )
parser.add_argument('--incremental', action="store_true", help='incremental rebuild' )
parser.add_argument('--serial', action="store_true", help='serial build' )

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

_options = {
    "force": (_args["force"]==True),
    "wipe": (_args["wipe"]==True),
    "incremental": (_args["incremental"]==True),
    "nofetch": (_args["nofetch"]==True),
    "serial": (_args["serial"]==True)
}

dep.require(_args["dependency"],miscoptions=_options)
