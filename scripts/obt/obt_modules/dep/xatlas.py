###############################################################################
# Orkid Build System
# Copyright 2010-2018, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################

VERSION = "f700c7790aaa030e794b52ba7791a05c085faf0c"

from obt import dep, host, path
from obt.command import Command as cmd

###############################################################################

class xatlas(dep.StdProvider):
  name = "xatlas"
  def __init__(self): ############################################
    super().__init__(xatlas.name)
    self.declareDep("premake")
    self._builder = self.createBuilder(dep.CustomBuilder)

    build_dir = self.source_root/"build"/"gmake2"
    build_bin_dir = build_dir/"bin"/"x86_64"/"Release"
    include_dir = self.source_root/"source"/"xatlas"
    shared_lib_name = "libxatlas.so"


    self._builder._incrbuildcommands = [
      cmd(["premake5","gmake2"]),
      cmd(["make","-j",host.NumCores],
          working_dir=build_dir)
    ]
    self._builder._installcommands += {
      cmd(["install",build_bin_dir/shared_lib_name,path.libs()/shared_lib_name]),
      cmd(["install",include_dir/"xatlas.h",path.includes()/"xatlas.h"]),
      cmd(["install",include_dir/"xatlas_c.h",path.includes()/"xatlas_c.h"])
    }
  ########################################################################
  def __str__(self): 
    return "xatlas (github-%s)" % VERSION
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=xatlas.name,
                             repospec="jpcy/xatlas",
                             revision=VERSION,
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"premake5.lua").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"xatlas.h").exists()
