###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "master"

import os, tarfile
from ork import dep, host, path, cmake, git, make, command, pathtools
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()

###############################################################################

class pybind11(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(pybind11,self)
    parclass.__init__(options=options)
    #print(options)
    self.source_dest = path.builds()/"pybind11"
    self.build_dest = path.builds()/"pybind11"/".build"
    self.manifest = path.manifests()/"pybind11"
    self.OK = self.manifest.exists()

  def __str__(self): ##########################################################

    return "PyBind11 (github-%s)" % VERSION

  def wipe(self): #############################################################
    os.system("rm -rf %s"%self.source_dest)

  def build(self): ##########################################################

    #########################################
    # fetch source
    #########################################

    if not self.source_dest.exists():
        git.Clone("https://github.com/pybind/pybind11",self.source_dest,VERSION)

    #########################################
    # build
    #########################################

    cmakeEnv = {
        "CMAKE_BUILD_TYPE": "RELEASE",
        "BUILD_SHARED_LIBS": "ON",
    }
    self.OK = self._std_cmake_build(self.source_dest,self.build_dest,cmakeEnv)
    return self.OK
