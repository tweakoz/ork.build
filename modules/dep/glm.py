###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, path, host
###############################################################################
class glm(dep.StdProvider):
  name = "glm"
  def __init__(self):
    super().__init__(glm.name)
    self.declareDep("cmake")
    self._builder = self.createBuilder(dep.CMakeBuilder)

    if host.IsDarwin:
      self._builder.setCmVars({
        "CMAKE_CXX_FLAGS": "-Wno-deprecated-declarations -Wno-poison-system-directories",
        "CMAKE_CXX_STANDARD": "17" 
      })
    #self._builder.requires(["lapack"])

  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=glm.name,
                             repospec="tweakoz/glm",
                             revision="toz-oct16",
                             recursive=False)

  #######################################################################

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return None

  def compileenv(self): ##########################################################
    return {
        "INCLUDE_PATH": path.includes()/"glm"/"glm.hpp"
    }
