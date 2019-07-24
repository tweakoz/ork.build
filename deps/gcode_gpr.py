###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from ork import dep, host, path, git, cmake, make
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()

###############################################################################

class gcode_gpr(dep.Provider):

  def __init__(self,options=None): ############################################


    parclass = super(gcode_gpr,self)
    parclass.__init__(options=options)
    self.manifest = path.manifests()/"gcode_gpr"
    self.source_dest = path.builds()/"gcode_gpr"
    self.build_dest = self.source_dest/".build"

    self.OK = self.manifest.exists()

  def __str__(self):
    return "A simple C++ G-code parser"

  def clone(self):
    #git.Clone("https://github.com/tweakoz/gpr",self.source_dest,"master")

    os.system("rm -rf %s"%self.build_dest)
    os.mkdir(self.build_dest)
    os.chdir(self.build_dest)
    cmake_ctx = cmake.context("..")
    cmake_ctx.exec()
    self.OK = (make.exec("install")==0)

  def provide(self): ##########################################################

      self.clone()
      self.manifest.touch()
      return self.OK
