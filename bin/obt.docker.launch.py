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
import ork.docker
from ork import dep, path
from ork.deco import Deco
deco = Deco()

def print_item(key,val):
 dstr = deco.inf(dockerid)
 kstr = deco.key(key)
 vstr = deco.val(val)
 print("%s.%s = %s"%(dstr,kstr,vstr))

###############################################################################

parser = argparse.ArgumentParser(description='ork.build docker launcher')
parser.add_argument('dockermodulename', metavar='D', type=str, help='a docker module to launch')

args, unknownargs = parser.parse_known_args()

_args = vars(args)

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

dockermodulename = _args["dockermodulename"]

ork._globals.setOption("dockermodulename",dockermodulename)

dockermodule = ork.docker.descriptor(dockermodulename)

print(dockermodule)

dockermodule.launch(unknownargs)

sys.exit(0)