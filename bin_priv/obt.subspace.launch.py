#!/usr/bin/env python3

###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, pathlib, argparse, string
import ork._globals
import ork.subspace
from ork import dep, path
from ork.deco import Deco
deco = Deco()

###############################################################################

parser = argparse.ArgumentParser(description='ork.build subspace launcher')
parser.add_argument('subspacemodulename', metavar='S', type=str, help='a subspace module to launch')
parser.add_argument('--launchargs', action="store", type=str, help='launch arguments' )

args, unknownargs = parser.parse_known_args()

_args = vars(args)

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

subspacemodulename = _args["subspacemodulename"]

ork._globals.setOption("subspacemodulename",subspacemodulename)

subspacemodule = ork.subspace.requires(subspacemodulename)

print("unknownargs: %s"%unknownargs)
if len(unknownargs)==0:
    subspacemodule.shell()
else:
    subspacemodule.launch(unknownargs)

sys.exit(0)