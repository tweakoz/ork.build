###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from obt import dep, command, pathtools, path
###############################################################################
class nlohmannjson(dep.StdProvider):
  VERSION ="v3.6.1"
  NAME = "nlohmannjson"
  def __init__(self):
    super().__init__(nlohmannjson.NAME)
    self.declareDep("cmake")    
    self._builder = dep.CMakeBuilder(nlohmannjson.NAME)
    self._builder.setCmVars({
        "CMAKE_BUILD_TYPE": "RELEASE",
        "BUILD_EXAMPLES": "ON"
    })
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=nlohmannjson.NAME,
                             repospec="nlohmann/json",
                             revision=nlohmannjson.VERSION,
                             recursive=True)
  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.include()/"nlohmann"/"json.hpp").exists()

