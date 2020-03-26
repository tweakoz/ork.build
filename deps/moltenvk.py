###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "v1.0.40"

import os, tarfile
from ork import dep, host, path, cmake, git, make, command
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()

###############################################################################

class moltenvk(dep.Provider):

  def __init__(self): ############################################
    super().__init__()
    #print(options)
    self.source_root = path.builds()/"moltenvk"
    self.build_dest = path.builds()/"moltenvk"/".build"
    self.manifest = path.manifests()/"moltenvk"
    self.OK = self.manifest.exists()

  def __str__(self): ##########################################################

    return "MoltenVK (github-%s)" % VERSION

  def wipe(self): #############################################################
    os.system("rm -rf %s"%self.source_root)
    os.system("rm -rf %s"%self.build_dest)

  def build(self): ##########################################################

    #glfw = dep.require("glfw")

    if not self.source_root.exists():
      git.Clone("https://github.com/KhronosGroup/MoltenVK",self.source_root,VERSION)

    os.chdir(self.source_root)

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
