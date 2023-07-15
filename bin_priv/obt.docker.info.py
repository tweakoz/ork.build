#!/usr/bin/env python3

###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, pathlib, argparse, string
import obt.docker

parser = argparse.ArgumentParser(description='obt.build docker information')
parser.add_argument('docker', metavar='T', type=str, help='a docker you want information on')

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

dockerid = _args["docker"]

D = obt.docker.descriptor(dockerid)

from obt import dep, path
from obt.deco import Deco
deco = Deco()

def print_item(key,val):
 dstr = deco.inf(dockerid)
 kstr = deco.key(key)
 vstr = deco.val(val)
 print("%s.%s = %s"%(dstr,kstr,vstr))

print_item("info",D.info())
#print_item("c_compiler",SDK.c_compiler)
#print_item("cxx_compiler",SDK.cxx_compiler)
