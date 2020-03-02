###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from ork import dep, host, path, pathtools
from ork.command import Command
###############################################################################

class ispctexc(dep.StdProvider):
  def __init__(self,miscoptions=None):
    name = "ispctexc"
    parclass = super(ispctexc,self)
    parclass.__init__(name=name,miscoptions=miscoptions)
    self._fetcher = dep.GitFetcher(name)
    self._fetcher._git_url = "https://github.com/GameTechDev/ISPCTextureCompressor"
    self._fetcher._cache=False,
    self._fetcher._recursive=False
    self._fetcher._revision = "master"
    self.build_dest = self.source_root/"build"

  def build(self):

    dep.require("ispc")

    #########################################
    # fetch source
    #########################################

    if not self.source_root.exists():
      self._fetcher.fetch(self.source_root)

    #########################################
    # build
    #########################################

    self.source_root.chdir()

    ENV = {
        "ISPC": path.stage()/"bin"/"ispc"
    }
    r = Command(["make","-f","Makefile.linux"],environment=ENV).exec()
    self.OK = (r==0)

    return self.OK

  def install(self):
    if self.OK:
      sonam = "libispc_texcomp.so"
      hdrnam = "ispc_texcomp.h"
      pathtools.copyfile(self.build_dest/sonam,path.stage()/"lib"/sonam)
      pathtools.copyfile(self.source_root/"ispc_texcomp"/hdrnam,path.stage()/"include"/hdrnam)
    return self.OK
