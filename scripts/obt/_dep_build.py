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
import obt.path, obt.host
from obt.command import Command, run
from obt.deco import Deco
from obt.wget import wget
from obt import pathtools, cmake, make, path, git, host, _globals, log
from obt._dep_impl import require
from collections.abc import Callable

deco = Deco()

###############################################################################
# BaseBuilder : builder basic interface
###############################################################################

class BaseBuilder(object):
  def __init__(self,name):
    super().__init__()
    self._name = name
    self._deps = []
    self._debug = False
    self._onPostBuild = None
    self._onPostInstall = None
  def requires(self,deplist):
    """declare that this dep module depends on others"""
    self._deps += deplist
  def build(self,srcdir,blddir,wrkdir,incremental=False):
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
  def build(self,srcdir,blddir,wrkdir,incremental=False):
    return True
###############################################################################
# BinInstaller : install binaries from downloaded package
###############################################################################

class BinInstaller(BaseBuilder):
  """Install binaries from downloaded package"""
  ###########################
  class InstallerItem:
    def __init__(self,src,dst,flags):
      self._src = src
      self._dst = dst
      self._flags = flags
  ###########################
  def __init__(self,name):
    super().__init__(name)
    self._items = []
    self._OK = True
  ###########################################
  """declare an install item given a source-path and dest-path"""
  def install_item(self,
                   source=None,
                   destination=None,
                   flags=None):
    self._items += [BinInstaller.InstallerItem(source,destination,flags)]
  ###########################################
  def build(self,srcdir,blddir,wrkdir,incremental=False):
    ok2build = require(self._deps)
    if not ok2build:
      return False
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
        "cp", item._src, item._dst
      ]
      Command(cmd).exec()
      if item._flags != None:
        cmd = [
          "chmod",item._flags, item._dst
        ]
        Command(cmd).exec()
    return self._OK

###############################################################################

class CMakeBuilder(BaseBuilder):
  ###########################################
  def __init__(self,
               name,
               static_libs=False,
               macos_defaults=True,
               install_prefix=None):
    super().__init__(name)
    self._minimal = False 
    self._install_prefix = install_prefix
    ##################################
    # ensure environment cmake present
    ##################################
    self._cmakeenv = {
      "CMAKE_BUILD_TYPE": "Release",
    }
    self._osenv = {
    }

    if not static_libs:
      self._cmakeenv["BUILD_SHARED_LIBS"]="ON"

    ##################################
    # default OSX stuff
    ##################################
    if obt.host.IsOsx and macos_defaults:
      sysroot_cmd = Command(["xcrun","--show-sdk-path"],do_log=False)
      sysroot = sysroot_cmd.capture().replace("\n","")

      if obt.host.IsAARCH64:
        self._cmakeenv.update({"CMAKE_HOST_SYSTEM_PROCESSOR":"arm64"})
      else:
        self._cmakeenv.update({"CMAKE_HOST_SYSTEM_PROCESSOR":"x86_64"})

      self._cmakeenv.update({
        "CMAKE_OSX_DEPLOYMENT_TARGET:STRING":"11",
        "CMAKE_OSX_SYSROOT:STRING":sysroot,
        "CMAKE_MACOSX_RPATH": "1",
        "CMAKE_INSTALL_RPATH": path.libs(),
        "CMAKE_SKIP_INSTALL_RPATH:BOOL":"NO",
        "CMAKE_SKIP_RPATH:BOOL":"NO",
        "CMAKE_INSTALL_NAME_DIR": "@executable_path/../lib"
      })

    ##################################
    self._parallelism = 0.0 if _globals.tryBoolOption("serial") else 1.0
    ##################################
    # implicit dependencies
    ##################################
    if name!="cmake":
      self._deps += ["cmake"]
  ###############################################
  @property 
  def install_prefix(self):
    return path.prefix() if (self._install_prefix==None) else self._install_prefix
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
  @property 
  def cmakeEnvAsString(self):
    return " ".join(self.cmakeEnvAsStringList)
  ###########################################
  @property 
  def cmakeEnvAsStringList(self):
    args = []
    for k in self._cmakeenv:
      v = self._cmakeenv[k]
      args += ["-D%s=%s"%(k,v)]
    return args
  ###########################################
  def build(self,srcdir,blddir,wrkdir,incremental=False):
    print("srcdir<%s>"%srcdir)
    print("blddir<%s>"%blddir)
    print("wrkdir<%s>"%wrkdir)

    ok2build = require(self._deps)
    if not ok2build:
      return False
    if incremental:
      pathtools.mkdir(blddir,clean=False)
      pathtools.chdir(wrkdir)
      cmake_ctx = cmake.context(root=srcdir,
                                env=self._cmakeenv,
                                osenv=self._osenv,
                                builddir=blddir,
                                working_dir=wrkdir,
                                install_prefix=self.install_prefix)
      ok2build = cmake_ctx.exec()==0
    else:
      pathtools.mkdir(blddir,clean=True)
      pathtools.chdir(wrkdir)
      cmake_ctx = cmake.context(root=srcdir,
                                env=self._cmakeenv,
                                osenv=self._osenv)
      ok2build = cmake_ctx.exec()==0

    if ok2build:
      OK = (make.exec(parallelism=self._parallelism)==0)
      if OK and self._onPostBuild!=None:
        self._onPostBuild()
      return OK
    return False
  ###########################################
  def install(self,blddir):
    pathtools.chdir(blddir)
    OK = (make.exec("install",parallelism=0.0)==0)
    if OK and self._onPostInstall!=None:
       self._onPostInstall()
    return OK

  ###########################################

###############################################################################

class AutoConfBuilder(BaseBuilder):
  ###########################################
  def __init__(self,name):
    super().__init__(name)
    ##################################
    self._needaclocal = False
    self._needsautogendotsh = False
    self._parallelism=1.0
    self._options = list()
    self._envvars = dict()
    if _globals.tryBoolOption("serial"):
      self._parallelism=0.0
  ###########################################
  def requires(self,deplist):
    self._deps += deplist
  ###########################################
  def setEnvVar(self,key,value):
    self._envvars[key] = value
  ###########################################
  def setConfVar(self,key,value):
    self._confvar[key] = value
  ###########################################
  def setOption(self,opt):
    self._options += [opt]
  ###########################################
  def setConfVars(self,othdict):
    for k in othdict:
      self._confvar[k] = othdict[k]
  ###########################################
  def build(self,srcdir,blddir,wrkdir,incremental=False):
    ok2build = require(self._deps)
    if not ok2build:
      return False
    retc = 0
    pathtools.mkdir(blddir)
    if incremental:
      os.chdir(blddir)
    else:

      if self._needaclocal:
        pathtools.chdir(srcdir)
        retc = Command(["aclocal"]).exec()
        if retc!=0:
          print(deco.red("Error running aclocal<%d>"%retc))
          return False
      if self._needsautogendotsh:
        pathtools.chdir(srcdir)
        retc = Command(["./autogen.sh"]).exec()
        if retc == 0:
           make.exec("distclean")
        else:
          print(deco.red("Error running autogen.sh<%d>"%retc))
          return False

      pathtools.mkdir(blddir,clean=True)
      pathtools.chdir(blddir)

      retc = Command([srcdir/"configure",
                      '--prefix=%s'%path.prefix()
                     ]+self._options,
                     environment=self._envvars
                     ).exec()
      if retc==0:
        make.exec("all")
        retc = make.exec("install",parallelism=0.0)
    print("retc<%d>"%int(retc))
    return retc==0
  ###########################################
  def install(self,blddir):
    pathtools.chdir(blddir)
    return (make.exec("install",parallelism=0.0)==0)
  ###########################################

###############################################################################

class CustomStep:
  def __init__(self,name,funktor):
    super().__init__()
    self._name = name
    self._funktor = funktor 

###############################################################################

class CustomBuilder(BaseBuilder):
  ###########################################
  def __init__(self,name):
    super().__init__(name)
    ##################################
    self._envvars = dict()
    self._parallelism=1.0
    self._cleanbuildcommands = list()
    self._incrbuildcommands = list()
    self._installcommands = list()
    self._builddir = path.builds()/name

    if _globals.tryBoolOption("serial"):
      self._parallelism=0.0
  ###########################################
  def requires(self,deplist):
    self._deps += deplist
  ###########################################
  def setEnvVar(self,key,value):
    self._envvars[key] = value
  ###########################################
  def setEnvVars(self,othdict):
    for k in othdict:
      self._envvars[k] = othdict[k]
  ###########################################
  def _run_commands(self,cmdlist):
    if len(cmdlist)>0:
      for cmd in cmdlist:
        if isinstance(cmd,Command):
          retc = cmd.exec()
          if retc!=0:
            return False
        elif isinstance(cmd,CustomStep):
          retc = cmd._funktor()
          if retc==False:
            return False
        elif isinstance(cmd,Callable):
          if cmd()==False:
            return False
    return True
  ###########################################
  def build(self,srcdir,blddir,wrkdir,incremental=False):
    print("srcdir<%s>"%srcdir)
    print("blddir<%s>"%blddir)
    print("incremental<%s>"%incremental)
    print("deps<%s>"%self._deps)
    ok2build = require(self._deps)
    if not ok2build:
      return False
    ###################################
    if incremental:
    ###################################
      pathtools.mkdir(self._builddir,clean=False,parents=True)
      pathtools.chdir(self._builddir)
      return self._run_commands(self._incrbuildcommands)
    ###################################
    else: # clean build
    ###################################
      pathtools.mkdir(self._builddir,clean=False)
      pathtools.chdir(self._builddir)
      return self._run_commands(self._cleanbuildcommands)
  ###########################################
  def install(self,blddir):
    pathtools.chdir(self._builddir)
    return self._run_commands(self._installcommands)
  ###########################################
