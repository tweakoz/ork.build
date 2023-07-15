###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from yarl import URL
from obt import dep, host, path
from obt.deco import Deco
from obt.wget import wget
from obt.command import Command
from obt.cmake import context

deco = Deco()

###############################################################################

class gitpython(dep.Provider):

  def __init__(self): ############################################
    super().__init__("gitpython")
    self.manifest = path.manifests()/"gitpython"
    self.OK = self.manifest.exists()

  ########

  def __str__(self):
    return "gitpython (pip3)"

  ########

  def provide(self): ##########################################################
    if False==self.OK:
      self.OK = 0==Command(["pip3","install","gitpython"]).exec()
    if self.OK:
      self.manifest.touch()

    return self.OK
