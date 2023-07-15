###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "master"

import os, tarfile
from yarl import URL
from obt import dep, host, path, cmake, git, make
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()

###############################################################################

class vrx(dep.Provider):

  def __init__(self): ############################################
    super().__init__("vrx")
    #print(options)
    self.source_root = path.builds()/"vrx"
    self.build_dest = path.builds()/"vrx"/".build"
    self.manifest = path.manifests()/"vrx"
    self.OK = self.manifest.exists()
    self._archlist = ["x86_64"]
  def __str__(self): ##########################################################

    return "VRX (github-%s)" % VERSION

  def build(self): ##########################################################

    assimp = dep.require("assimp")
    glfw = dep.require("glfw")
    utpp = dep.require("unittestpp")

    if self.should_incremental_build:
        os.chdir(self.build_dest)
    else:
        git.Clone("https://github.com/tweakoz/vrx",self.source_root,VERSION)
        os.system("rm -rf %s"%self.build_dest)
        os.mkdir(self.build_dest)
        os.chdir(self.build_dest)
        cmake_ctx = cmake.context("..")
        cmake_ctx.exec()

    rval = (make.exec("install")==0)
    return rval

  def linkenv(self): ##########################################################
    LIBS = ["obt.vrx"]
    return {
        "LIBS": LIBS,
        "LFLAGS": ["-l%s"%item for item in LIBS]
    }
