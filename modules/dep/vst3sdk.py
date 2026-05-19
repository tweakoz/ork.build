###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, shutil, tarfile
from obt import dep, host, path, pathtools, git, cmake, make, command
from obt.deco import Deco
from obt.wget import wget

deco = Deco()

VERSION = "master"
###############################################################################

class vst3sdk(dep.Provider):

  def __init__(self): ############################################
    super().__init__("vst3sdk")
    self.source_root = path.builds()/"vst3sdk"
    self.build_dest = self.source_root/".build"
    self._archlist = ["x86_64"]

  ########

  def __str__(self):
    return "VST3SDK (github-%s)" % VERSION

  ########

  def build(self): #############################################################

    OK = True

    if self.should_force_build and self.source_root.exists():
        shutil.rmtree(str(self.source_root), ignore_errors=True)

    git.Clone("https://github.com/steinbergmedia/vst3sdk",
              self.source_root,
              VERSION,
              recursive = True)

    pathtools.mkdir(self.build_dest,clean=True)

    cmakeEnv = {
        "CMAKE_BUILD_TYPE": "RELEASE",
        "OPTION_BUILD_SHARED_LIBS": "ON",
        "VERBOSE":"ON"
    }

    cmake_ctx = cmake.context(sourcedir=self.source_root,
                              builddir=self.build_dest,
                              working_dir=self.build_dest,
                              env=cmakeEnv)
    if cmake_ctx.exec()==0:
        if make.exec("all", working_dir=self.build_dest)==0:
          self.manifest.touch()
          OK = True

    return OK

  ########

  def provide(self): ##########################################################
    return super()._old_provide()
