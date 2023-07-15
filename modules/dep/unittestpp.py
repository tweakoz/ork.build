###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "master"

import os, tarfile
from obt import dep, host, path, git, make, cmake
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()

###############################################################################

class unittestpp(dep.Provider):

  def __init__(self): ############################################
    super().__init__("unittestpp")

    self.source_root = path.builds()/"unittestpp"
    self.build_dest = path.builds()/"unittestpp"/".build"
    self.manifest = path.manifests()/"unittestpp"

    self.OK = self.manifest.exists()

  ########

  def __str__(self):
    return "UnitTestPP (github-%s)" % VERSION

  ########

  def build(self): ############################################################

    git.Clone("https://github.com/tweakoz/unittestpp",self.source_root,VERSION)

    os.system("rm -rf %s"%self.build_dest)
    os.mkdir(self.build_dest)
    os.chdir(self.build_dest)
    cmake_ctx = cmake.context("..",env={
        "BUILD_SHARED_LIBS": "ON"
    })
    cmake_ctx.exec()
    return (make.exec("install")==0)

  def provide(self): ##########################################################

    if self.should_build:

      self.OK = self.build()
      if self.OK:
        self.manifest.touch()

    return self.OK
