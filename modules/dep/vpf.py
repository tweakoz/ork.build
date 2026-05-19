###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "master"

import os, shutil, tarfile
from obt import dep, host, path, cmake, git, make, pathtools
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()

###############################################################################

class vpf(dep.Provider):

  def __init__(self): ############################################
    super().__init__("vpf")
    #print(options)
    self.source_root = path.builds()/"vpf"
    self.build_dest = path.builds()/"vpf"/".build"
    self.sdk_dir = path.Path("/opt/nvencsdk")
    self._archlist = ["x86_64"]

  def __str__(self): ##########################################################

    return "VPF (github-%s)" % VERSION

  def wipe(self): #############################################################
    if self.source_root.exists():
      shutil.rmtree(str(self.source_root), ignore_errors=True)

  def build(self): ##########################################################

    if not self.sdk_dir.exists():
        print(deco.red("you need the nvenc SDK at <%s>" % self.sdk_dir ))
        print(deco.red("download @ https://developer.nvidia.com/nvidia-video-codec-sdk"))
        print(deco.yellow(" * requires login which is why I cannot download it for you!"))
        assert(False)

    python = dep.require("python")
    pybind11 = dep.require("pybind11")

    #########################################
    # fetch source
    #########################################

    if not self.source_root.exists():
        git.Clone("https://github.com/tweakoz/VideoProcessingFramework",self.source_root,VERSION)

    #########################################
    # prep for build
    #########################################

    ok2build = True
    if self.should_incremental_build:
        pass  # no chdir; make.exec below uses working_dir
    else:

        pathtools.mkdir(self.build_dest,clean=True)

        cmakeEnv = {
            "CMAKE_BUILD_TYPE": "RELEASE",
            "VIDEO_CODEC_SDK_INCLUDE_DIR": self.sdk_dir/"include",
            "GENERATE_PYTHON_BINDINGS": True
        }

        cmake_ctx = cmake.context(sourcedir=self.source_root,
                                  builddir=self.build_dest,
                                  working_dir=self.build_dest,
                                  env=cmakeEnv)
        ok2build = cmake_ctx.exec()==0

    #########################################
    # build
    #########################################

    OK = True
    if ok2build:
        OK = (make.exec("install", working_dir=self.build_dest)==0)
    return OK

  def linkenv(self): ##########################################################
    LIBS = ["ork_vpf"]
    return {
        "LIBS": LIBS,
        "LFLAGS": ["-l%s"%item for item in LIBS]
    }
