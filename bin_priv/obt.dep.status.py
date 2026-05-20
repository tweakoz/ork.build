#!/usr/bin/env python3

###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, sys, pathlib, argparse, string

parser = argparse.ArgumentParser(description='obt.build dep builder')
parser.add_argument('dependency', metavar='D', type=str, help='a dependency to build')

_args = vars(parser.parse_args())

if len(sys.argv)==1:
    print(parser.format_usage())
    sys.exit(1)

depname = _args["dependency"]

from obt import dep, path
from obt.deco import Deco
deco = Deco()

chain = dep.Chain(depname)

###############################################################################
# Priority-aware topological build order (deps-first / leaves-first).
#
# Kahn's algorithm: repeatedly emit a node whose prereqs are all already
# emitted; among the currently-ready frontier, emit highest build_priority
# first (ties broken by topo index). This mirrors how the parallel
# pipeline scheduler dispatches — so the listing reflects the order deps
# would actually build. It is an approximation: the live scheduler's order
# also shifts with build-slot contention and fetch timing, which a static
# listing can't model.
###############################################################################
def _build_order(chain):
  providers = list(chain._list)
  by_name   = chain._dict
  indeg     = {}
  dependents = {}
  for p in providers:
    prereqs = [d._name for d in p._required_deps.values()
               if d is not None and d._name in by_name]
    indeg[p._name] = len(prereqs)
    for pre in prereqs:
      dependents.setdefault(pre, []).append(p._name)
  ready = [p for p in providers if indeg[p._name] == 0]
  order = []
  while ready:
    # highest build_priority first; stable tie-break on topo index
    ready.sort(key=lambda p: (-getattr(p, "build_priority", 0), p._topoindex))
    p = ready.pop(0)
    order.append(p)
    for dn in dependents.get(p._name, []):
      indeg[dn] -= 1
      if indeg[dn] == 0:
        ready.append(by_name[dn])
  return order

def genline(dep,scope,sup,man,spres,bpres,srcr):
  line = "%-40s" % dep
  line += "%24s" % scope
  line += "%24s" % sup
  line += "%28s" % man
  line += "%28s" % spres
  line += "%28s" % bpres
  line += "%60s" % srcr
  return line

def separator():
  print(deco.inf("#########################################################################################################################################"))

separator()
print(genline(deco.white("Dependency(BuildOrder)"),
            deco.val("Scope"),
	          deco.val("Supported"),
	          deco.val("Manifest"),
	          deco.val("SrcPresent"),
	          deco.val("BinPresent"),
	          deco.path("SourceRoot")))
separator()
index = 0
for item in _build_order(chain):
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

  scope = str(item.scope).split('.')[1]
  scope = deco.val(scope)

  print(genline(name,scope,sup,man,spres,bpres,srcr))
  index+=1

separator()
