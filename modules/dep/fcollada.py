###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION ="master"

import os, shutil, tarfile
from obt import dep, host, path, git, cmake, make
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command
from obt.cmake import context

deco = Deco()

###############################################################################

class fcollada(dep.Provider):

  def __init__(self): ############################################
    super().__init__("fcollada")

    self.source_root = path.builds()/"fcollada"
    self.build_dest = path.builds()/"fcollada"/".build"

  def __str__(self): ##########################################################

    return "fcollada"

  def build(self): ##########################################################

    git.Clone("https://github.com/tweakoz/obt.fcollada",self.source_root,VERSION)

    if self.build_dest.exists():
      shutil.rmtree(str(self.build_dest), ignore_errors=True)
    os.mkdir(self.build_dest)
    cmake_ctx = cmake.context(sourcedir=self.source_root,
                              builddir=self.build_dest,
                              working_dir=self.build_dest)
    cmake_ctx.exec()
    return (make.exec("install", working_dir=self.build_dest)==0)

  def linkenv(self): ##########################################################
    return {
        "LIBS": ["fcollada"]
    }
