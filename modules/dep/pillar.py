###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

import os, tarfile
from obt import dep, host, path, pathtools
from obt.deco import Deco
from obt.wget import wget
import obt.git
from obt.command import Command
import obt.patch
import obt.pip

deco = Deco()

###########################################################

class pillar(dep.Provider):

  ################################

  def __init__(self):
    super().__init__("pillar")
    self.source_root = path.builds()/"pillar-python-sdk"
    self.url = "https://github.com/armadillica/pillar"
    self.manifest = path.manifests()/"pillar-python-sdk"
    self.OK = self.manifest.exists()
    if self.option("force")==True:
      self.OK = False

  ################################

  def __str__(self):
    return "pillar-python-sdk (%s)" % self.url

  ################################

  def provide(self):

    if False==self.OK:
      obt.git.Clone(self.url,self.source_root,"master")
      os.chdir(self.source_root)

      # install deps
      obt.pip.install([ "raven",
                        "celery",
                        "bleach",
                        "CommonMark",
                        "Flask-Babel"])

      # patch pillar

      patcher = obt.patch.patcher("pillar")
      patcher.patch_list([[self.source_root/"pillar","markdown.py"]])

      # install

      Command(["python3","setup.py", "install"]).exec()

      self.manifest.touch()

    return True
