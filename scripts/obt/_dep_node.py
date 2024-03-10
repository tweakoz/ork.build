###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
import os, inspect, tarfile, sys
from pathlib import Path
import importlib.util
import obt.path, obt.host
from obt.command import Command, run
from obt.deco import Deco
from obt.wget import wget
from obt import pathtools, cmake, make, path, git, host, _globals, log, buildtrace
import obt._dep_provider
import obt._dep_enumerate
#import obt._dep_x

deco = Deco()
def module_of_class(clazz):
   return sys.modules[clazz.__module__].__file__

###############################################################################
class DepNode:
    """dependency provider node"""
    def __init__(self,dep_name=None,dep_path=None,with_overrides=True):
      assert(isinstance(dep_name,str))
      self.miscoptions = _globals.getOptions()
      self.name = dep_name
      self.module_path = dep_path
      self.modules_base = Path(obt.path.obt_modules_base()).resolve()
      self.scrname = ("%s.py"%dep_name)
      self.module_spec = importlib.util.spec_from_file_location(self.name, str(self.module_path))
      self.module = importlib.util.module_from_spec(self.module_spec)
      self.module_spec.loader.exec_module(self.module)
      if(hasattr(self.module,dep_name)):
        assert(hasattr(self.module,dep_name))
        self.module_class = getattr(self.module,dep_name)
        #print(self.module_class)
        assert(inspect.isclass(self.module_class))
        assert(issubclass(self.module_class,obt._dep_provider.Provider))
        ##########################################################
        # check for override class in <staging>/"dep-overrides"
        ##########################################################
        override_path = path.stage()/"dep-overrides"/self.scrname
        if with_overrides and override_path.exists():
          self.module_path = override_path
          self.module_spec = importlib.util.spec_from_file_location(self.name, str(self.module_path))
          self.module = importlib.util.module_from_spec(self.module_spec)
          self.module_spec.loader.exec_module(self.module)
          if(hasattr(self.module,dep_name)):
            override_class = getattr(self.module,dep_name)
            assert(inspect.isclass(override_class))
            #print(module_of_class(self.module_class))
            #print(module_of_class(override_class))
            #assert(issubclass(override_class,self.module_class))
            self.module_class = override_class
        ##########################################################
        #print(dep_name)
        self.instance = self.module_class()
        self.instance._node = self
    ## string descriptor of dependency

    def __str__(self):
      return str(self.instance) if hasattr(self,"instance") else "???"

    ## provider method

    def provide(self):
      #print(self,self.name,self.module_path,self.module,self.module_class)
      #print(self.instance)
      if self.instance.exists:
        provide = self.instance.provide()
        assert(provide==True)
        return provide
      else:
        provide = self.instance.provide()
        return provide

    @classmethod
    def nodeForName(cls,named,with_overrides=True):
      n = _globals.getNode(named)
      if n==None:
        n = cls.FIND(named,with_overrides)
        if n!=None:
          _globals.setNode(named,n)
      return n

    @classmethod
    def ALL(cls,with_overrides=True):
      ALL_DEPS = dict()
      e = obt._dep_enumerate._enumerate()
      for key in e.keys():
        val = e[key]
        n = DepNode(key,val._fullpath,with_overrides)
        if n and hasattr(n,"instance") and n.instance.supports_host:
          ALL_DEPS[key]=n
      return ALL_DEPS

    @classmethod
    def FIND(cls,named,with_overrides=True):
      e = obt._dep_enumerate._enumerate()
      n = None
      if named in e.keys():
        val = e[named]
        n = DepNode(named,val._fullpath,with_overrides)
      if n and hasattr(n,"instance") and n.instance.supports_host:
        return n
      return None

###############################################################################
    @classmethod
    def FindWithMethod(cls,named):
      e = obt._dep_enumerate._enumerate()
      rval = {}
      for k in e.keys():
        val = e[k]
        #print(val._fullpath)
        n = DepNode(k,val._fullpath)
        if n and hasattr(n,"instance") and n.instance.supports_host:
          if hasattr(n.instance,named):
            rval[k] = n.instance
      return rval

