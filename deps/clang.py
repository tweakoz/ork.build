###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from ork import dep, host, path, git, cmake, make
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
from ork.cmake import context

deco = Deco()

###############################################################################

class clang(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(clang,self)
    parclass.__init__(options=options)

    self.llvm = dep.require("llvm")

    self.source_dest = self.llvm.dest_base/"clang"
    self.build_dest = self.source_dest/".build"
    self.manifest = path.manifests()/"clang"

    self.OK = self.manifest.exists()

  def __str__(self): ##########################################################
    return "Clang (github-llvm)"

  def build(self): ##########################################################

    cmakeEnv = {
        "CMAKE_BUILD_TYPE": "RELEASE",
        "BUILD_SHARED_LIBS": "ON",
    }
    self.OK = self._std_cmake_build(self.source_dest,self.build_dest,cmakeEnv)
    return self.OK
