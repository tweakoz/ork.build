###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from ork import dep, host, path, cmake
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()
    
###############################################################################

class yarl(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(yarl,self)
    parclass.__init__(options=options)
    Command(["pip3","install","yarl"]).exec()
    self.manifest = path.manifests()/"yarl"
    self.manifest.touch()

  def provide(self): ##########################################################
      return True

