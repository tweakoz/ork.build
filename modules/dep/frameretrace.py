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

class frameretrace(dep.Provider):

  def __init__(self): ############################################
    super().__init__("frameretrace")
    self.source_root = path.builds()/"frameretrace"
    self.build_dest = path.builds()/"frameretrace"/".build"
    self._archlist = ["x86_64"]

  def __str__(self): ##########################################################

    return "FrameRetrace (github)"

  def build(self): ##########################################################

    git.Clone("https://github.com/janesma/apitrace",self.source_root,VERSION)

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
        "LIBS": ["frameretrace"]
    }

  def provide(self): ##########################################################

    if self.should_build:

      self.OK = self.build()
      if self.OK:
        self.manifest.touch()

    print(self.OK)

    return self.OK
