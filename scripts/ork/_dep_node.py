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
from ork import _dep_provider
###############################################################################
class DepNode:
    """dependency provider node"""
    def __init__(self,name=None):
      assert(isinstance(name,str))
      self.miscoptions = _globals.options
      self.name = name
      self.scrname = ("%s.py"%name)
      self.module_path = ork.path.deps()/self.scrname
      self.module_spec = importlib.util.spec_from_file_location(self.name, str(self.module_path))
      self.module = importlib.util.module_from_spec(self.module_spec)
      #print(name,dir(self.module))
      self.module_spec.loader.exec_module(self.module)
      if(hasattr(self.module,name)):
        assert(hasattr(self.module,name))
        self.module_class = getattr(self.module,name)
        assert(inspect.isclass(self.module_class))
        assert(issubclass(self.module_class,_dep_provider.Provider))
        self.instance = self.module_class()
        self.instance._node = self

    ## string descriptor of dependency

    def __str__(self):
      return str(self.instance) if hasattr(self,"instance") else "???"

    ## provider method

    def provide(self):
      #print(self.instance)
      if self.instance.exists():
        provide = self.instance.provide()
        assert(provide==True)
        return provide
      else:
        provide = self.instance.provide()
        assert(provide==True)
        return provide
