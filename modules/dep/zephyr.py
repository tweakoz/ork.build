###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION ="litex-vexriscv"

import os, tarfile
from obt import dep, host, path, git, cmake, make
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command
from obt.cmake import context

deco = Deco()

###############################################################################

class zephyr(dep.Provider):

  def __init__(self): ############################################
    super().__init__("zephyr")
    self.source_root = path.builds()/"zephyr"
    self.build_dest = path.builds()/"zephyr"/".build"
    self._archlist = ["x86_64"]
    self._oslist = ["Linux"]

  def __str__(self): ##########################################################

    return "ZEPHYR (github-tweakoz/litex-edition)"

  def env_goto(self): #########################################################
    return {
      "zephyr-src": self.source_root,
      "zephyr-build": self.build_dest
    }

  def build(self): ##########################################################

    git.Clone("https://github.com/tweakoz/zephyr",self.source_root,VERSION)

    os.system("rm -rf %s"%self.build_dest)
    os.mkdir(self.build_dest)
    os.chdir(self.build_dest)

    #cmake_ctx = cmake.context("..")
    #cmake_ctx.exec()
    #return (make.exec("install")==0)

    return True

  def provide(self): ##########################################################

    if self.should_build:

      self.OK = self.build()
      if self.OK:
        self.manifest.touch()

    print(self.OK)

    return self.OK
