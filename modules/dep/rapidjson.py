###############################################################################
# Orkid Build System
# Copyright 2010-2020, Michael T. Mayers
# email: michael@tweakoz.com
# The Orkid Build System is published under the GPL 2.0 license
# see http://www.gnu.org/licenses/gpl-2.0.html
###############################################################################
from ork import dep, command, pathtools, path
###############################################################################
class rapidjson(dep.StdProvider):
  VERSION ="master"
  NAME = "rapidjson"
  def __init__(self):
    super().__init__(rapidjson.NAME)
    self.declareDep("cmake")
    self._builder = dep.CMakeBuilder(rapidjson.NAME)
    self._builder.setCmVars({
        "CMAKE_BUILD_TYPE": "RELEASE",
        "BUILD_EXAMPLES": "ON"
    })
  ########################################################################
  @property
  def _fetcher(self):
    return dep.GithubFetcher(name=rapidjson.NAME,
                             repospec="tweakoz/rapidjson",
                             revision=rapidjson.VERSION,
                             recursive=False)

  ########################################################################
  def areRequiredSourceFilesPresent(self):
    return (self.source_root/"CMakeLists.txt").exists()
  def areRequiredBinaryFilesPresent(self):
    return (path.includes()/"rapidjson"/"rapidjson.h").exists()
