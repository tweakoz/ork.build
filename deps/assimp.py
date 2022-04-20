###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, command, pathtools, path
###############################################################################
class assimp(dep.StdProvider):
  def __init__(self):
    VERSION ="obt-v5.0.1"
    NAME = "assimp"
    super().__init__(NAME)
    self.declareDep("cmake")
    self._fetcher = dep.GithubFetcher(name=NAME,
                                      repospec="tweakoz/assimp",
                                      revision=VERSION,
                                      recursive=False)
    
    self._builder = dep.CMakeBuilder(NAME)
  ########
  def on_build_shell(self):
    pathtools.mkdir(self.build_dest,clean=False)
    return command.subshell( directory=self.build_dest,
                             prompt = "ASSIMP",
                             environment = dict() )
  ########
  def linkenv(self): ##########################################################
    return {
        "LIBS": ["assimp"]
    }
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libassimp.so").exists()
