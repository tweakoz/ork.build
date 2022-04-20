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
from ork import pathtools, cmake, make, path, git, host, _globals
import ork._dok_enumerate
#import ork._dep_x

deco = Deco()
###############################################################################
class DockerNode:
    """docker provider node"""
    @classmethod
    def ALL(cls):
      ALL_DOKS = dict()
      e = ork._dok_enumerate._enumerate()
      #for key in e.keys():
      #  val = e[key]
      #  n = DockerNode(key,val._fullpath)
      #  if n and hasattr(n,"instance") and n.instance.supports_host:
      #    ALL_DOKS[key]=n
      return e #ALL_DOKS

    def __init__(self,dep_name=None,dep_path=None):
      assert(isinstance(dep_name,str))
      self.miscoptions = _globals.getOptions()
