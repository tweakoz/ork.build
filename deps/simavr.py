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

  def __init__(self,options=None): ############################################


    parclass = super(simavr,self)
    parclass.__init__(options=options)
    self.manifest = path.manifests()/"simavr"
    self.source_dest = path.builds()/"simavr"
    self.build_dest = self.source_dest/".build"

    self.clone()
    self.manifest.touch()

    self.OK = self.manifest.exists()

  def clone(self): 
    git.Clone("https://github.com/tweakoz/simavr",self.source_dest,"master")

    os.chdir(self.source_dest)

    make.exec("install")

  def provide(self): ##########################################################

      return self.OK

