###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION ="master"

import os, tarfile
from ork import dep, host, path, git, make, cmake
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()

###############################################################################

class glfw(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(glfw,self)
    parclass.__init__(options=options)

    self.source_dest = path.builds()/"glfw"
    self.build_dest = path.builds()/"glfw"/".build"
    self.manifest = path.manifests()/"glfw"

    self.OK = self.manifest.exists()

  def __str__(self): ##########################################################

    return "GLFW (src-%s)" % VERSION

  def build(self): ############################################################

    git.Clone("https://github.com/glfw/glfw",self.source_dest,VERSION)

    os.system("rm -rf %s"%self.build_dest)
    os.mkdir(self.build_dest)
    os.chdir(self.build_dest)
    cmake_ctx = cmake.context("..",env={
        "BUILD_SHARED_LIBS": "ON"
    })
    cmake_ctx.exec()
    return (make.exec("install")==0)

  def provide(self): ##########################################################

    if self.should_build():

      self.OK = self.build()
      if self.OK:
        self.manifest.touch()

    return self.OK
