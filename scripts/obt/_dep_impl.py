###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, tarfile
from pathlib import Path
import importlib.util
import obt.path, obt.host
from obt.command import Command, run
from obt.deco import Deco
from obt.wget import wget
from obt import pathtools, cmake, make, path, git, host, buildtrace
import obt._dep_enumerate

deco = Deco()

###############################################################################

def switch(linux=None,macos=None):
  if host.IsOsx:
    if macos==None:
      assert(False) # dep not supported on platform
    return macos
  elif host.IsIx:
    if linux==None:
      assert(False) # dep not supported on platform
    return linux
  else:
   return linux


###############################################################################
# require - returns True if dep(s) succesfully provided, otherwise False
###############################################################################

def require(name_or_list):
  from obt import _dep_node
  ######################################
  # list of dependencies?
  ######################################
  with buildtrace.NestedBuildTrace({ "op": "dep.require(%s)"%str(name_or_list)}) as nested:
   if (isinstance(name_or_list,list)):
    ######################
    # empty list ? 
    ######################
    if not name_or_list:
      return True # no deps, requirements met..
    ######################
    for item in name_or_list:
      #print(item)

      inst = _dep_node.DepNode.FIND(item)
      if inst==None:
        deconame = deco.orange(item)
        print(deco.red("dep not found>> %s"%deconame))
        return False
      rval = inst.provide()
      ######################
      # a dep failed....
      ######################
      if not rval:
        return False
    ######################
    # all deps must be met!
    ######################
    return True
   ######################################
   # single dependency (string) ?
   ######################################
   else:
    inst = _dep_node.DepNode.FIND(name_or_list)
    #######################
    ## dep not found...
    #######################
    if inst==None:
      deconame = deco.orange(name_or_list)
      print(deco.red("dep not found>> %s"%deconame))
      return False
    #######################
    ## dep was found, is it provided ?
    #######################
    OK = inst.provide()
    return inst.instance if OK else None
   #######################
   # technically, this should never hit..
   #######################
  assert(False)
  return False

