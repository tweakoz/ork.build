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
import ork.path
from ork.command import Command
from ork.deco import Deco
from ork.wget import wget
from ork import pathtools, cmake, make, path, git

deco = Deco()

###############################################################################

def require(name_or_list,miscoptions={}):
    if(isinstance(name_or_list,str)):
      node = DepNode(name_or_list,miscoptions=miscoptions)
      node._status = node.provide()
      return node.instance
    elif (isinstance(name_or_list,list)):
      return [DepNode(item,miscoptions=miscoptions).provide() for item in name_or_list]

###############################################################################

class Provider:
    """base class for all dependency providers"""
    def __init__(self,miscoptions={}):
        self._miscoptions = miscoptions
        self._node = None
        pass

    #############################
    ## wipe build ?
    #############################

    def should_wipe(self):
        wipe = False
        if "wipe" in self._miscoptions:
          wipe = self._miscoptions["wipe"]==True
        return wipe

    #############################
    ## serial build ?
    #############################

    def should_serial_build(self):
        serial = False
        if "serial" in self._miscoptions:
          serial = self._miscoptions["serial"]==True
        return serial

    def default_parallelism(self):
      parallelism = 1.0
      if self.should_serial_build():
        parallelism=0.0
      return parallelism

    #############################
    ## force build ?
    #############################

    def force(self):
        force = False
        if "force" in self._miscoptions:
          force = self._miscoptions["force"]==True
        return force

    #############################
    ## force build ?
    #############################

    def incremental(self):
        incremental = False
        if "incremental" in self._miscoptions:
          incremental = self._miscoptions["incremental"]==True
        return incremental

    #############################

    def should_build(self):
        no_manifest = (False==self.manifest.exists())
        force = self.force()
        incremental = self.incremental()
        return no_manifest or force or incremental

    #############################

    def should_fetch(self):
        fetch = False
        if "nofetch" in self._miscoptions:
          fetch = self._miscoptions["nofetch"]==False
        return fetch

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

    def _std_cmake_vars():
      cmakeEnv = {
        "CMAKE_BUILD_TYPE": "Release",
        "BUILD_SHARED_LIBS": "ON",
      }
      return cmakeEnv

    #############################

    def _std_cmake_build(self,srcdir,blddir,cmakeEnv=_std_cmake_vars(),parallelism=1.0):
      ok2build = True
      if self.incremental():
        os.chdir(blddir)
      else:
        pathtools.mkdir(blddir,clean=True)
        pathtools.chdir(blddir)
        cmake_ctx = cmake.context(root=srcdir,env=cmakeEnv)
        ok2build = cmake_ctx.exec()==0
      if ok2build:
        return (make.exec("install",parallelism=parallelism)==0)
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

class GitFetcher:
  ###########################################
  def __init__(self,name):
    self._name = name
    self._git_url = ""
    self._revision = ""
    self._recursive = False
    self._cache = True
  ###########################################
  def descriptor(self):
    return "%s (git-%s)" % (self._name,self._revision)
  ###########################################
  def fetch(self,dest):
    git.Clone(self._git_url,dest,self._revision,recursive=self._recursive,cache=self._cache)
  ###########################################

###############################################################################

class NopFetcher:
  ###########################################
  def __init__(self,name):
    self._name = name
    self._revision = ""
  ###########################################
  def descriptor(self):
    return "%s (%s)" % (self._name,self._revision)
  ###########################################
  def fetch(self,dest):
    pass
  ###########################################

###############################################################################

class CMakeBuilder:
  ###########################################
  def __init__(self,name):
    ##################################
    # ensure environment cmake present
    ##################################
    if name!="cmake":
      require("cmake")
    ##################################
    self._name = name
    self._cmakeenv = {
      "CMAKE_BUILD_TYPE": "Release",
      "BUILD_SHARED_LIBS": "ON",
    }
    self._parallelism=1.0
    self._deps = []
  ###########################################
  def requires(self,deplist):
    self._deps += deplist
  ###########################################
  def setCmVar(self,key,value):
    self._cmakeenv[key] = value
  ###########################################
  def setCmVars(self,othdict):
    for k in othdict:
      self._cmakeenv[k] = othdict[k]
  ###########################################
  def build(self,srcdir,blddir,incremental=False):
    require(self._deps)
    ok2build = True
    if incremental:
      os.chdir(blddir)
    else:
      pathtools.mkdir(blddir,clean=True)
      pathtools.chdir(blddir)
      cmake_ctx = cmake.context(root=srcdir,env=self._cmakeenv)
      ok2build = cmake_ctx.exec()==0
    if ok2build:
      return (make.exec(parallelism=self._parallelism)==0)
    return False
  ###########################################
  def install(self,blddir):
    pathtools.chdir(blddir)
    return (make.exec("install",parallelism=0.0)==0)
  ###########################################

###############################################################################

class StdProvider(Provider):

    #############################

    def __init__(self,name,miscoptions={}):
      parclass = super(StdProvider,self)
      parclass.__init__(miscoptions=miscoptions)
      self._fetcher = None
      self._builder = None
      self._node = None
      self.manifest = path.manifests()/name
      self.OK = self.manifest.exists()
      self.source_root = path.builds()/name
      self.build_src = self.source_root
      self.build_dest = self.source_root/".build"

    #############################

    def postinit(self):
      pass

    #############################

    def install(self):
      return self._builder.install(self.build_dest)

    #############################

    def __str__(self):
      return self._fetcher.descriptor()

    #############################

    def wipe(self):
      os.system("rm -rf %s"%self.source_root)

    #############################

    def build(self):

      #########################################
      # fetch source
      #########################################

      if not self.source_root.exists():
        self._fetcher.fetch(self.source_root)

      #########################################
      # build
      #########################################

      self.OK = self._builder.build(self.build_src,self.build_dest,self.incremental())


      #########################################

      return self.OK

    #########################################

    def provide(self):
      self.postinit()
      if self.should_wipe():
        self.wipe()
      if self.should_build():
        self.OK = self.build()
        if self.OK:
          self.OK = self.install()
      if self.OK:
        self.manifest.touch()
      return self.OK

###############################################################################

class DepNode:
    """dependency provider node"""
    def __init__(self,name=None,miscoptions=None):
      assert(isinstance(name,str))
      self.miscoptions = miscoptions
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
        self.instance = self.module_class(miscoptions=miscoptions)
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
