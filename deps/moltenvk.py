###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "master"

import os, tarfile
from ork import dep, host, path, cmake, git, make, command
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()

###############################################################################

class moltenvk(dep.Provider):

  def __init__(self,miscoptions=None): ############################################

    parclass = super(moltenvk,self)
    parclass.__init__(miscoptions=miscoptions)
    #print(options)
    self.source_dest = path.builds()/"moltenvk"
    self.build_dest = path.builds()/"moltenvk"/".build"
    self.manifest = path.manifests()/"moltenvk"
    self.OK = self.manifest.exists()

  def __str__(self): ##########################################################

    return "MoltenVK (github-%s)" % VERSION

  def build(self): ##########################################################

    #glfw = dep.require("glfw")

    if self.incremental():
        os.chdir(self.build_dest)
    else:
        git.Clone("https://github.com/KhronosGroup/MoltenVK",self.source_dest,VERSION)


    os.chdir(self.source_dest)

    command.system(["./fetchDependencies"])
    cmd = ["make", "macos"]
    ok = (0 == command.system(cmd))
    if ok:
      cmd = ["cp","Package/Latest/MoltenVK/macOS/static/libMoltenVK.a",path.libs()/"libMoltenVK.a"]
      ok = (0 == command.system(cmd))
      if ok:
        cmd = ["cp","-r","Package/Latest/MoltenVK/include/*",path.includes()]
        ok = (0 == command.system(cmd))
    return ok
