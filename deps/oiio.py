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

###############################################################################

class oiio(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(oiio,self)
    parclass.__init__(options=options)
    self.manifest = path.manifests()/"OpenImageIo"
    self.OK = self.manifest.exists()
    self.source_dest = path.builds()/"OpenImageIo"
    self.build_dest = self.source_dest/".build"

  ########

  def __str__(self):
    return "OpenEXR (github)"

  ########

  def provide(self): ##########################################################
    if False==self.OK:
        dep.require("pkgconfig")
        dep.require("cmake314")
        dep.require("qt5")
        dep.require("openexr")

        os.system("rm -rf %s"%self.source_dest)

        git.Clone("https://github.com/OpenImageIO/oiio",
                  self.source_dest,
                  "spi-spcomp2-release-49")

        pathtools.mkdir(self.build_dest,clean=True)
        pathtools.chdir(self.build_dest)

        cmakeEnv = {
            "CMAKE_BUILD_TYPE": "RELEASE",
            "CMAKE_CXX_FLAGS": "-Wno-error=deprecated",
            "BUILD_SHARED_LIBS": "ON",
            "USE_NUKE": "OFF",
        }

        cmake_ctx = cmake.context(root="..",env=cmakeEnv)
        if cmake_ctx.exec()==0:
            if make.exec("install")==0:
                self.manifest.touch()
                self.OK = True

    return self.OK
