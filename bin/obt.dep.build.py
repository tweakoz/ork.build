#!/usr/bin/env python3

import os, sys, pathlib, argparse
import ork._globals

parser = argparse.ArgumentParser(description='ork.build dep builder')
parser.add_argument('dependency', metavar='D', type=str, help='a dependency to build')
parser.add_argument('--force', action="store_true", help='force rebuild' )
parser.add_argument('--wipe', action="store_true", help='wipe and redownload' )
parser.add_argument('--nofetch', action="store_true", help='do not run download/extract/fetch step' )
parser.add_argument('--incremental', action="store_true", help='incremental rebuild' )
parser.add_argument('--serial', action="store_true", help='serial build' )
parser.add_argument('--usegitclone', action="store_true", help='do not use github wget, use github clone for fetching' )
parser.add_argument('--verbose', action="store_true", help='verbose build' )
parser.add_argument('--debug', action="store_true", help='debug build' )

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

depname = _args["dependency"]

ork._globals.setOption("depname",depname)

for item in "force wipe incremental nofetch serial usegitclone verbose debug".split(" "):
  ork._globals.setOption(item,_args[item]==True)

from ork import dep
from ork.deco import Deco
deco = Deco()

subspace = os.environ["OBT_SUBSPACE"]
node = dep.instance(depname)
if not node.allowed_in_subspace(subspace):
   print( "Dependency '%s' not allowed to be built in subspaces other than %s"%(depname,node._allowed_subspaces))
   sys.exit(-1)

chain = dep.Chain(depname)

print(chain)
for item in reversed(chain._list):
  name = deco.key("%s"%(item._name))
  should = item.supports_host and item.should_build
  print("dep<%s> ShouldBuild<%s>"%(name,deco.val("%s"%should)))
  ret = True
  if should:
    ret = item.provide()
  
  if not ret:
  	print(deco.red("Dependency Failed! : %s ret<%s>"%(name,ret)))
  	sys.exit(-1)
#print("dep<%s> returned<%s>"%(depname,status))
sys.exit(0)