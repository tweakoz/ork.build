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

###############################################################################

class nlohmannjson(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(nlohmannjson,self)
    parclass.__init__(options=options)
    self.manifest = path.manifests()/"nlohmannjson"
    self.OK = self.manifest.exists()
    self.json_source_dest = path.builds()/"nlohmannjson"
    self.json_build_dest = self.json_source_dest/".build"

  ########

  def __str__(self):
    return "NLohmannJson (github)"

  ########

  def provide(self): ##########################################################
    if False==self.OK:

        os.system("rm -rf %s"%self.json_source_dest)

        git.Clone("https://github.com/nlohmann/json",
                  self.json_source_dest,
                  "v3.6.1")

        pathtools.mkdir(self.json_build_dest,clean=True)
        pathtools.chdir(self.json_build_dest)

        cmakeEnv = {
            "CMAKE_BUILD_TYPE": "RELEASE",
            "BUILD_EXAMPLES": "ON"
        }

        cmake_ctx = cmake.context(root="..",env=cmakeEnv)
        if cmake_ctx.exec()==0:
            if make.exec("install")==0:
                self.manifest.touch()
                self.OK = True

    return self.OK