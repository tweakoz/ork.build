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
from ork import pathtools, cmake, make, path, git, host, globals
from ork.dep_fetch import *
from ork.dep_build import *
from ork.dep_provider import *
deco = Deco()
###############################################################################

def _get_instance(item):
  if(isinstance(item,str)):
    node = DepNode(item)
    return node.instance
  elif (isinstance(item,DepNode)):
    return item.instance
  elif (isinstance(item,Provider)):
    return item
  else:
    assert(False)

###############################################################################

def _get_node(item):
  if(isinstance(item,str)):
    node = DepNode(item)
    return node
  elif (isinstance(item,DepNode)):
    return item
  else:
    assert(False)

###############################################################################

def instance(name):
  return _get_instance(name)

###############################################################################

def require(name_or_list):
  if (isinstance(name_or_list,list)):
    rval = []
    for item in name_or_list:
      inst = _get_instance(item)
      inst.provide()
      rval += [inst]
  else:
    inst = _get_instance(name_or_list)
    ok = inst.provide()
    if ok:
      rval = inst
    else:
      rval = None
  return rval

###############################################################################

def require_opts(name_or_list,opts):
  if (isinstance(name_or_list,list)):
    rval = []
    globals.options = opts
    for item in name_or_list:
      inst = _get_instance(item)
      inst.provide()
      rval += [inst]
    globals.options = []
  else:
    globals.options = opts
    inst = _get_instance(name_or_list)
    globals.options = []
    ok = inst.provide()
    if ok:
      rval = inst
    else:
      rval = None
  return rval

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

def enumerate():
  deps = ork.pathtools.patglob(ork.path.deps(),"*.py")
  depnames = set()
  depnodes = dict()
  for item in deps:
    d = os.path.basename(item)
    d = os.path.splitext(d)[0]
    depnames.add(d)
    #print(d)
    dn = ork.dep.DepNode(d)
    if dn:
        depnodes[d] = dn
  return depnodes

###############################################################################

def enumerate_with_method(named):
  depnodes = enumerate()
  rval = {}
  for depitemk in depnodes:
    depitem = depnodes[depitemk]
    if hasattr(depitem,"instance"):
      if hasattr(depitem.instance,named):
        rval[depitemk] = depitem.instance
  return rval


###############################################################################

class DepNode:
    """dependency provider node"""
    def __init__(self,name=None):
      assert(isinstance(name,str))
      self.miscoptions = globals.options
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
        assert(issubclass(self.module_class,Provider))
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

###############################################################################

def downloadAndExtract(urls,
                       outname,
                       archive_type,
                       md5val,
                       build_dest):

  arcpath = wget( urls = urls,
                  output_name = outname,
                  md5val = md5val )


  if arcpath:
    if build_dest.exists():
      Command(["rm","-rf",build_dest]).exec()
    print("extracting<%s> to build_dest<%s>"%(deco.path(arcpath),deco.path(build_dest)))
    print(archive_type)
    build_dest.mkdir()
    if( archive_type=="zip" ):
        os.chdir(str(build_dest))
        Command(["unzip",arcpath]).exec()
    elif archive_type=="tgz":
        os.chdir(str(build_dest))
        Command(["tar","xvfz",arcpath]).exec()
    else:
        assert(tarfile.is_tarfile(str(arcpath)))
        tf = tarfile.open(str(arcpath),mode='r:%s'%archive_type)
        tf.extractall(path=str(build_dest))

  return arcpath
