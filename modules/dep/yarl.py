###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from obt import dep, host, path, cmake
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command
import obt.pip

deco = Deco()

###############################################################################

class yarl(dep.Provider):

  def __init__(self): ############################################
    super().__init__("yarl")
    self.manifest = path.manifests()/"yarl"
    self.OK = self.manifest.exists()

  ########

  def __str__(self):
    return "YARL (pip3)"

  ########

  def provide(self): ##########################################################
    if False==self.OK:
      self.OK = 0==obt.pip.install("yarl")
      if self.OK:
        self.manifest.touch()

    return self.OK
