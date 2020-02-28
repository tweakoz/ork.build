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

VERSION = "master"

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

  def wipe(self): #############################################################
    os.system("rm -rf %s"%self.source_dest)

  ########
  def build(self): #############################################################

    dep.require(["fltk"])

    #########################################
    # fetch source
    #########################################

    if not self.source_dest.exists():
        git.Clone("https://github.com/openexr/openexr",
                  self.source_dest,
                  VERSION)

    cmakeEnv = {
        "CMAKE_BUILD_TYPE": "RELEASE",
        "BUILD_SHARED_LIBS": "ON",
        "OPENEXR_VIEWERS_ENABLE": "OFF",
        "CMAKE_MODULE_PATH": self.source_dest
    }

    self.OK = self._std_cmake_build(self.source_dest,self.build_dest,cmakeEnv)
    return self.OK

  ########
