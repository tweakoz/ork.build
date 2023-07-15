#!/usr/bin/env python3

###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, pathlib, argparse, string

assert(os.environ["OBT_SUBSPACE"]=="host")

parser = argparse.ArgumentParser(description='obt.build dep information')
parser.add_argument('dependency', metavar='D', type=str, help='a dependency you want information on')

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

depname = _args["dependency"]

from obt import dep, path
from obt.deco import Deco
deco = Deco()

instance = dep.instance(depname)


def print_item(key,val):
 dstr = deco.inf(depname)
 kstr = deco.key(key)
 vstr = deco.val(val)
 print("%s.%s = %s"%(dstr,kstr,vstr))

src_present = str(instance.areRequiredSourceFilesPresent())
if src_present=="None":
   src_present = "False"

bin_present = str(instance.areRequiredBinaryFilesPresent())
if bin_present=="None":
   bin_present = "False"

decl_deps = list()
for dep_name in instance._required_deps.keys():
  dep_inst = instance._required_deps[dep_name]
  decl_deps += [dep_name]

print_item("name",instance._name)
print_item("scope",instance.scopestr)
print_item("manifest present",instance.exists)
print_item("source present",src_present)
print_item("binaries present",bin_present)
print_item("architectures",instance._archlist)
print_item("declared deps",decl_deps)

print_item("source root",instance.source_root)
print_item("build_src",instance.build_src)
print_item("build_dest",instance.build_dest)

