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

VERSION = "v2.4.0"

###############################################################################

class openexr(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(openexr,self)
    parclass.__init__(options=options)
    self.manifest = path.manifests()/"openexr"
    self.OK = self.manifest.exists()
    self.source_dest = path.builds()/"openexr"
    self.build_dest = self.source_dest/".build"

  ########

  def __str__(self):
    return "OpenEXR (github-%s)" % VERSION

  ########

  def build(self): #############################################################

    dep.require("fltk")

    os.system("rm -rf %s"%self.source_dest)

    git.Clone("https://github.com/openexr/openexr",
              self.source_dest,
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

    if self.should_build():
      self.OK = self.build()
    print(self.OK)
    return self.OK
