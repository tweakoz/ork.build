###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from obt import dep, host, path, pathtools, git, cmake, make, command
from obt.deco import Deco
from obt.wget import wget

deco = Deco()

VERSION = "master"
###############################################################################

class vst3sdk(dep.Provider):

  def __init__(self): ############################################
    super().__init__("vst3sdk")
    self.manifest = path.manifests()/"vst3sdk"
    self.OK = self.manifest.exists()
    self.source_root = path.builds()/"vst3sdk"
    self.build_dest = self.source_root/".build"
    self._archlist = ["x86_64"]

  ########

  def __str__(self):
    return "VST3SDK (github-%s)" % VERSION

  ########

  def build(self): #############################################################

    self.OK = False
    if self.should_force_build:
        os.system("rm -rf %s"%self.source_root)

    git.Clone("https://github.com/steinbergmedia/vst3sdk",
              self.source_root,
              VERSION,
              recursive = True)

    pathtools.mkdir(self.build_dest,clean=True)
    pathtools.chdir(self.build_dest)

    cmakeEnv = {
        "CMAKE_BUILD_TYPE": "RELEASE",
        "OPTION_BUILD_SHARED_LIBS": "ON",
        "VERBOSE":"ON"
    }

    cmake_ctx = cmake.context(root="..",env=cmakeEnv)
    if cmake_ctx.exec()==0:
        if make.exec("all")==0:
          self.manifest.touch()
          self.OK = True

    return self.OK

  ########

  def provide(self): ##########################################################

    if self.should_build:
      self.OK = self.build()
    print(self.OK)
    return self.OK
