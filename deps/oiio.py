###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from ork import dep, host, path, pathtools, git, cmake, make
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()

VERSION = "spi-spcomp2-release-49.4"
###############################################################################

class oiio(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(oiio,self)
    parclass.__init__(options=options)
    self.manifest = path.manifests()/"oiio"
    self.OK = self.manifest.exists()
    self.source_dest = path.builds()/"oiio"
    self.build_dest = self.source_dest/".build"

  ########

  def __str__(self):
    return "OpenImageIO (github-%s)" % VERSION

  def wipe(self): #############################################################
    os.system("rm -rf %s"%self.source_dest)

  ########

  def provide(self): ##########################################################

    dep.require(["pkgconfig","openexr","pybind11"])
    if host.IsLinux:
        dep.require(["qt5"])

    #########################################
    # fetch source
    #########################################

    if not self.source_dest.exists():
      git.Clone("https://github.com/OpenImageIO/oiio",
                self.source_dest,
                VERSION )

    cmakeEnv = {
        "CMAKE_BUILD_TYPE": "RELEASE",
        "CMAKE_CXX_FLAGS": "-Wno-error=deprecated",
        "BUILD_SHARED_LIBS": "ON",
        "USE_NUKE": "OFF",
        "USE_PYTHON": "ON",
        "OIIO_BUILD_TOOLS": "ON",
        "OIIO_BUILD_TESTS": "ON"
    }

    if host.IsLinux:
       cmakeEnv["CMAKE_CXX_COMPILER"] = "g++-9"
       cmakeEnv["CMAKE_C_COMPILER"] = "gcc-9"

    self.OK = self._std_cmake_build(self.source_dest,self.build_dest,cmakeEnv)
    return self.OK
