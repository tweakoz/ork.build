###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from ork import dep, host, path, pathtools, git, cmake, make, command
from ork.deco import Deco
from ork.wget import wget

deco = Deco()

VERSION = "release-1.3.5"
###############################################################################

class fltk(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(fltk,self)
    parclass.__init__(options=options)
    self.manifest = path.manifests()/"fltk"
    self.OK = self.manifest.exists()
    self.source_dest = path.builds()/"fltk"
    self.build_dest = self.source_dest/".build"

  ########

  def __str__(self):
    return "FLTK (github-%s)" % VERSION

  ########

  def build(self): #############################################################

    self.OK = False

    os.system("rm -rf %s"%self.source_dest)

    git.Clone("https://github.com/fltk/fltk",
              self.source_dest,
              VERSION)

    pathtools.mkdir(self.build_dest,clean=True)
    pathtools.chdir(self.build_dest)

    cmakeEnv = {
        "CMAKE_BUILD_TYPE": "RELEASE",
        "OPTION_BUILD_SHARED_LIBS": "ON",
    }

    cmake_ctx = cmake.context(root="..",env=cmakeEnv)
    if cmake_ctx.exec()==0:
        if make.exec("install")==0:
            err = command.system(["rm",path.stage()/"lib"/"libfltk*.a"])
            if err==0:
              self.manifest.touch()
              self.OK = True

    return self.OK

  ########

  def provide(self): ##########################################################

    if self.should_build():
      self.OK = self.build()
    print(self.OK)
    return self.OK
