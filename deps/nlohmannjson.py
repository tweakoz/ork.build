###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, command, pathtools, path
###############################################################################
class nlohmannjson(dep.StdProvider):
  def __init__(self):
    VERSION ="v3.6.1"
    NAME = "nlohmannjson"
    super().__init__(NAME)
    self.declareDep("cmake")
    self._fetcher = dep.GithubFetcher(name=NAME,
                                      repospec="nlohmann/json",
                                      revision=VERSION,
                                      recursive=False)
    
    self._builder = dep.CMakeBuilder(NAME)
    self._builder.setCmVars({
        "CMAKE_BUILD_TYPE": "RELEASE",
        "BUILD_EXAMPLES": "ON"
    })
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.include()/"nlohmann"/"json.hpp").exists()

