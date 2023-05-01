###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from ork import dep, host, path, pathtools
from ork.deco import Deco
from ork.wget import wget
import ork.git
from ork.command import Command
import ork.patch
import ork.pip

deco = Deco()

###########################################################

class pillar(dep.Provider):

  ################################

  def __init__(self):
    super().__init__("pillar")
    self.url = "https://github.com/armadillica/pillar"
    self.OK = self.manifest.exists()
    if self.option("force")==True:
      self.OK = False

  ################################

  def __str__(self):
    return "pillar-python-sdk (%s)" % self.url

  ################################

  def provide(self):

    if False==self.OK:
      ork.git.Clone(self.url,self.source_root,"master")
      os.chdir(self.source_root)

      # install deps
      ork.pip.install([ "raven",
                        "celery",
                        "bleach",
                        "CommonMark",
                        "Flask-Babel"])

      # patch pillar

      patcher = ork.patch.patcher("pillar")
      patcher.patch_list([[self.source_root/"pillar","markdown.py"]])

      # install

      Command(["python3","setup.py", "install"]).exec()

      self.manifest.touch()

    return True
