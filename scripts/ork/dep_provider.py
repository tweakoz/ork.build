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

deco = Deco()
###############################################################################

class Provider(object):
    """base class for all dependency providers"""
    def __init__(self):
      self._miscoptions = globals.options
      self._node = None
      self._deps = {}

    #############################
    ## wipe build ?
    #############################

    @property
    def should_wipe(self):
      """predicate controlling build-clean during provisioning of a dependency"""
      wipe = False
      if "wipe" in self._miscoptions:
        wipe = self._miscoptions["wipe"]==True
      return wipe

    #############################
    ## serial build ?
    #############################

    @property
    def should_serial_build(self):
      """predicate controlling 1cpu build during provisioning of a dependency (for build debugging)"""
      serial = False
      if "serial" in self._miscoptions:
        serial = self._miscoptions["serial"]==True
      return serial

    @property
    def default_parallelism(self):
      parallelism = 1.0
      if self.should_serial_build:
        parallelism=0.0
      return parallelism

    #############################
    ## force build ?
    #############################

    @property
    def should_force_build(self):
        force = False
        if "force" in self._miscoptions:
          force = self._miscoptions["force"]==True
        return force

    #############################
    ## force build ?
    #############################

    @property
    def should_incremental_build(self):
        incremental = False
        if "incremental" in self._miscoptions:
          incremental = self._miscoptions["incremental"]==True
        return incremental

    #############################

    @property
    def should_build(self):
        return (False==self.manifest.exists()) or \
               self.should_force_build or \
               self.should_incremental_build

    #############################

    @property
    def should_fetch(self):
        fetch = False
        if "nofetch" in self._miscoptions:
          fetch = self._miscoptions["nofetch"]==False
        return fetch

    #############################

    @property
    def _std_cmake_vars():
      cmakeEnv = {
        "CMAKE_BUILD_TYPE": "Release",
        "BUILD_SHARED_LIBS": "ON",
      }
      return cmakeEnv

    #############################

    @property
    def exists(self):
        return False

    #############################

    def option(self,named):
      if named in self._miscoptions:
        return self._miscoptions[named]
      else:
        return None

    #############################

    def provide(self):
      if self.should_wipe:
        self.wipe()
      if self.should_build:
        self.OK = self.build()
      if self.OK:
        self.manifest.touch()
      return self.OK


    #############################

    def _std_cmake_build(self,srcdir,blddir,cmakeEnv=_std_cmake_vars,parallelism=1.0):
      ok2build = True
      if self.should_incremental_build:
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

    @property
    def shlib_extension(self):
      if host.IsOsx:
        return "dylib"
      if host.IsIx:
        return "so"

###############################################################################

class HomebrewProvider(Provider):
  def __init__(self,name,pkgname):
    super().__init__()
    self.manifest = path.manifests()/name
    self.OK = self.manifest.exists()
    self.pkgname = pkgname
    self._deps = list()
  ###########################################
  def requires(self,deplist):
    self._deps += deplist
  ###########################################
  def brew_prefix(self):
    return Path("/")/"usr"/"local"
  ###########################################
  def build(self):
    require(self._deps)
    retc = Command(["brew","install",self.pkgname]).exec()
    if 0 == retc:
      self.manifest.touch()
    return 0==retc

###############################################################################

class StdProvider(Provider):
    #############################
    def __init__(self,name):
      super().__init__()
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
    def requires(self,deplist):
      self._builder.requires(deplist)
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
        fetchOK = self._fetcher.fetch(self.source_root)
        if False==fetchOK:
          self.OK = False
          return False
      #########################################
      # build
      #########################################
      self.OK = self._builder.build(self.build_src,self.build_dest,self.should_incremental_build)
      #########################################
      return self.OK
    #########################################
    def provide(self):
      self.postinit()
      if self.should_wipe:
        self.wipe()
      if self.should_build:
        self.OK = self.build()
        if self.OK:
          self.OK = self.install()
      if self.OK:
        self.manifest.touch()
      return self.OK
