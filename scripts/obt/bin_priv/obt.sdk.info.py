#!/usr/bin/env python3

###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, pathlib, argparse, string
import obt.sdk

parser = argparse.ArgumentParser(description='obt.build sdk information')
parser.add_argument('sdk', metavar='S', type=str, help='a sdk you want information on')

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

sdkid = _args["sdk"]

target_arch = sdkid.split('-')[0]
target_os = sdkid.split('-')[1]

S = obt.sdk.descriptor(target_arch,target_os)

if S==None:
  print("SDK not supported on hosts")
  sys.exit(-1)

from obt import dep, path
from obt.deco import Deco
deco = Deco()

sdkid = "%s-%s" % (S.architecture,S.os)

def print_item(key,val):
 dstr = deco.inf(sdkid)
 kstr = deco.key(key)
 vstr = deco.val(val)
 print("%s.%s = %s"%(dstr,kstr,vstr))

print_item("identifier",S.identifier)
print_item("c_compiler",S.c_compiler)
print_item("cxx_compiler",S.cxx_compiler)
print_item("supports host",S.supports_host)
print_item("misc",S.misc())
#print_item("sdkdir",S.sdkdir)
