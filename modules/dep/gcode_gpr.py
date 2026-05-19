###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, shutil, tarfile
from obt import dep, host, path, git, cmake, make
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()

###############################################################################

class gcode_gpr(dep.Provider):

  def __init__(self): ############################################
    super().__init__("gcode_gpr")
    self.source_root = path.builds()/"gcode_gpr"
    self.build_dest = self.source_root/".build"

  def __str__(self):
    return "A simple C++ G-code parser"

  def clone(self):
    #git.Clone("https://github.com/tweakoz/gpr",self.source_root,"master")

    if self.build_dest.exists():
      shutil.rmtree(str(self.build_dest), ignore_errors=True)
    os.mkdir(self.build_dest)
    cmake_ctx = cmake.context(sourcedir=self.source_root,
                              builddir=self.build_dest,
                              working_dir=self.build_dest)
    cmake_ctx.exec()
    self.OK = (make.exec("install", working_dir=self.build_dest)==0)

  def provide(self): ##########################################################

      self.clone()
      self.manifest.touch()
      return self.OK
