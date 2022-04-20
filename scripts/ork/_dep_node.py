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
from ork import pathtools, cmake, make, path, git, host, _globals, log, buildtrace
import ork._dep_provider
import ork._dep_enumerate
#import ork._dep_x

deco = Deco()
###############################################################################
class DepNode:
    """dependency provider node"""
    def __init__(self,dep_name=None,dep_path=None):
      assert(isinstance(dep_name,str))
      self.miscoptions = _globals.getOptions()
      self.name = dep_name
      self.module_path = dep_path
      self.scrname = ("%s.py"%dep_name)
      #self.module_path = ork.path.deps()/self.scrname
      #print(dep_name,self.module_path)
      self.module_spec = importlib.util.spec_from_file_location(self.name, str(self.module_path))
      self.module = importlib.util.module_from_spec(self.module_spec)
      self.module_spec.loader.exec_module(self.module)
      if(hasattr(self.module,dep_name)):
        assert(hasattr(self.module,dep_name))
        self.module_class = getattr(self.module,dep_name)
       # print(self.module_class)
        assert(inspect.isclass(self.module_class))
        assert(issubclass(self.module_class,ork._dep_provider.Provider))
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
    def nodeForName(cls,named):
      n = _globals.getNode(named)
      if n==None:
        n = cls.FIND(named)
        if n!=None:
          _globals.setNode(named,n)
      return n

    @classmethod
    def ALL(cls):
      ALL_DEPS = dict()
      e = ork._dep_enumerate._enumerate()
      for key in e.keys():
        val = e[key]
        n = DepNode(key,val._fullpath)
        if n and hasattr(n,"instance") and n.instance.supports_host:
          ALL_DEPS[key]=n
      return ALL_DEPS

    @classmethod
    def FIND(cls,named):
      e = ork._dep_enumerate._enumerate()
      n = None
      if named in e.keys():
        val = e[named]
        n = DepNode(named,val._fullpath)
      if n and hasattr(n,"instance") and n.instance.supports_host:
        return n
      return None

###############################################################################
    @classmethod
    def FindWithMethod(cls,named):
      e = ork._dep_enumerate._enumerate()
      rval = {}
      for k in e.keys():
        val = e[k]
        n = DepNode(k,val._fullpath)
        if n and hasattr(n,"instance") and n.instance.supports_host:
          if hasattr(n.instance,named):
            rval[k] = n.instance
      return rval

###############################################################################
# require - returns True if dep(s) succesfully provided, otherwise False
###############################################################################

def require(name_or_list):
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
      inst = DepNode.FIND(item)
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
    inst = DepNode.FIND(name_or_list)
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
    return inst.provide()
   #######################
   # technically, this should never hit..
   #######################
  assert(False)
  return False

