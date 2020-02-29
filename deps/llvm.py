###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION ="llvmorg-8.0.1"

import os, tarfile
from ork import dep, host, path, git, cmake, make
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
from ork.cmake import context

deco = Deco()

###############################################################################

class llvm(dep.Provider):

  def __init__(self,miscoptions=None): ############################################

    parclass = super(llvm,self)
    parclass.__init__(miscoptions=miscoptions)

    self.dest_base = path.builds()/"llvm"
    self.source_dest = self.dest_base/"llvm"
    self.build_dest = self.source_dest/".build"
    self.utils_source_dest = self.dest_base/"llvm"/"utils"
    self.utils_build_dest = self.utils_source_dest/".build"
    self.manifest = path.manifests()/"llvm"

    self.OK = self.manifest.exists()

  def __str__(self): ##########################################################
    return "LLVM (github-%s)" % VERSION

  def wipe(self): #############################################################
    os.system("rm -rf %s"%self.dest_base)

  def build(self): ##########################################################

    #########################################
    # fetch source
    #########################################

    if not self.dest_base.exists():
        git.Clone("https://github.com/llvm/llvm-project",self.dest_base,VERSION)

    #########################################
    # build
    #########################################

    cmakeEnv = {
        "CMAKE_BUILD_TYPE": "RELEASE",
        "BUILD_SHARED_LIBS": "ON",
        "LLVM_INSTALL_UTILS": "ON",
        "LLVM_ENABLE_DUMP": "ON"
    }
    self.OK = self._std_cmake_build(self.source_dest,self.build_dest,cmakeEnv)
    return self.OK
