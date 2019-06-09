###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION ="v3.14.5"

import os, tarfile
from ork import dep, host, path, git, cmake, make
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
from ork.cmake import context

deco = Deco()

###############################################################################

class cmake314(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(cmake314,self)
    parclass.__init__(options=options)

    self.source_dest = path.builds()/"cmake"
    self.build_dest = path.builds()/"cmake"/".build"
    self.manifest = path.manifests()/"cmake"

    self.OK = self.manifest.exists()

  def __str__(self): ##########################################################

    return "CMAKE (latest)"

  def build(self): ##########################################################

    git.Clone("https://github.com/Kitware/CMake",self.source_dest,VERSION)

    os.system("rm -rf %s"%self.build_dest)
    os.mkdir(self.build_dest)
    os.chdir(self.build_dest)
    cmake_ctx = cmake.context("..")
    cmake_ctx.exec()
    return (make.exec("install")==0)

  def provide(self): ##########################################################

    if self.should_build():

      self.OK = self.build()
      if self.OK:
        self.manifest.touch()

    print(self.OK)

    return self.OK
