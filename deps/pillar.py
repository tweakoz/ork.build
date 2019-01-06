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

deco = Deco()
    
###########################################################

class pillar(dep.Provider):

  ################################

  def __init__(self,options=None):
    self.source_dest = path.builds()/"pillar-python-sdk"
    self.url = "https://github.com/armadillica/pillar"
    self.manifest = path.manifests()/"pillar-python-sdk"
    self.OK = self.manifest.exists()
    if "force" in options and options["force"]==True:
      self.OK = False
    pass

  ################################

  def __str__(self):
    return "pillar-python-sdk (%s)" % self.url

  ################################

  def provide(self):

    if False==self.OK:
      ork.git.Clone(self.url,self.source_dest,"master")
      buildir = self.source_dest/".build"
      pathtools.mkdir(buildir,clean=True)
      os.chdir(buildir)

      # patch pillar

      patcher = ork.patch.patcher("pillar")
      patcher.patch_list([[self.source_dest/"pillar","markdown.py"]])

      # install
      pip = "pip3"

      Command([pip,"install","raven"]).exec()
      Command([pip,"install","bleach"]).exec()
      Command([pip,"install","CommonMark"]).exec()
      Command([pip,"install","Flask-Babel"]).exec()
      Command([pip,"install","-e",".."]).exec()
      Command([pip,"install","-U","-r","../requirements.txt"]).exec()
      self.manifest.touch()

    return True
    





