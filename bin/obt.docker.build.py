#!/usr/bin/env python3

import os, sys, pathlib, argparse
import ork._globals

parser = argparse.ArgumentParser(description='ork.build docker builder')
parser.add_argument('dockername', metavar='D', type=str, help='a dockerimage to build')
parser.add_argument('--force', action="store_true", help='force rebuild' )
parser.add_argument('--wipe', action="store_true", help='wipe and redownload' )
parser.add_argument('--nofetch', action="store_true", help='do not run download/extract/fetch step' )
parser.add_argument('--incremental', action="store_true", help='incremental rebuild' )
parser.add_argument('--serial', action="store_true", help='serial build' )
parser.add_argument('--usegitclone', action="store_true", help='do not use github wget, use github clone for fetching' )
parser.add_argument('--verbose', action="store_true", help='verbose build' )
parser.add_argument('--debug', action="store_true", help='debug build' )

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

dokname = _args["dockername"]

ork._globals.setOption("dockername",dokname)

for item in "force wipe incremental nofetch serial usegitclone verbose debug".split(" "):
  ork._globals.setOption(item,_args[item]==True)

from ork import docker
from ork.deco import Deco
deco = Deco()


print(dokname)

sys.exit(0)