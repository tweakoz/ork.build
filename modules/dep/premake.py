###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "v5.0.0-beta2"

from obt import dep, host, path
from obt.command import Command as cmd

###############################################################################

class premake(dep.StdProvider):
  name = "premake"
  def __init__(self): ############################################
    super().__init__(premake.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CustomBuilder)
    PLATFORM = "linux"
    if host.IsDarwin:
      PLATFORM = "osx"
    self._builder._incrbuildcommands = [
      cmd(["make","-f","Bootstrap.mak",PLATFORM])
    ]
    self._builder._installcommands += {
      cmd(["install","bin/release/premake5",path.bin()/"premake5"])
    }
  ########################################################################
  def __str__(self): 
    return "premake (github-%s)" % VERSION
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=premake.name,
                             repospec="premake/premake-core",
                             revision=VERSION,
                             recursive=False)
  ########################################################################
  #def linkenv(self):
  #  LIBS = ["premake"]
  #  return {
  #      "LIBS": LIBS,
  #      "LFLAGS": ["-l%s"%item for item in LIBS]
  #  }
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"doxyfile").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"premake.h").exists()
