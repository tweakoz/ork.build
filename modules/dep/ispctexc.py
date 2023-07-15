###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

from obt import dep, host, path, pathtools
from obt.command import Command
###############################################################################

class ispctexc(dep.StdProvider):
  name = "ispctexc"
  def __init__(self):
    super().__init__(ispctexc.name)
    self.declareDep("ispc")
    self.build_dest = self.source_root/"build"
    self._archlist = ["x86_64"]

  ########################################################################
  @property
  def _fetcher(self):
    fetcher = dep.GithubFetcher(name=ispctexc.name,
                                repospec="tweakoz/ISPCTextureCompressor",
                                revision="master",
                                recursive=False)
    fetcher._cache=False
    return fetcher

  ########################################################################

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
    r = Command(["make","-f","Makefile.linux"]).exec()
    self.OK = (r==0)

    return self.OK

  def install(self):
    if self.OK:
      sonam = "libispc_texcomp.so"
      hdrnam = "ispc_texcomp.h"
      if host.IsOsx:
        cmd = ["install_name_tool",
               "-id","@rpath/libispc_texcomp.so",
               self.build_dest/sonam]
        Command(cmd).exec()
      pathtools.copyfile(self.build_dest/sonam,path.stage()/"lib"/sonam)
      pathtools.copyfile(self.source_root/"ispc_texcomp"/hdrnam,path.stage()/"include"/hdrnam)
    return self.OK

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"Makefile.linux").exists()

  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libispc_texcomp.so").exists()

 
