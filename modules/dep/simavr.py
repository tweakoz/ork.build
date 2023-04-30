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

class simavr(dep.Provider):

  def __init__(self): ############################################
    super().__init__("simavr")
    self.source_root = path.builds()/"simavr"
    self._archlist = ["x86_64"]

  def provide(self): ##########################################################

    git.Clone("https://github.com/tweakoz/simavr",self.source_root,"master")
    os.chdir(self.source_root)
    os.environ["INSTALL_PREFIX"] = str(path.prefix())
    make.exec("install")
    self.manifest.touch()
    self.OK = self.manifest.exists()
    return self.OK
