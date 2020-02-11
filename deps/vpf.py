###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "master"

import os, tarfile
from ork import dep, host, path, cmake, git, make
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()

###############################################################################

class vpf(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(vpf,self)
    parclass.__init__(options=options)
    #print(options)
    self.source_dest = path.builds()/"vpf"
    self.build_dest = path.builds()/"vpf"/".build"
    self.manifest = path.manifests()/"vpf"
    self.OK = self.manifest.exists()

  def __str__(self): ##########################################################

    return "VPF (github-%s)" % VERSION

  def build(self): ##########################################################

    python = dep.require("python")
    pybind11 = dep.require("pybind11")

    if self.incremental():
        os.chdir(self.build_dest)
    else:
        #git.Clone("https://github.com/tweakoz/VideoProcessingFramework",self.source_dest,VERSION)
        os.system("rm -rf %s"%self.build_dest)
        os.mkdir(self.build_dest)
        os.chdir(self.build_dest)

        cmakeEnv = {
            "CMAKE_BUILD_TYPE": "RELEASE",
            "VIDEO_CODEC_SDK_INCLUDE_DIR": "/opt/nvencsdk/include/",
            "GENERATE_PYTHON_BINDINGS": True
        }

        cmake_ctx = cmake.context("..",env=cmakeEnv)
        cmake_ctx.exec()

    rval = (make.exec("install")==0)
    return rval

  def linkenv(self): ##########################################################
    LIBS = ["ork_vpf"]
    return {
        "LIBS": LIBS,
        "LFLAGS": ["-l%s"%item for item in LIBS]
    }
