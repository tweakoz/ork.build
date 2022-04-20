###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, path
###############################################################################
class glm(dep.StdProvider):
  def __init__(self):
    name = "glm"
    super().__init__(name)
    self.declareDep("cmake")
    self._fetcher = dep.GithubFetcher(name=name,
                                      repospec="tweakoz/glm",
                                      revision="master",
                                      recursive=False)
    self._builder = self.createBuilder(dep.CMakeBuilder)
    #self._builder.requires(["lapack"])

  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()

  def areRequiredBinaryFilesPresent(self):
    return None

  def compileenv(self): ##########################################################
    return {
        "INCLUDE_PATH": path.includes()/"glm"/"glm.hpp"
    }
