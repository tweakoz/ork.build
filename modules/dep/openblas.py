###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, command, pathtools, path
###############################################################################
class openblas(dep.StdProvider):
  VERSION ="v0.3.23"
  NAME = "openblas"
  def __init__(self):
    super().__init__(openblas.NAME)
    self.declareDep("cmake")    
    self._builder = dep.CMakeBuilder(openblas.NAME)
    self._builder.setCmVars({
        "CMAKE_BUILD_TYPE": "RELEASE",
        "BUILD_EXAMPLES": "ON"
    })
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=openblas.NAME,
                             repospec="xianyi/OpenBLAS",
                             revision=openblas.VERSION,
                             recursive=False)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"openblas"/"lapacke.h").exists()

