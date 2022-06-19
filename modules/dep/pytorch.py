
###############################################################################
# Orkid Build System
# Copyright 2010-2022, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from ork import dep, host, path, cmake, env, pip
from ork.deco import Deco
from ork.wget import wget
from ork.command import Command
from ork import log, macos

deco = Deco()


###############################################################################

class pytorch(dep.Provider):

  def __init__(self,target=None): ############################################
    super().__init__("pytorch")
    self.python = dep.instance("python")

  def build(self): ############################################################
      ret = -1
      if host.IsLinux:
        ret = Command([self.python.executable,"-m","pip","install","torch",
                      "torchvision","torchaudio","torchdata","--extra-index-url","https://download.pytorch.org/whl/cu113"]).exec()
      elif host.IsOsx:        
        ret = pip.install(["torch","torchvision","torchaudio","torchdata"])

      return (ret==0)

  def areRequiredSourceFilesPresent(self):
    return (self.python.site_packages_dir/"torch"/"torch_version.py").exists()

  def areRequiredBinaryFilesPresent(self):
    return self.areRequiredSourceFilesPresent()
    