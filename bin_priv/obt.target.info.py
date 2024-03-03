#!/usr/bin/env python3

###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, pathlib, argparse, string
import obt.target
import obt.sdk

parser = argparse.ArgumentParser(description='obt.build target information')
parser.add_argument('target', metavar='T', type=str, help='a target you want information on')

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

targetid = _args["target"]

target_arch = targetid.split('-')[0]
target_os = targetid.split('-')[1]

T = obt.target.descriptor(target_arch,target_os)
SDK = obt.sdk.descriptor(target_arch,target_os)
print(T)
print(SDK)
#SDK = T.sdk  

from obt import dep, path
from obt.deco import Deco
deco = Deco()

target_id = "%s-%s" % (T.architecture,T.os)

def print_item(key,val):
 dstr = deco.inf(target_id)
 kstr = deco.key(key)
 vstr = deco.val(val)
 print("%s.%s = %s"%(dstr,kstr,vstr))

print_item("identifier",T.identifier)
print_item("c_compiler",SDK.c_compiler)
print_item("cxx_compiler",SDK.cxx_compiler)
