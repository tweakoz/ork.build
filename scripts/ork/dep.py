###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, inspect, tarfile
from pathlib import Path
import importlib.util
import ork.path
from ork.command import Command
from ork.deco import Deco
from ork.wget import wget
from ork import pathtools, cmake, make

deco = Deco()

###############################################################################

class Provider:
    """base class for all dependency providers"""
    def __init__(self,options={}):
        self._options = options
        self._node = None
        pass

    #############################
    ## wipe build ?
    #############################

    def should_wipe(self):
        wipe = False
        if "wipe" in self._options:
          wipe = self._options["wipe"]==True
        return wipe

    #############################
    ## force build ?
    #############################

    def force(self):
        force = False
        if "force" in self._options:
          force = self._options["force"]==True
        return force

    #############################
    ## force build ?
    #############################

    def incremental(self):
        incremental = False
        if "incremental" in self._options:
          incremental = self._options["incremental"]==True
        return incremental

    #############################

    def should_build(self):
        no_manifest = (False==self.manifest.exists())
        force = self.force()
        incremental = self.incremental()
        return no_manifest or force or incremental

    #############################

    def provide(self):
      if self.should_wipe():
        self.wipe()
      if self.should_build():
        self.OK = self.build()
      if self.OK:
        self.manifest.touch()
      return self.OK

    #############################

    def _std_cmake_build(self,srcdir,blddir,cmakeEnv):
      ok2build = True
      if self.incremental():
        os.chdir(blddir)
      else:
        pathtools.mkdir(blddir,clean=True)
        pathtools.chdir(blddir)
        cmake_ctx = cmake.context(root=srcdir,env=cmakeEnv)
        ok2build = cmake_ctx.exec()==0
        if ok2build:
          return (make.exec("install")==0)
      return False

    #############################

    def wipe(self):
        pass

    #############################

    def node(self):
        return self._node

    #############################

    def exists(self):
        return False

###############################################################################

class DepNode:
    """dependency provider node"""
    def __init__(self,name=None,options={}):
      assert(isinstance(name,str))
      self.options = options
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
        self.instance = self.module_class(options=options)
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

def require(name_or_list,options={}):
    if(isinstance(name_or_list,str)):
      node = DepNode(name_or_list,options=options)
      node._status = node.provide()
      return node.instance
    elif (isinstance(name_or_list,list)):
      return [DepNode(item,options=options).provide() for item in name_or_list]

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
    build_dest.mkdir()
    if( archive_type=="zip" ):
        os.chdir(str(build_dest))
        Command(["unzip",arcpath]).exec()
    else:
        assert(tarfile.is_tarfile(str(arcpath)))
        tf = tarfile.open(str(arcpath),mode='r:%s'%archive_type)
        tf.extractall(path=str(build_dest))

  return arcpath

###############################################################################
