###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from obt import dep, host, path, pathtools, git, cmake, make, command
from obt.deco import Deco
from obt.wget import wget

deco = Deco()

VERSION = "2.20.2"
###############################################################################

class faust(dep.Provider):

  def __init__(self): ############################################
    super().__init__("faust")
    self.source_root = path.builds()/"faust"
    self.build_dest = self.source_root/".build"
    self._archlist = ["x86_64"]

  ########

  def __str__(self):
    return "faust (github-%s)" % VERSION

  ########

  def build(self): #############################################################

    OK = False
    if self.should_force_build:
        os.system("rm -rf %s"%self.source_root)

    git.Clone("https://github.com/grame-cncm/faust",
              self.source_root,
              VERSION,
              recursive=True)

    pathtools.chdir(self.source_root)

    makeenv = {
        "PREFIX": path.stage()
    }

    if command.Command(['make',"-e"],environment=makeenv).exec()==0:
        if command.Command(['make',"-e","install"],environment=makeenv).exec()==0:
          OK = True
          self.manifest.touch()

    return OK

  ########

  def provide(self): ##########################################################
    super()._old_provide()
