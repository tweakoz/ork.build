###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from ork import dep, host, path
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command

deco = Deco()
    
###############################################################################

class unittestpp(dep.Provider):

  def __init__(self,options=None): ############################################

    parclass = super(unittestpp,self)
    parclass.__init__(options=options)
    self.manifest = path.manifests()/"unittestpp"
    self.OK = self.manifest.exists()

  ########

  def __str__(self):
    return "UnitTestPP (homebrew)"

  ########

  def provide(self): ##########################################################
    if False==self.OK:
      if host.IsOsx:
        self.OK = 0==Command(["brew","install","unittest-cpp"]).exec()
      if self.OK:
        self.manifest.touch()

    return self.OK

