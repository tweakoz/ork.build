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
import obt.subspace
from obt import dep, path
from obt.deco import Deco
deco = Deco()

def print_item(key,val):
 dstr = deco.inf(subspaceid)
 kstr = deco.key(key)
 vstr = deco.val(val)
 print("%s.%s = %s"%(dstr,kstr,vstr))

###############################################################################

parser = argparse.ArgumentParser(description='obt.build subspace builder')
parser.add_argument('subspacemodulename', metavar='S', type=str, help='a subspace module to build')
parser.add_argument('--force', action="store_true", help='force rebuild' )
parser.add_argument('--wipe', action="store_true", help='wipe and rebuild' )
parser.add_argument('--buildargs', action="store", type=str, help='wipe and rebuild' )

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

subspacemodulename = _args["subspacemodulename"]

obt._globals.setOption("subspacemodulename",subspacemodulename)

do_wipe = False
for item in "force wipe".split(" "):
  do_wipe=True

print(subspacemodulename)

subspacemodule = obt.subspace.descriptor(subspacemodulename)

print(subspacemodule)

subspacemodule.build(_args["buildargs"],do_wipe=do_wipe)

sys.exit(0)