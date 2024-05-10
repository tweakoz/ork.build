###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from obt import dep, host, path
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command

deco = Deco()

###############################################################################

class irrlicht(dep.Provider):

  def __init__(self): ############################################
    super().__init__("irrlicht")

  ########

  def __str__(self):
    return "irrlicht (homebrew)"

  ########

  def provide(self): ##########################################################
    OK = self.manifest.exists()
    if False==self.OK:
      if host.IsOsx:
        OK = 0==Command(["brew","install","irrlicht"]).exec()
      if OK:
        self.manifest.touch()

    return OK
