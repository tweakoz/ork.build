#!/usr/bin/env python3

###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, pathlib, argparse, string
import obt._globals
import obt.docker
from obt import dep, path
from obt.deco import Deco
deco = Deco()

def print_item(key,val):
 dstr = deco.inf(dockerid)
 kstr = deco.key(key)
 vstr = deco.val(val)
 print("%s.%s = %s"%(dstr,kstr,vstr))

###############################################################################

parser = argparse.ArgumentParser(description='obt.build docker builder')
parser.add_argument('dockermodulename', metavar='D', type=str, help='a docker module to build')
parser.add_argument('--force', action="store_true", help='force rebuild' )
parser.add_argument('--wipe', action="store_true", help='wipe and rebuild' )
parser.add_argument('--buildargs', nargs=argparse.REMAINDER, help='pass arguments to the inferior' )

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

dockermodulename = _args["dockermodulename"]

obt._globals.setOption("dockermodulename",dockermodulename)

for item in "force wipe".split(" "):
  obt._globals.setOption(item,_args[item]==True)

print(dockermodulename)

dockermodule = obt.docker.descriptor(dockermodulename)

print(dockermodule)

build_args = []
if "buildargs" in _args and _args["buildargs"]!=None:
  build_args = _args["buildargs"]

dockermodule.build(build_args)

sys.exit(0)