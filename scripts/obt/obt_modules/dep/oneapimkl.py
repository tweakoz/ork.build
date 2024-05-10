###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, command, pathtools, path
###############################################################################
class oneapimkl(dep.StdProvider):
  VERSION ="v0.2"
  NAME = "oneapimkl"
  def __init__(self):
    super().__init__(oneapimkl.NAME)
    self.declareDep("cmake")
    self._builder = dep.CMakeBuilder(oneapimkl.NAME)
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=oneapimkl.NAME,
                             repospec="oneapi-src/oneMKL",
                             revision=oneapimkl.VERSION,
                             recursive=False)

  #######################################################################
  def on_build_shell(self):
    pathtools.mkdir(self.build_dest,clean=False)
    return command.subshell( directory=self.build_dest,
                             prompt = "ASSIMP",
                             environment = dict() )
  ########
  def linkenv(self): ##########################################################
    return {
        "LIBS": ["oneapimkl"]
    }
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.libs()/"libassimp.so").exists()

