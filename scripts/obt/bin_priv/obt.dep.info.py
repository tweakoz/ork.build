#!/usr/bin/env python3

###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, pathlib, argparse, string

#assert(os.environ["OBT_SUBSPACE"]=="host")

parser = argparse.ArgumentParser(description='obt.build dep information')
parser.add_argument('dependency', metavar='D', type=str, help='a dependency you want information on')

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

depname = _args["dependency"]

from obt import dep, path, pathtools
from obt.deco import Deco
deco = Deco()

instance = dep.instance(depname)

if instance==None:
   print("no available dependency %s for this host/target"%depname)
   sys.exit(1)

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

subspace_VIF = instance._subspace_vif

print_item("name",instance._name)
print_item("provider_path",instance._node.module_path)
print_item("has_shell",hasattr(instance,"on_build_shell"))
print_item("has_envinit",hasattr(instance,"env_init"))
print()
#############################################################
if hasattr(instance,"github_repo"):
   print_item("github_repo",instance.github_repo)
if hasattr(instance,"revision"):
   print_item("revision",instance.revision)
#############################################################
if hasattr(instance,"download_URL"):
   print_item("download_URL",instance.download_URL)
if hasattr(instance,"download_MD5"):
   print_item("download_MD5",instance.download_MD5)
#############################################################
print()
print_item("scope",instance.scopestr)
print_item("manifest path",instance.manifest)
print_item("manifest present",instance.manifest.exists())
print_item("source present",src_present)
print_item("binaries present",bin_present)
print_item("os", "All" if (instance._oslist==None) else instance._oslist)
print_item("architectures", "All" if (instance._archlist==None) else instance._archlist)
print_item("declared deps",decl_deps)
print_item("subspace_VIF",subspace_VIF)
print()
#############################################################
if subspace_VIF==2:
  if hasattr(instance,"_conanfile"):
     print_item("conanfile",instance._conanfile)
  if hasattr(instance,"_conan_build"):
     print_item("conan_build",instance._conan_build)
#############################################################
print_item("source root",instance.source_root)
print_item("build_src",instance.build_src)
if instance.build_src.exists():
  print_item("build_src size: ","%0.2f (MiB)"%(pathtools.sizeOfDirectory(instance.build_src)/1048576.0))

print_item("build_dest",instance.build_dest)

if instance.build_dest.exists():
  print_item("build_dest size: ","%0.2f (MiB)"%(pathtools.sizeOfDirectory(instance.build_dest)/1048576.0))
#############################################################


