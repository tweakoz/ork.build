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
import ork.path, ork.host
from ork.command import Command, run
from ork.deco import Deco
from ork.wget import wget
from ork import pathtools, cmake, make, path, git, host

###############################################################################
def _enumerate():
  #######################################
  class EnumItem:
    def __init__(self,name,fullpath):
      self._name = name 
      self._fullpath = fullpath
  #######################################
  doks = dict()
  dep_search_list = os.environ["OBT_DEP_PATH"].split(":")
  #print(dep_search_list)
  for _dep_search_path in dep_search_list:
    dok_path = path.Path(_dep_search_path)/".."/"dockers"
    print(dok_path)
    dok_list = ork.pathtools.recursive_glob_get_dirs(dok_path)
    print(dok_list)
    for item in dok_list:
      d = os.path.basename(item)
      #d = os.path.splitext(d)[0]
      #_dir = os.path.splitext(item)[0]
      print(d)#,_dir,item)
      #e = EnumItem(d,item)
      #if e._node and hasattr(e._node,"instance") and e._node.instance.supports_host:
      doks[d] = e

  #######################################
 # print(deps)
  return doks

#_ALL_DEPS = _enumerate()

###############################################################################
