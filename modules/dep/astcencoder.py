###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION ="1.7"

import os, shutil, tarfile
from obt import dep, host, path, git, cmake, make
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command
from obt.cmake import context

deco = Deco()

###############################################################################

class astcencoder(dep.Provider):

  def __init__(self,miscoptions=None): ############################################

    super().__init__("astcencoder")

    self.source_root = path.builds()/"astcencoder"
    self.build_dest = path.builds()/"astcencoder"/"Source"

  def __str__(self): ##########################################################

    return "ARM ASTC encoder (github-%s)" % VERSION

  def build(self): ##########################################################

    dep.require("openexr")

    if self.source_root.exists():
      shutil.rmtree(str(self.source_root), ignore_errors=True)
    git.Clone("https://github.com/ARM-software/astc-encoder",self.source_root,VERSION)
    cmd = Command(["make","-j",host.NumCores], working_dir=self.build_dest)
    err = cmd.exec()
    if err == 0:
      cmd = Command(["ls","-l"], working_dir=self.build_dest)
      err = cmd.exec()
      if err == 0:
        cmd = Command(["cp","astcenc",path.prefix()/"bin"],
                      working_dir=self.build_dest)
        err = cmd.exec()
        self.manifest.touch()
    return (err==0)
