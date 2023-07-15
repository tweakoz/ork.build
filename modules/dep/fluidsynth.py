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

VERSION = "v2.1.0"
###############################################################################

class fluidsynth(dep.Provider):

  def __init__(self): ############################################
    super().__init__("fluidsynth")
    self.manifest = path.manifests()/"fluidsynth"
    self.OK = self.manifest.exists()
    self.source_root = path.builds()/"fluidsynth"
    self.build_dest = self.source_root/".build"
    self._archlist = ["x86_64"]

  ########

  def __str__(self):
    return "CALF (github-%s)" % VERSION

  ########

  def build(self): #############################################################

    self.OK = False

    os.system("rm -rf %s"%self.source_root)

    git.Clone("https://github.com/FluidSynth/fluidsynth",
              self.source_root,
              VERSION)

    pathtools.mkdir(self.build_dest,clean=True)
    pathtools.chdir(self.build_dest)

    cmakeEnv = {
        "CMAKE_BUILD_TYPE": "RELEASE",
        "BUILD_SHARED_LIBS": "ON",
    }

    cmake_ctx = cmake.context(root="..",env=cmakeEnv)
    if cmake_ctx.exec()==0:
        if make.exec("install")==0:
            self.manifest.touch()
            self.OK = True

    return self.OK

  ########

  def provide(self): ##########################################################

    if self.should_build:
      self.OK = self.build()
    print(self.OK)
    return self.OK
