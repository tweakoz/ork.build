###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION ="1.7"

import os, tarfile
from ork import dep, host, path, git, cmake, make
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
from ork.cmake import context

deco = Deco()

###############################################################################

class astcencoder(dep.Provider):

  def __init__(self,miscoptions=None): ############################################

    super().__init__("astcencoder")

    self.OK = self.manifest.exists()

  def __str__(self): ##########################################################

    return "ARM ASTC encoder (github-%s)" % VERSION

  def build(self): ##########################################################

    dep.require("openexr")

    os.system("rm -rf %s"%self.source_root)
    git.Clone("https://github.com/ARM-software/astc-encoder",self.source_root,VERSION)
    os.chdir(self.build_dest)
    cmd = Command(["make","-j",host.NumCores])
    err = cmd.exec()
    if err == 0:
      cmd = Command(["ls","-l"])
      err = cmd.exec()
      if err == 0:
        cmd = Command(["cp","astcenc",path.prefix()/"bin"])
        err = cmd.exec()
        self.manifest.touch()
    return (err==0)
