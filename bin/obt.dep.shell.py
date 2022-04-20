#!/usr/bin/env python3

import os, sys, pathlib, argparse
from ork import dep, host, path
import ork._globals
import ork.deco
deco = ork.deco.Deco()

parser = argparse.ArgumentParser(description='ork.build dep build shell')
parser.add_argument('dependency', metavar='D', type=str, help='a dependency to build')

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

depname = _args["dependency"]
DEP = dep.instance(depname)
if DEP==None:
   print(deco.red("Dep<%s> not found!"%depname))
   sys.exit(0)

if not hasattr(DEP,"on_build_shell"):
   print(deco.red("Dep<%s> does not support on_build_shell!"%depname))
   sys.exit(0)

print(deco.bright("Entering build shell for Dep<%s>! just exit to return here"%depname))

retc = DEP.on_build_shell()
if retc==None:
  retc = 0

sys.exit(retc)
