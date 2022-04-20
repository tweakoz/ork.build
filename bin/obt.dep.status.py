#!/usr/bin/env python3

import os, sys, pathlib, argparse, string

parser = argparse.ArgumentParser(description='ork.build dep builder')
parser.add_argument('dependency', metavar='D', type=str, help='a dependency to build')

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

depname = _args["dependency"]

from ork import dep, path
from ork.deco import Deco
deco = Deco()

chain = dep.Chain(depname)

def genline(dep,sup,man,spres,bpres,srcr):
  line = "%-40s" % dep
  line += "%24s" % sup
  line += "%28s" % man
  line += "%28s" % spres
  line += "%28s" % bpres
  line += "%60s" % srcr
  return line

print(deco.inf("############################################################################################################################"))
print(genline(deco.white("Dependency(RevTopoOrder)"),
	          deco.val("Supported"),
	          deco.val("Manifest"),
	          deco.val("SrcPresent"),
	          deco.val("BinPresent"),
	          deco.path("SourceRoot")))
print(deco.inf("############################################################################################################################"))
index = 0
for item in chain._list:
  should = item.should_build
  colorize_name = deco.red if should else deco.white
  name = colorize_name("%d. %s"%(index,item._name))
  sup = deco.val(item.supports_host)
  man = deco.val(item.manifest.exists())

  src_present = str(item.areRequiredSourceFilesPresent())
  if src_present=="None":
     src_present = "----"
  spres = deco.val(src_present)

  bin_present = str(item.areRequiredBinaryFilesPresent())
  if bin_present=="None":
     bin_present = "----"
  bpres = deco.val(bin_present)

  srcroot = str(item.source_root).replace(str(path.builds()),"${OBT_BUILDS}")
  srcr = deco.path(srcroot)
  print(genline(name,sup,man,spres,bpres,srcr))
  index+=1
print(deco.inf("############################################################################################################################"))
