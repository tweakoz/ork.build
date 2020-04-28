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
from ork._dep_provider import require

deco = Deco()

###############################################################################
# BaseBuilder : builder basic interface
###############################################################################

class BaseBuilder(object):
  def __init__(self,name):
    super().__init__()
    self._name = name
    self._deps = []
  def requires(self,deplist):
    """declare that this dep module depends on others"""
    self._deps += deplist
  def build(self,srcdir,blddir,incremental=False):
    """execute build phase"""
    require(self._deps)
  def install(self,blddir):
    """execute install phase"""
    return True

###############################################################################
# NopBuilder : do nothing builder (but still installs child dependencies)
###############################################################################

class NopBuilder(BaseBuilder):
  """Do nothing builder (but still installs child dependencies)"""
  def __init__(self,name):
    super().__init__(name)

###############################################################################
# BinInstaller : install binaries from downloaded package
###############################################################################

class BinInstaller(BaseBuilder):
  """Install binaries from downloaded package"""
  ###########################
  class InstallerItem:
    def __init__(self,src,dst):
      self._src = src
      self._dst = dst
  ###########################
  def __init__(self,name):
    super().__init__(name)
    self._items = []
    self._OK = True
  ###########################################
  """declare an install item given a source-path and dest-path"""
  def install_item(self,source=None,destination=None):
    self._items += [BinInstaller.InstallerItem(source,destination)]
  ###########################################
  def build(self,srcdir,blddir,incremental=False):
    require(self._deps)
    for item in self._items:
      exists = item._src.exists()
      #print(item,item._src,exists)
      if False==exists:
        self._OK = False
        return False
    return True
  ###########################################
  def install(self,blddir):
    for item in self._items:
      cmd = [
        "cp", str(item._src), str(item._dst)
      ]
      Command(cmd).exec()
    return self._OK

###############################################################################

class CMakeBuilder(BaseBuilder):
  ###########################################
  def __init__(self,name):
    super().__init__(name)
    ##################################
    # ensure environment cmake present
    ##################################
    self._cmakeenv = {
      "CMAKE_BUILD_TYPE": "Release",
      "BUILD_SHARED_LIBS": "ON",
    }
    ##################################
    # default OSX stuff
    ##################################
    if ork.host.IsOsx:
      sysroot_cmd = Command(["xcrun","--show-sdk-path"],do_log=False)
      sysroot = sysroot_cmd.capture().replace("\n","")
      self._cmakeenv.update({
        "CMAKE_OSX_ARCHITECTURES:STRING":"x86_64",
        "CMAKE_OSX_DEPLOYMENT_TARGET:STRING":"10.14",
        "CMAKE_OSX_SYSROOT:STRING":sysroot,
        "CMAKE_MACOSX_RPATH": "1",
        "CMAKE_INSTALL_RPATH": path.libs(),
        "CMAKE_SKIP_INSTALL_RPATH:BOOL":"NO",
        "CMAKE_SKIP_RPATH:BOOL":"NO",
        "CMAKE_INSTALL_NAME_DIR": "@executable_path/../lib"
      })

    ##################################
    self._parallelism=1.0
    ##################################
    # implicit dependencies
    ##################################
    if name!="cmake":
      self._deps += ["cmake"]
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
