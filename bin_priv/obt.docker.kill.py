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

parser = argparse.ArgumentParser(description='obt.build docker killer')
parser.add_argument('dockermodulename', metavar='D', type=str, help='a docker module to kill')

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

dockermodulename = _args["dockermodulename"]

obt._globals.setOption("dockermodulename",dockermodulename)

dockermodule = obt.docker.descriptor(dockermodulename)

print(dockermodule)

dockermodule.kill()

sys.exit(0)