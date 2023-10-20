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
from obt import pathtools, cmake, make, path, git, host

###############################################################################
def _enumerate():
  #######################################
  class EnumItem:
    def __init__(self,name,fullpath):
      self._name = name 
      self._fullpath = fullpath
  #######################################
  deps = dict()
  dep_search_list = os.environ["OBT_MODULES_PATH"].split(":")
  #print(dep_search_list)
  for modules_repo in dep_search_list:
    dep_repo = obt.path.Path(modules_repo)/"dep"
    dep_list = obt.pathtools.patglob(dep_repo,"*.py")
    for item in dep_list:
      d = os.path.basename(item)
      d = os.path.splitext(d)[0]
      _dir = os.path.splitext(item)[0]
      #print(d,_dir,item)
      e = EnumItem(d,item)
      #if e._node and hasattr(e._node,"instance") and e._node.instance.supports_host:
      deps[d] = e

  #######################################
  return deps

#_ALL_DEPS = _enumerate()

###############################################################################
