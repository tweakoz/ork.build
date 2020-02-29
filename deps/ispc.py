###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION ="v1.12.0"

import os, tarfile
from ork import dep, host, path, git, cmake, make
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
from ork.cmake import context

deco = Deco()

###############################################################################

class ispc(dep.Provider):

  def __init__(self,miscoptions=None): ############################################

    parclass = super(ispc,self)
    parclass.__init__(miscoptions=miscoptions)

    self.source_dest = path.builds()/"ispc"
    self.build_dest = path.builds()/"ispc"
    self.manifest = path.manifests()/"ispc"

    self.OK = self.manifest.exists()

  def __str__(self): ##########################################################
    return "Intel ISPC Compiler (github-%s)" % VERSION

  def wipe(self): #############################################################
    os.system("rm -rf %s"%self.source_dest)

  def build(self): ##########################################################

    dep.require(["llvm","clang"])

    #########################################
    # fetch source
    #########################################

    if not self.source_dest.exists():
        git.Clone("https://github.com/ispc/ispc",self.source_dest,VERSION,cache=False,recursive=False)

    #########################################
    # build
    #########################################

    cmakeEnv = {
        "CMAKE_BUILD_TYPE": "RELEASE",
        "BUILD_SHARED_LIBS": "ON",
    }
    os.chdir(str(self.source_dest))
    this_dir = path.Path(".")
    self.OK = self._std_cmake_build(this_dir,this_dir,cmakeEnv)
    return self.OK
